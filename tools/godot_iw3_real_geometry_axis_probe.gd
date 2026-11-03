extends SceneTree

# Geometry-aware diagnostic, added after real Pixel Fold screenshots disproved
# the -90 and +90 numerical-only "upright" gates. NEVER label these as visually
# approved merely because the rig's nominal basis vector points camera-up.
# Inspect the ACTUAL source gun meshes, skeleton tag_camera/tag_weapon and
# real M4 AK47 MP5 tags (tag_flash + iron/reflex sight) at candidate roll angles.
# Report only numeric geometry projections, never proprietary model pixels.
const Game = preload("res://playground.tscn")
const GUNS: Array[String] = ["m4","ak47","mp5"]
const ROLLS: Array[float] = [0.0, 90.0, -90.0, 180.0]
const SCALE: float = 0.0254

func bone_world(skeleton: Skeleton3D, name: String) -> Transform3D:
    var index: int = skeleton.find_bone(name)
    if index < 0:
        return Transform3D.IDENTITY
    skeleton.force_update_all_bone_transforms()
    return skeleton.global_transform * skeleton.get_bone_global_pose(index)

func projected(camera: Camera3D, point: Vector3) -> Dictionary:
    var space: Vector3 = camera.to_local(point)
    var result: Dictionary = {"camera_space_m":[snappedf(space.x,0.00001),
        snappedf(space.y,0.00001),snappedf(space.z,0.00001)],
        "distance_m":snappedf(point.distance_to(camera.global_position),0.00001)}
    if space.z < -camera.near:
        var viewport: Vector2 = camera.get_viewport().get_visible_rect().size
        var uv: Vector2 = camera.unproject_position(point) / viewport
        result["screen_uv"]=[snappedf(uv.x,0.0001),snappedf(uv.y,0.0001)]
        result["in_frustum"]=camera.is_position_in_frustum(point)
    else:
        result["screen_uv"]=null
        result["in_frustum"]=false
    return result

func mesh_bounds(camera: Camera3D, root_node: Node) -> Dictionary:
    var boxes: Array[MeshInstance3D] = []
    var to_scan: Array[Node] = [root_node]
    while not to_scan.is_empty():
        var child: Node = to_scan.pop_back()
        if child is MeshInstance3D:
            boxes.append(child as MeshInstance3D)
        for next in child.get_children():
            to_scan.append(next)
    var lo: Vector3 = Vector3(INF, INF, INF)
    var hi: Vector3 = Vector3(-INF,-INF,-INF)
    var behind_count: int = 0
    var infront_count: int = 0
    for mesh in boxes:
        var bbox: AABB = mesh.get_aabb()
        for point_index in range(8):
            var bitmask: int = point_index
            var local: Vector3 = bbox.position + Vector3(
                bbox.size.x if bitmask & 1 else 0.0,
                bbox.size.y if bitmask & 2 else 0.0,
                bbox.size.z if bitmask & 4 else 0.0)
            var space: Vector3 = camera.to_local(mesh.to_global(local))
            lo = lo.min(space)
            hi = hi.max(space)
            if space.z >= -camera.near:
                behind_count += 1
            else:
                infront_count += 1
    return {"mesh_count":boxes.size(),"corners_ahead":infront_count,
        "corners_behind_or_inside_camera":behind_count,
        "min_camera_xyz":[snappedf(lo.x,0.001),snappedf(lo.y,0.001),snappedf(lo.z,0.001)],
        "max_camera_xyz":[snappedf(hi.x,0.001),snappedf(hi.y,0.001),snappedf(hi.z,0.001)]}

func _test_roll(game: Node3D, roll: float) -> Dictionary:
    var control: Node3D = game.controller
    var rig: Node3D = control.mount
    var camera: Camera3D = game.camera
    # Compare on the same original idle source meshes; no animation retarget
    # assumptions are needed to report real tag offsets.
    control.transform = Transform3D(
        (Basis(Vector3.UP, PI * 0.5) *
         Basis(Vector3.RIGHT, deg_to_rad(roll))).scaled(Vector3.ONE*SCALE),
        Vector3.ZERO)
    rig.position = Vector3.ZERO
    rig.initial_local_position = Vector3.ZERO
    rig.set_timed_action("idle",0.0)
    var eye: Transform3D = bone_world(rig.hands_skeleton,"tag_camera")
    var eye_local: Vector3 = rig.to_local(eye.origin)
    rig.position -= eye_local
    rig.initial_local_position = rig.position
    await process_frame
    rig.hands_skeleton.force_update_all_bone_transforms()
    rig.weapon_skeleton.force_update_all_bone_transforms()
    var out: Dictionary = {"roll_degrees":roll,
        "note":"Real weapon geometry observations, NOT visual approval",
        "tags":{}}
    for tag in ["tag_weapon","tag_camera","tag_ads"]:
        var index: int = rig.hands_skeleton.find_bone(tag)
        if index>=0:
            out["tags"]["hands_"+tag]=projected(camera,bone_world(rig.hands_skeleton,tag).origin)
    for tag in ["tag_flash","tag_iron_sight","tag_reflex_sight","tag_acog","tag_brass"]:
        var index: int = rig.weapon_skeleton.find_bone(tag)
        if index>=0:
            out["tags"]["weapon_"+tag]=projected(camera,bone_world(rig.weapon_skeleton,tag).origin)
    out["hands_mesh_aabb"]=mesh_bounds(camera,rig.hands_root)
    out["gun_mesh_aabb"]=mesh_bounds(camera,rig.weapon_root)
    out["gun_to_hands_attachment"]=rig.anchor_error()
    var muzzle: Dictionary = out["tags"].get("weapon_tag_flash",{})
    var sight: Dictionary = out["tags"].get("weapon_tag_iron_sight",
        out["tags"].get("weapon_tag_reflex_sight",{}))
    var front: Array = muzzle.get("camera_space_m",[])
    var rear: Array = sight.get("camera_space_m",[])
    if front.size()==3 and rear.size()==3:
        out["front_farther_into_screen_than_sight"] = float(front[2]) < float(rear[2])
        out["muzzle_look_above_sight_m"]=snappedf(float(front[1])-float(rear[1]),0.00001)
        out["muzzle_left_right_of_sight_m"]=snappedf(float(front[0])-float(rear[0]),0.00001)
    return out

func _run() -> void:
    var report: Dictionary={"device_reports":["9 oclock original","6 oclock -90",
        "still visibly wrong +90"],"authoritative_visual_status":"FAILED_ON_PHONE",
        "geometry_candidates":{},"has_geometry":true,"vision_approved":false}
    var stage: Node3D = Game.instantiate()
    root.add_child(stage)
    await process_frame
    await physics_frame
    for i in range(GUNS.size()):
        if not stage.equip(i):
            report["has_geometry"]=false
            report["geometry_candidates"][GUNS[i]]={"error":"equip failed"}
            continue
        await process_frame
        var shots: Array = []
        for roll in ROLLS:
            shots.append(await _test_roll(stage,roll))
        report["geometry_candidates"][GUNS[i]]=shots
        print("IW3_REAL_GEOMETRY_AXIS_SWEEP: "+JSON.stringify({
            "weapon":GUNS[i],
            "candidates":shots.map(func(row:Dictionary)->Dictionary:
                return {"roll":row["roll_degrees"],
                    "sight":row["tags"].get("weapon_tag_iron_sight",
                        row["tags"].get("weapon_tag_reflex_sight",{})).get("screen_uv",null),
                    "flash":row["tags"].get("weapon_tag_flash",{}).get("screen_uv",null),
                    "front_forward":row.get("front_farther_into_screen_than_sight",false),
                    "gun_camera_intersections":row["gun_mesh_aabb"]["corners_behind_or_inside_camera"],
                    "hands_camera_intersections":row["hands_mesh_aabb"]["corners_behind_or_inside_camera"]}))
    var file: FileAccess=FileAccess.open("res://godot-geometry-axis-sweep.json",FileAccess.WRITE)
    if file==null:
        printerr("Axis sweep report cannot be written")
        quit(2)
        return
    file.store_string(JSON.stringify(report))
    file.close()
    print("IW3_REAL_MESH_GEOMETRY_DIAGNOSTIC: "+JSON.stringify({
        "real_weapon_models":report["geometry_candidates"].size(),
        "candidate_rolls_per_model":ROLLS.size(),
        "visual_status":"FAILED_ON_PHONE; NOT CERTIFIED",
        "generated_only_numerical_metadata":true}))
    stage.queue_free()
    quit(0 if report["has_geometry"] else 1)

func _initialize() -> void:
    call_deferred("_run")
