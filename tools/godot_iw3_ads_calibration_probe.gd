extends SceneTree

# Adversarial corrective ADS gate: IW3 raw ADS keyframes did NOT align the sight
# in the fixed player camera. Original COD4 uses additional procedural viewmodel
# offsets. Test an automatically solved camera-space offset from a real original
# weapon attachment tag; do not invent per-gun XYZ or claim original IW behavior.
#
# Only numerical positioning and rig attachment metadata are persisted.
# Source COD4 meshes/animations and preview frames never leave the CI runner.

const Mount = preload("res://weapon_mount.gd")
const GUNS: Array[String] = ["m4", "ak47", "mp5"]
const EPS: float = 0.06

func _aim_tag(rig: Node) -> Dictionary:
    var skeleton: Skeleton3D = rig.weapon_skeleton
    if skeleton.find_bone("tag_iron_sight") >= 0:
        return {"name": "tag_iron_sight", "confidence": "attachment_tag_only"}
    if skeleton.find_bone("tag_reflex_sight") >= 0:
        return {"name": "tag_reflex_sight", "confidence": "optic_mount_approximation"}
    return {"name": "", "confidence": "no_aim_marker"}

func _at(skeleton: Skeleton3D, name: String) -> Vector3:
    var idx: int = skeleton.find_bone(name)
    return (skeleton.global_transform * skeleton.get_bone_global_pose(idx)).origin

func _offset(camera: Camera3D, world: Vector3, viewport: SubViewport) -> Array:
    var projected: Vector2 = camera.unproject_position(world)
    var dimensions: Vector2 = Vector2(viewport.size)
    var normalized: Vector2 = (projected - dimensions / 2.0) / dimensions
    return [snappedf(normalized.x, 0.00001), snappedf(normalized.y, 0.00001)]

func _run() -> void:
    var viewport: SubViewport = SubViewport.new()
    viewport.size = Vector2i(640, 360)
    root.add_child(viewport)
    var world: Node3D = Node3D.new()
    viewport.add_child(world)
    var camera: Camera3D = Camera3D.new()
    camera.near = 0.01
    camera.far = 60.0
    camera.fov = 80.0
    world.add_child(camera)
    camera.current = true
    var report: Dictionary = {"engine": Engine.get_version_info().get("string", ""),
        "camera_direction": "fixed IW3 +X; NEVER look_at(weapon)",
        "guns": {}, "all_numerical_offsets_solving": true,
        "ads_visual_approved": false, "original_ads_behavior_verified": false,
        "weapon_assets_distributed": false}
    await process_frame
    for gun in GUNS:
        var hands: Resource = load("res://weapons/" + gun + "_hands_animated_experimental.glb")
        var weapon: Resource = load("res://weapons/" + gun + "_animated_experimental.glb")
        if not (hands is PackedScene) or not (weapon is PackedScene):
            report["guns"][gun] = {"error": "missing GLB"}
            report["all_numerical_offsets_solving"] = false
            continue
        var rig = Mount.new()
        rig.scale = Vector3.ONE * 0.0254
        world.add_child(rig)
        if not rig.configure(hands as PackedScene, weapon as PackedScene):
            report["guns"][gun] = {"error": "cannot attach bone"}
            report["all_numerical_offsets_solving"] = false
            rig.queue_free()
            continue
        await process_frame
        rig.seek_action("idle", 0.0)
        await process_frame
        var eye: Vector3 = _at(rig.hands_skeleton, "tag_camera")
        camera.global_position = eye
        camera.look_at(eye + Vector3.RIGHT, Vector3.UP)
        var marker: Dictionary = _aim_tag(rig)
        var tag: String = marker["name"]
        if tag.is_empty():
            report["guns"][gun] = {"error": "no available aim tag"}
            report["all_numerical_offsets_solving"] = false
            rig.queue_free()
            continue
        var output: Dictionary = {"aim_bone": tag,
            "aim_marker_confidence": marker["confidence"],
            "camera_fixed": true, "frames": {}}
        for action in ["idle", "ads"]:
            var samples: Array = []
            var length: float = rig.hands_player.get_animation(action).length
            for progress in [0.0, 0.50, 0.90, 1.0]:
                rig.position = Vector3.ZERO  # avoid accumulated per-frame drift
                var time: float = length * float(progress)
                rig.seek_action(action, time)
                await process_frame
                rig.mount.on_skeleton_update()
                var position_before: Vector3 = _at(rig.weapon_skeleton, tag)
                var screen_before: Array = _offset(camera, position_before, viewport)
                var in_front: bool = not camera.is_position_behind(position_before)
                var local: Vector3 = camera.global_transform.affine_inverse() * position_before
                var displacement: Vector3 = camera.global_transform.basis * Vector3(-local.x, -local.y, 0.0)
                var blend: float = float(progress) if action == "ads" else 0.0
                rig.global_position += displacement * blend
                rig.hands_skeleton.force_update_all_bone_transforms()
                rig.weapon_skeleton.force_update_all_bone_transforms()
                rig.mount.on_skeleton_update()
                var position_after: Vector3 = _at(rig.weapon_skeleton, tag)
                var screen_after: Array = _offset(camera, position_after, viewport)
                var anchor_error: Dictionary = rig.anchor_error()
                var sample: Dictionary = {
                    "progress": progress, "time": snappedf(time, 0.00001),
                    "before": screen_before, "after": screen_after,
                    "in_front": in_front,
                    "moved_m": snappedf((displacement * blend).length(), 0.00001),
                    "anchor_error": anchor_error["anchor_position_error"],
                    "camera_unchanged": camera.global_position.distance_to(eye) < 0.000001}
                if action == "ads" and progress >= 0.9:
                    var centered: bool = absf(float(screen_after[0])) < EPS and absf(float(screen_after[1])) < EPS
                    sample["sight_centered_numerically"] = centered
                    if not centered or not in_front or float(anchor_error["anchor_position_error"]) > 0.001:
                        report["all_numerical_offsets_solving"] = false
                samples.append(sample)
            output["frames"][action] = samples
        report["guns"][gun] = output
        rig.queue_free()
        await process_frame
    var file: FileAccess = FileAccess.open("res://godot-ads-solver-gate.json", FileAccess.WRITE)
    if file == null:
        quit(2)
        return
    file.store_string(JSON.stringify(report))
    file.close()
    var summary: Dictionary = {}
    for gun in report["guns"]:
        var info: Dictionary = report["guns"][gun]
        var values: Array = info.get("frames", {}).get("ads", [])
        summary[gun] = {"aim_tag": info.get("aim_bone", "missing"),
           "offset_before_at_90": values[2]["before"] if values.size() > 2 else [],
           "offset_after_at_90": values[2]["after"] if values.size() > 2 else [],
           "moved_m_at_90": values[2]["moved_m"] if values.size() > 2 else -1.0}
    print("IW3_ADS_PROCEDURAL_SOLVER: " + JSON.stringify({
       "numerical_pass": report["all_numerical_offsets_solving"],
       "guns": summary, "visual_approval": false}))
    quit(0 if report["all_numerical_offsets_solving"] else 1)

func _initialize() -> void:
    call_deferred("_run")
