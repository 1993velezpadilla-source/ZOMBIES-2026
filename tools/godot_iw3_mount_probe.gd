extends SceneTree

# Mounts the user's privately extracted IW3 gun models to the animated
# tag_weapon bone of the original viewhands, exercising all 4 actions.
# Writes ONLY metadata to CI artifacts. Does not certify visual alignment.

const WeaponMount = preload("res://weapon_mount.gd")
const GUNS := ["m4", "ak47", "mp5"]
const ACTIONS := ["idle", "ads", "fire", "reload"]
const FRACTIONS := [0.0, 0.5, 0.9]

func _run() -> void:
    var report: Dictionary = {"engine": Engine.get_version_info().get("string", ""),
        "gun_reports": {}, "all_bone_attachments_valid": true,
        "all_actions_covered": true, "visual_pose_verified": false,
        "ads_sight_alignment_verified": false, "legal_distribution_cleared": false}
    for gun in GUNS:
        var hands_file: String = "res://weapons/" + str(gun) + "_hands_animated_experimental.glb"
        var weapon_file: String = "res://weapons/" + str(gun) + "_animated_experimental.glb"
        var hands: Resource = load(hands_file)
        var weapon: Resource = load(weapon_file)
        if not (hands is PackedScene) or not (weapon is PackedScene):
            report["gun_reports"][gun] = {"error": "missing original GLB"}
            report["all_bone_attachments_valid"] = false
            continue
        var rig = WeaponMount.new()
        rig.name = str(gun) + "_fps_mount"
        root.add_child(rig)
        var valid: bool = rig.configure(hands as PackedScene, weapon as PackedScene)
        if not valid:
            report["gun_reports"][gun] = {"error": "failed mounting gun to viewhands tag_weapon"}
            report["all_bone_attachments_valid"] = false
            rig.queue_free()
            continue
        await process_frame
        var output: Dictionary = {"mount_bone": rig.mount.bone_name,
            "base_tag_camera_present": rig.hands_skeleton.find_bone("tag_camera") >= 0,
            "weapon_skeleton_bones": rig.weapon_skeleton.get_bone_count(),
            "hand_skeleton_bones": rig.hands_skeleton.get_bone_count(),
            "action_metrics": {}}
        for action in ACTIONS:
            var entries: Array = []
            var seconds: float = rig.hands_player.get_animation(action).length
            var previous: Vector3 = Vector3.ZERO
            for fraction in FRACTIONS:
                var at: float = seconds * float(fraction)
                var could_seek: bool = rig.seek_action(action, at)
                await process_frame
                rig.hands_skeleton.force_update_all_bone_transforms()
                rig.mount.on_skeleton_update()
                var entry: Dictionary = rig.anchor_error()
                entry["time_seconds"] = snappedf(at, 0.00001)
                entry["camera_to_weapon_pivot_distance"] = snappedf(
                    rig.diagnostic_camera_to_weapon_distance(), 0.00001)
                entry["attachment_mounted"] = could_seek
                if entry["anchor_position_error"] > 0.001 or not entry["bone_valid"] or not entry["weapon_parent_is_attachment"]:
                    report["all_bone_attachments_valid"] = false
                entries.append(entry)
            output["action_metrics"][action] = entries
            if entries.size() != FRACTIONS.size():
                report["all_actions_covered"] = false
        report["gun_reports"][gun] = output
        rig.queue_free()
        await process_frame
    var file: FileAccess = FileAccess.open("res://godot-mount-gate.json", FileAccess.WRITE)
    if file == null:
        push_error("Cannot save Godot mount report")
        quit(2)
        return
    file.store_string(JSON.stringify(report))
    file.close()
    print("IW3_GODOT_MOUNT_GATE: " + JSON.stringify({
        "engine": report["engine"],
        "three_guns": report["gun_reports"].size() == 3,
        "all_bone_attachments_valid": report["all_bone_attachments_valid"],
        "all_actions_covered": report["all_actions_covered"],
        "visual_pose_verified": false}))
    quit(0 if report["all_bone_attachments_valid"] and report["all_actions_covered"] else 1)

func _initialize() -> void:
    call_deferred("_run")
