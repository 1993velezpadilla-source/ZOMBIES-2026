extends SceneTree

# PRIVATE VISUAL INSPECTION — 3 real owner-supplied IW3 weapons.
# Renders true pixels from user's GLB models; screenshot ZIP is encrypted with
# a user-controlled RSA public key BEFORE any GitHub artifact upload.
# Unlike the earlier bogus GREEN gates, tests actual skinned gun/hand geometry.
const Stage = preload("res://playground.tscn")
const GUNS: Array[String] = ["m4", "ak47", "mp5"]
const ROLLS: Array[float] = [0.0, 90.0, -90.0, 180.0]
const SCALE: float = 0.0254

func _pose_tag(skeleton: Skeleton3D, name: String) -> Vector3:
    var idx: int = skeleton.find_bone(name)
    if idx<0:
        return Vector3.ZERO
    skeleton.force_update_all_bone_transforms()
    return (skeleton.global_transform *
        skeleton.get_bone_global_pose(idx)).origin

func _reposition_source_viewmodel(stage: Node3D, roll: float) -> void:
    var gun: Node3D = stage.controller
    var rig: Node3D = stage.controller.mount
    gun.transform = Transform3D(
        (Basis(Vector3.UP,PI/2.0) * Basis(Vector3.RIGHT,deg_to_rad(roll)))
        .scaled(Vector3.ONE*SCALE),Vector3.ZERO)
    rig.position=Vector3.ZERO
    rig.initial_local_position=Vector3.ZERO
    rig.set_timed_action("idle",0.0)
    var eye: Vector3=_pose_tag(rig.hands_skeleton,"tag_camera")
    rig.position-=rig.to_local(eye)
    rig.initial_local_position=rig.position

func _snapshot(stage: Node3D, gun: String, roll: float, action: String) -> Dictionary:
    for _i in range(4):
        await process_frame
    RenderingServer.force_draw(false)
    var img: Image=root.get_texture().get_image()
    var name: String="%s_%03d_%s.png" % [gun,int(roll)+180,action]
    var abs_path: String=ProjectSettings.globalize_path("res://private_frames/"+name)
    var wrote: Error=img.save_png(abs_path)
    var rig: Node3D=stage.controller.mount
    var index: int=rig.weapon_skeleton.find_bone("tag_iron_sight")
    if index<0:
        index=rig.weapon_skeleton.find_bone("tag_reflex_sight")
    var sight: Dictionary={}
    if index>=0:
        var world_pt: Vector3=(rig.weapon_skeleton.global_transform *
            rig.weapon_skeleton.get_bone_global_pose(index)).origin
        var screen: Vector2=stage.camera.unproject_position(world_pt)
        sight={"uv_x":snappedf(screen.x/float(img.get_width()),0.0001),
            "uv_y":snappedf(screen.y/float(img.get_height()),0.0001)}
    return {"file":name,"save_ok":wrote==OK,
        "width":img.get_width(),"height":img.get_height(),
        "roll_degrees":roll,"action":action,"sight":sight}

func _run() -> void:
    root.size=Vector2i(1280,720)
    var output: String=ProjectSettings.globalize_path("res://private_frames")
    DirAccess.make_dir_recursive_absolute(output)
    var stage: Node3D=Stage.instantiate()
    root.add_child(stage)
    await process_frame
    await physics_frame
    await process_frame
    stage.set_process(false)
    var reports: Array[Dictionary]=[]
    var no_error: bool=true
    for weapon_i in range(GUNS.size()):
        var gun_name: String=GUNS[weapon_i]
        if not stage.equip(weapon_i):
            printerr("Cannot equip original model "+gun_name)
            no_error=false
            continue
        stage.controller.set_process(false)
        await process_frame
        for roll in ROLLS:
            _reposition_source_viewmodel(stage,roll)
            stage.controller.reset_viewmodel()
            stage.controller.mount.set_timed_action("idle",0.0)
            var hip: Dictionary=await _snapshot(stage,gun_name,roll,"hip")
            reports.append(hip)
            if not hip["save_ok"]:
                no_error=false
            stage.controller.reset_viewmodel()
            if not stage.controller.toggle_ads():
                no_error=false
            for _frame in range(18):
                stage.controller.tick(1.0/60.0)
            var ads: Dictionary=await _snapshot(stage,gun_name,roll,"ads")
            reports.append(ads)
            if not ads["save_ok"]:
                no_error=false
    var metadata: Dictionary={"samples":reports,
        "all_images_saved":no_error and reports.size()==GUNS.size()*ROLLS.size()*2,
        "private_images_only":true,
        "device_visual_approved":false,
        "original_owner_assets":true,
        "proprietary_images_never_uploaded_in_cleartext":true}
    var meta_file: FileAccess=FileAccess.open("res://private_frames/geometry-visual-report.json",FileAccess.WRITE)
    if meta_file==null:
        printerr("Cannot save geometry report")
        no_error=false
    else:
        meta_file.store_string(JSON.stringify(metadata))
        meta_file.close()
    print("IW3_REAL_PRIVATE_CAPTURE_GATE: "+JSON.stringify({
        "count":reports.size(),
        "all_saved":no_error,"contains_original_art":true,
        "private_encryption_required":true,
        "visually_approved":false}))
    stage.queue_free()
    quit(0 if no_error else 1)

func _initialize() -> void:
    call_deferred("_run")
