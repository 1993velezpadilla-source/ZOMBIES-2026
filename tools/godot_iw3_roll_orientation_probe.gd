extends SceneTree

# Regression from Pixel Fold 2026-11-02 screenshots: M4/AK47/MP5 top side
# points 9 o'clock instead of 12. The camera had a correct forward direction
# but the viewmodel was rolled 90 degrees.
#
# Run with the ORIGINAL user-supplied converted GLBs in a private CI sandbox.
# Report ONLY orientation vectors & Boolean results, never private models.
const Stage = preload("res://playground.tscn")

const GUNS: Array[String] = ["m4", "ak47", "mp5"]
const EPS: float = 0.00015
const DEFAULT_ROLL: float = -90.0

func _basis_without_scale(node: Node3D) -> Basis:
    return node.global_transform.basis.orthonormalized()

func _check(game: Node, action: String) -> Dictionary:
    var rig: Node3D = game.controller.mount
    rig.set_timed_action(action, 0.0 if action=="idle" else (
        rig.hands_player.get_animation(action).length * 0.60))
    await process_frame
    rig.hands_skeleton.force_update_all_bone_transforms()
    rig.weapon_skeleton.force_update_all_bone_transforms()
    var cam_basis: Basis = _basis_without_scale(game.camera)
    var model_basis: Basis = _basis_without_scale(game.controller)
    # The X-forward source -> camera-front AND +Z source top -> camera-up.
    # The latter was exactly WRONG in the user screenshots.
    var source_forward: Vector3 = model_basis * Vector3.RIGHT
    var camera_forward: Vector3 = -cam_basis.z
    var source_top: Vector3 = model_basis * Vector3.BACK
    var camera_up: Vector3 = cam_basis.y
    var forward_dot: float = source_forward.dot(camera_forward)
    var up_dot: float = source_top.dot(camera_up)
    var right: Vector3 = model_basis * Vector3.UP
    var horizontal_dot: float = right.dot(cam_basis.x)
    var attachment: Dictionary = rig.anchor_error()
    return {
        "action": action,
        "model_forward_parallel_camera": snappedf(forward_dot, 0.000001),
        "model_top_parallel_screen_up": snappedf(up_dot, 0.000001),
        "model_horizontal_parallel_screen_right": snappedf(horizontal_dot, 0.000001),
        "gun_tag_weapon_attachment_error_m": attachment["anchor_position_error"],
        "gun_bone_attachment_ok": attachment["bone_valid"] and attachment["weapon_parent_is_attachment"],
        "pass": forward_dot > 1.0-EPS and up_dot > 1.0-EPS and
                absf(float(attachment["anchor_position_error"])) < EPS and
                attachment["weapon_parent_is_attachment"]
    }

func _run() -> void:
    var report: Dictionary = {"source": "Pixel Fold actual screenshots",
        "bug": "top face points to 9 o'clock for all 3 imported weapons",
        "expected_top": "12 o'clock", "roll_fix_degrees": DEFAULT_ROLL,
        "all_guns_pass": true, "guns": {},
        "visual_screenshots_approved": false,
        "ready_for_android_playtest": false}
    var stage: Node = Stage.instantiate()
    root.add_child(stage)
    await process_frame
    await physics_frame
    await process_frame
    stage.set_process(false)
    for gun in GUNS:
        var selected: int = GUNS.find(gun)
        var equipped: bool = stage.equip(selected)
        if not equipped:
            report["all_guns_pass"]=false
            report["guns"][gun]={"error":"could not equip"}
            continue
        await process_frame
        var poses: Array = []
        for action in ["idle","ads","fire","reload"]:
            var result: Dictionary = await _check(stage,action)
            poses.append(result)
            if not result["pass"]:
                report["all_guns_pass"]=false
        var cam_dir_before: Vector3 = -stage.camera.global_transform.basis.z.normalized()
        stage.controller.reset_viewmodel()
        stage.toggle_ads()
        for _i in range(18):
            stage.controller.tick(1.0 / 60.0)
        var cam_dir_after: Vector3 = -stage.camera.global_transform.basis.z.normalized()
        var camera_unchanged: bool = cam_dir_before.distance_to(cam_dir_after) < EPS
        var stable: Dictionary = await _check(stage,"ads")
        if not camera_unchanged or not stable["pass"]:
            report["all_guns_pass"]=false
        report["guns"][gun] = {"orientation_and_tags_by_action":poses,
            "camera_direction_unchanged_by_ads":camera_unchanged,
            "ads_orientation_pass":stable["pass"]}
        print("IW3_ROLL_GATE_GUN: " + JSON.stringify({"gun":gun,
            "all_four_actions_upright": poses.all(func(v: Dictionary) -> bool: return v["pass"]),
            "camera_fixed":camera_unchanged,
            "model_top_dot_up": stable["model_top_parallel_screen_up"]}))
    var out: FileAccess = FileAccess.open("res://godot-viewmodel-roll-gate.json",FileAccess.WRITE)
    if out==null:
        printerr("Cannot write roll audit metadata")
        quit(2)
        return
    out.store_string(JSON.stringify(report))
    out.close()
    print("IW3_VIEWMODEL_ROLL_90_GATE: "+JSON.stringify({
        "pass":report["all_guns_pass"],
        "guns":report["guns"].size(),"roll_deg":DEFAULT_ROLL,
        "screenshots_not_yet_retested_on_android":true}))
    stage.queue_free()
    quit(0 if report["all_guns_pass"] else 1)

func _initialize() -> void:
    call_deferred("_run")
