extends SceneTree

# Regression against actual owner-supplied IW3 rigs, not fake test shapes.
# Real visual capture proved +90 keeps blue optic ABOVE magazine; prior
# -90 Android screenshots put magazine above optic and failed. Proves the
# *visible V4 indicator* and LIVE roll switches, plus original tag attachment.
const Stage = preload("res://playground.tscn")
const GUNS: Array[String] = ["m4","ak47","mp5"]

func _real_sight_to_mag(game: Node3D) -> Dictionary:
    var rig: Node3D = game.controller.mount
    var skeleton: Skeleton3D = rig.weapon_skeleton
    var sight_idx: int = skeleton.find_bone("tag_iron_sight")
    if sight_idx < 0:
        sight_idx = skeleton.find_bone("tag_reflex_sight")
    var clip_idx: int = skeleton.find_bone("tag_clip")
    if sight_idx < 0 or clip_idx < 0:
        return {"ok":false,"reason":"original gun sight / magazine tags missing"}
    skeleton.force_update_all_bone_transforms()
    var sight: Vector3 = (skeleton.global_transform *
        skeleton.get_bone_global_pose(sight_idx)).origin
    var clip: Vector3 = (skeleton.global_transform *
        skeleton.get_bone_global_pose(clip_idx)).origin
    var difference: Vector3 = game.camera.to_local(sight) - game.camera.to_local(clip)
    return {"ok": difference.y > 0.035 and absf(difference.x) < 0.016,
        "optic_above_mag_m":snappedf(difference.y,0.00001),
        "optic_side_offset_m":snappedf(difference.x,0.00001)}

func _run() -> void:
    var report: Dictionary = {"v5_real_gun_calibration_gate":false,"guns":{},
        "fails":[],"user_pixel_fold_visual_confirmation":false,
        "real_models":true}
    var game: Node3D=Stage.instantiate()
    root.add_child(game)
    await process_frame
    await physics_frame
    game.set_process(false)
    var count: int=0
    for name in GUNS:
        var loaded: bool=game.equip(GUNS.find(name))
        if not loaded:
            report["fails"].append("equip "+name)
            continue
        var message: String=game.message_label.text
        var controls: HBoxContainer=game.orientation_controls
        var ui_ok: bool=controls!=null and controls.get_child_count()==2 and \
            message.contains("IW3 V5 REAL GUNS") and message.contains("90")
        var beginning: Dictionary=_real_sight_to_mag(game)
        var original_anchor: Dictionary=game.controller.mount.anchor_error()
        var input_before: float=game.viewmodel_roll_degrees
        # Trigger actual touch-button signal, not a direct helper shortcut.
        var left: Button=controls.get_child(0) as Button
        left.emit_signal("pressed")
        var roll_zero: bool=absf(game.viewmodel_roll_degrees)<0.1
        var right: Button=controls.get_child(1) as Button
        right.emit_signal("pressed")
        var back_to_upright: bool=absf(game.viewmodel_roll_degrees-90.0)<0.1
        var after: Dictionary=_real_sight_to_mag(game)
        var next_anchor: Dictionary=game.controller.mount.anchor_error()
        # Source tag_camera is intentionally not in the viewer's eye any
        # longer; it previously put hands/receiver INSIDE the camera.
        # Verify ORIGINAL iron/reflex tag is at desired HIP depth/location.
        var mount: Node3D = game.controller.mount
        var bone_name: String=mount.aim_tag_info().get("name","")
        var optic_index: int=mount.weapon_skeleton.find_bone(bone_name)
        var optic_point: Vector3=(mount.weapon_skeleton.global_transform *
            mount.weapon_skeleton.get_bone_global_pose(optic_index)).origin
        var hip_local: Vector3=game.camera.to_local(optic_point)
        var expected: Vector3=Vector3(0.12,-0.12,-0.55)
        var hip_ok: bool=hip_local.distance_to(expected)<0.0005
        # In ADS the real tag must be 60 cm in front of camera and centered.
        var ads_on: bool=game.toggle_ads()
        var last_tick: Dictionary={}
        for _frame in range(24):
            last_tick=game.controller.tick(1.0/60.0)
        var optic_after: Vector3=(mount.weapon_skeleton.global_transform *
            mount.weapon_skeleton.get_bone_global_pose(optic_index)).origin
        var ads_local: Vector3=game.camera.to_local(optic_after)
        var ads_ok: bool=ads_on and last_tick.get("ok",false) and \
            last_tick.get("aligned",false) and \
            ads_local.distance_to(Vector3(0.0,0.0,-0.60))<0.005 and \
            game.controller.ads_blend>0.99 and \
            game.controller.failed_alignment_frames==0
        var valid: bool=ui_ok and absf(input_before-90.0)<0.1 and \
            beginning.get("ok",false) and after.get("ok",false) and roll_zero and \
            back_to_upright and hip_ok and ads_ok and \
            original_anchor.get("anchor_position_error",999.0)<0.0002 and \
            next_anchor.get("anchor_position_error",999.0)<0.0002
        report["guns"][name]={"pass":valid,"ui_correct":ui_ok,"initial_roll":input_before,
            "button_to_zero":roll_zero,"button_back_to_90":back_to_upright,
            "optical_landmark_before":beginning,"optical_landmark_after":after,
            "hip_optic_camera_m":[hip_local.x,hip_local.y,hip_local.z],
            "ads_optic_camera_m":[ads_local.x,ads_local.y,ads_local.z],
            "hip_target_reached":hip_ok,"ads_target_reached":ads_ok,
            "gun_attachment_m":next_anchor.get("anchor_position_error",-1)}
        if not valid:
            report["fails"].append(name)
        count += int(valid)
    report["v5_real_gun_calibration_gate"]=count==3
    var file: FileAccess=FileAccess.open("res://godot-live-roll-v4-gate.json",FileAccess.WRITE)
    if file == null:
        printerr("Cannot write live-roll gate")
        quit(2)
        return
    file.store_string(JSON.stringify(report))
    file.close()
    print("IW3_REAL_ANDROID_HIP_ADS_DEPTH_V5_GATE: "+
        JSON.stringify({"passed":count,"guns":3,
            "real_optic_above_mag_and_ads_safe_depth_proven":count==3,"user_visual_test_outstanding":true}))
    game.queue_free()
    quit(0 if count==3 else 1)

func _initialize() -> void:
    call_deferred("_run")
