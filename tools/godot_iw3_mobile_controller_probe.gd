extends SceneTree

# Integration testing against real, locally extracted IW3 skinned GLB scenes.
# This is a deterministic 60 fps touch-control state-machine check without
# submitting copyrighted GLB models/textures/screenshots to public artifacts.
const Controller = preload("res://fps_controller.gd")
const GUNS: Array[String] = ["m4", "ak47", "mp5"]
const FRAME: float = 1.0 / 60.0
const WIDTH: float = 640.0
const HEIGHT: float = 360.0

func _bone_world(skeleton: Skeleton3D, name: String) -> Vector3:
    var index: int = skeleton.find_bone(name)
    return (skeleton.global_transform * skeleton.get_bone_global_pose(index)).origin

func _center_error(camera: Camera3D, rig: Node, center: Vector2) -> Dictionary:
    var marker: Dictionary = rig.aim_tag_info()
    var tag: String = marker.get("name", "")
    if tag.is_empty():
        return {"valid": false, "reason": "no iron sight or optic mount tag"}
    var point: Vector3 = _bone_world(rig.weapon_skeleton, tag)
    if camera.is_position_behind(point):
        return {"valid": false, "reason": "sight behind camera"}
    var projected: Vector2 = camera.unproject_position(point)
    var norm: Vector2 = (projected - center) / Vector2(WIDTH, HEIGHT)
    return {"valid": true, "tag": tag, "x": snappedf(norm.x, 0.00001),
        "y": snappedf(norm.y, 0.00001), "magnitude": snappedf(norm.length(), 0.00001),
        "marker_source": marker.get("source", "unknown")}

func _steps(controller: Node, count: int) -> Dictionary:
    var last: Dictionary = {}
    for i in range(count):
        last = controller.tick(FRAME)
        if not last.get("ok", false):
            return last
    return last

func _run() -> void:
    var report: Dictionary = {"engine": Engine.get_version_info().get("string", ""),
        "guns": {}, "full_mobile_controller_gate": true,
        "independent_live_android_device_test": false,
        "real_iron_sight_art_approved": false,
        "copyrighted_assets_uploaded": false}
    var world: Node3D = Node3D.new()
    root.add_child(world)
    var camera: Camera3D = Camera3D.new()
    camera.near = 0.01
    camera.far = 75.0
    camera.fov = 80.0
    world.add_child(camera)
    camera.current = true
    await process_frame
    for gun in GUNS:
        var hands: Resource = load("res://weapons/" + gun + "_hands_animated_experimental.glb")
        var weapon: Resource = load("res://weapons/" + gun + "_animated_experimental.glb")
        if not (hands is PackedScene) or not (weapon is PackedScene):
            report["guns"][gun] = {"error": "missing original model"}
            report["full_mobile_controller_gate"] = false
            continue
        var controller = Controller.new()
        controller.name = gun + "_controller"
        controller.scale = Vector3.ONE * 0.0254
        world.add_child(controller)
        controller.set_process(false) # test deterministic tick(), not wall clock
        if not controller.configure(camera, hands as PackedScene, weapon as PackedScene):
            report["guns"][gun] = {"error": "cannot configure controller"}
            report["full_mobile_controller_gate"] = false
            controller.queue_free()
            continue
        await process_frame
        controller.mount.set_timed_action("idle", 0.0)
        var eye: Vector3 = _bone_world(controller.mount.hands_skeleton, "tag_camera")
        camera.global_position = eye
        camera.look_at(eye + Vector3.RIGHT, Vector3.UP)
        var pivot: Vector3 = controller.mount.global_position
        var center: Vector2 = Vector2(WIDTH / 2.0, HEIGHT / 2.0)
        var record: Dictionary = {"hip": _center_error(camera, controller.mount, center)}
        var ok: bool = controller.toggle_ads()
        record["toggle_ads_supported"] = ok
        record["ads_one_second"] = _steps(controller, 60)
        record["ads_final"] = _center_error(camera, controller.mount, center)
        record["ads_attachment"] = controller.mount.anchor_error()
        # ADS should center only its target tag numerically. Original sight
        # image alignment and camera/viewmodel near-clipping are not approved.
        var centered: bool = record["ads_final"].get("valid", false)
        if centered:
            centered = record["ads_final"]["magnitude"] < 0.01
        if not centered:
            ok = false
        if float(record["ads_attachment"]["anchor_position_error"]) > 0.001:
            ok = false
        var stable_start: Vector3 = controller.mount.global_position
        record["ads_hold"] = _steps(controller, 90)
        record["ads_drift_m"] = snappedf(stable_start.distance_to(controller.mount.global_position), 0.00001)
        if float(record["ads_drift_m"]) > 0.0001:
            ok = false

        record["trigger_fire"] = controller.press_fire()
        record["fire_first_frame"] = controller.tick(FRAME)
        record["fire_end"] = _steps(controller, 50)
        record["after_fire"] = controller.status()
        if not record["trigger_fire"] or record["after_fire"]["fire_count"] != 1:
            ok = false
        record["start_reload"] = controller.start_reload()
        record["reload_start"] = controller.tick(FRAME)
        record["reload_mid"] = _steps(controller, 24)
        record["reload_mount_position"] = controller.mount.global_position.distance_to(pivot)
        # Fire during reload must cancel reload, never leave us locked out.
        record["cancel_to_fire"] = controller.press_fire()
        record["cancel_state"] = controller.status()
        if not record["cancel_to_fire"] or record["cancel_state"]["cancelled_reload_to_fire"] != 1:
            ok = false
        _steps(controller, 50)
        controller.reset_viewmodel()
        record["reset"] = controller.tick(FRAME)
        record["reset_sight"] = _center_error(camera, controller.mount, center)
        record["hip_pivot_position_delta_m"] = snappedf(
            pivot.distance_to(controller.mount.global_position), 0.00001)
        if float(record["hip_pivot_position_delta_m"]) > 0.0001:
            ok = false
        # Switch input semantics to ADS HOLD without any weapon rebuild.
        controller.ads_hold_mode = true
        record["toggle_rejected_in_hold_mode"] = not controller.toggle_ads()
        record["hold_enable"] = controller.set_ads_held(true)
        record["hold_on"] = _steps(controller, 20)
        record["hold_disable"] = controller.set_ads_held(false)
        record["hold_off"] = _steps(controller, 20)
        record["final"] = controller.status()
        record["checks_passed"] = ok and record["hold_enable"] and record["hold_disable"] and             float(record["final"]["ads_blend"]) < 0.001 and record["final"]["failed_alignment_frames"] == 0
        if not record["checks_passed"]:
            report["full_mobile_controller_gate"] = false
        report["guns"][gun] = record
        controller.queue_free()
        await process_frame
    var file: FileAccess = FileAccess.open("res://godot-mobile-controller-gate.json", FileAccess.WRITE)
    if file == null:
        printerr("Failed to store controller metrics")
        quit(2)
        return
    file.store_string(JSON.stringify(report))
    file.close()
    var short: Dictionary = {}
    for gun in report["guns"]:
        var r: Dictionary = report["guns"][gun]
        short[gun] = {"pass": r.get("checks_passed", false),
            "ads_sight_norm_error": r.get("ads_final", {}).get("magnitude", -1),
            "ads_drift_m": r.get("ads_drift_m", -1),
            "hip_return_delta_m": r.get("hip_pivot_position_delta_m", -1),
            "reload_cancelled_by_fire": r.get("cancel_state", {}).get("cancelled_reload_to_fire", -1),
            "hold_released": r.get("final", {}).get("ads_blend", -1)}
    print("IW3_MOBILE_FPS_CONTROLLER_GATE: " + JSON.stringify({
        "pass": report["full_mobile_controller_gate"], "guns": short,
        "camera_procedural_ads_visually_approved": false}))
    quit(0 if report["full_mobile_controller_gate"] else 1)

func _initialize() -> void:
    call_deferred("_run")
