extends SceneTree

# First genuine FPS-camera calibration gate for extracted IW3 gun + hands.
# Unlike the earlier visual smoke test, this camera is NEVER aimed at the
# weapon pivot; it is anchored to the hands' original tag_camera at idle,
# then held fixed while ADS, fire and reload animate.
#
# Compares coordinate-axis hypotheses from IW3 -> OAT -> glTF conversion.
# Renders frames in an ephemeral Xvfb/OpenGL runner. NO screenshots, models,
# animations, or image pixels are written to disk or CI artifacts.
# Pixel occupancy and projected attachment-tag positions are diagnostics,
# NOT visual confirmation that ADS/poses are anatomically correct.

const WeaponMount = preload("res://weapon_mount.gd")
const GUNS: Array[String] = ["m4", "ak47", "mp5"]
const ACTIONS: Array[String] = ["idle", "ads", "fire", "reload"]
const WORLD_UP: Vector3 = Vector3.UP

func _make_viewport() -> Dictionary:
    var viewport: SubViewport = SubViewport.new()
    viewport.size = Vector2i(640, 360)
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    viewport.transparent_bg = false
    root.add_child(viewport)
    var world: Node3D = Node3D.new()
    viewport.add_child(world)
    var environment: WorldEnvironment = WorldEnvironment.new()
    environment.environment = Environment.new()
    environment.environment.background_mode = Environment.BG_COLOR
    environment.environment.background_color = Color(0.07, 0.12, 0.19)
    environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.environment.ambient_light_color = Color.WHITE
    environment.environment.ambient_light_energy = 1.4
    world.add_child(environment)
    var light: DirectionalLight3D = DirectionalLight3D.new()
    light.rotation_degrees = Vector3(-28.0, -37.0, 0.0)
    light.light_energy = 1.8
    world.add_child(light)
    var camera: Camera3D = Camera3D.new()
    camera.fov = 80.0
    camera.near = 0.01
    camera.far = 75.0
    world.add_child(camera)
    camera.current = true
    return {"viewport": viewport, "world": world, "camera": camera}

func _sample_image(image: Image) -> Dictionary:
    if image == null or image.is_empty():
        return {"valid": false, "pixels": 0}
    var background: Color = image.get_pixel(0, 0)
    var total: int = 0
    var altered: int = 0
    var min_x: int = image.get_width()
    var min_y: int = image.get_height()
    var max_x: int = 0
    var max_y: int = 0
    for y in range(0, image.get_height(), 6):
        for x in range(0, image.get_width(), 6):
            var pixel: Color = image.get_pixel(x, y)
            total += 1
            var diff: float = maxf(absf(pixel.r - background.r),
                maxf(absf(pixel.g - background.g), absf(pixel.b - background.b)))
            if diff > 0.10:
                altered += 1
                min_x = mini(min_x, x)
                min_y = mini(min_y, y)
                max_x = maxi(max_x, x)
                max_y = maxi(max_y, y)
    var box: Array[int] = []
    if altered > 0:
        box = [min_x, min_y, max_x, max_y]
    return {"valid": true, "pixels": total, "foreground": altered,
            "fraction": snappedf(float(altered) / float(maxi(total, 1)), 0.0001),
            "bbox": box}

func _bone_pose(skeleton: Skeleton3D, name: String) -> Transform3D:
    var index: int = skeleton.find_bone(name)
    if index < 0:
        return Transform3D.IDENTITY
    return skeleton.global_transform * skeleton.get_bone_global_pose(index)

func _possible_tag_names(skeleton: Skeleton3D) -> Array[String]:
    var found: Array[String] = []
    for index in range(skeleton.get_bone_count()):
        var name: String = skeleton.get_bone_name(index)
        if name.begins_with("tag_"):
            found.append(name)
    return found

func _apply_camera(camera: Camera3D, hypothesis: String, reference: Transform3D) -> void:
    camera.global_position = reference.origin
    match hypothesis:
        "bone_orientation":
            camera.global_transform = Transform3D(reference.basis.orthonormalized(), reference.origin)
        "iw3_forward_plus_x":
            camera.look_at(reference.origin + Vector3.RIGHT, WORLD_UP)
        "world_minus_x":
            camera.look_at(reference.origin + Vector3.LEFT, WORLD_UP)
        "world_plus_z":
            camera.look_at(reference.origin + Vector3.BACK, WORLD_UP)
        "world_minus_z":
            camera.look_at(reference.origin + Vector3.FORWARD, WORLD_UP)
        "bone_forward_plus_x":
            camera.look_at(reference.origin + reference.basis.x.normalized(), WORLD_UP)
        "bone_forward_minus_z":
            camera.look_at(reference.origin - reference.basis.z.normalized(), WORLD_UP)
        _:
            camera.look_at(reference.origin + Vector3.RIGHT, WORLD_UP)

func _point_projection(camera: Camera3D, point: Vector3, viewport: SubViewport) -> Dictionary:
    var camera_space: Vector3 = camera.global_transform.affine_inverse() * point
    if absf(camera_space.z) < 0.00001:
        return {"projection_valid": false, "behind": true,
            "in_frustum": false, "screen": null, "center_offset": null,
            "reason": "point lies on camera image plane"}
    var behind: bool = camera.is_position_behind(point)
    var projection: Vector2 = camera.unproject_position(point)
    var dims: Vector2 = Vector2(viewport.size)
    var center_delta: Vector2 = (projection - dims * 0.5) / dims
    return {"projection_valid": true, "behind": behind, "in_frustum": camera.is_position_in_frustum(point),
       "screen": [snappedf(projection.x, 0.001), snappedf(projection.y, 0.001)],
       "center_offset": [snappedf(center_delta.x, 0.0001), snappedf(center_delta.y, 0.0001)],
       "camera_distance_m": snappedf(camera.global_position.distance_to(point), 0.0001)}

func _run() -> void:
    var scene: Dictionary = _make_viewport()
    var viewport: SubViewport = scene["viewport"]
    var world: Node3D = scene["world"]
    var camera: Camera3D = scene["camera"]
    var report: Dictionary = {
       "engine": Engine.get_version_info().get("string", ""),
       "renderer": RenderingServer.get_current_rendering_driver_name(),
       "mode": "Original tag_camera stays stationary while hands/gun animate",
       "hypotheses_not_auto_approved": true, "guns": {},
       "visual_approval": false, "ads_ironsights_verified": false,
       "copyrighted_assets_uploaded": false}
    await process_frame
    for gun in GUNS:
        var hands: Resource = load("res://weapons/" + gun + "_hands_animated_experimental.glb")
        var weapon: Resource = load("res://weapons/" + gun + "_animated_experimental.glb")
        if not (hands is PackedScene) or not (weapon is PackedScene):
            report["guns"][gun] = {"error": "original GLB is missing"}
            continue
        var rig = WeaponMount.new()
        rig.scale = Vector3.ONE * 0.0254
        world.add_child(rig)
        if not rig.configure(hands as PackedScene, weapon as PackedScene):
            report["guns"][gun] = {"error": "cannot mount gun to tag_weapon"}
            rig.queue_free()
            continue
        await process_frame
        rig.seek_action("idle", 0.0)
        await process_frame
        var eye: Transform3D = _bone_pose(rig.hands_skeleton, "tag_camera")
        var info: Dictionary = {"camera_tag_found": rig.hands_skeleton.find_bone("tag_camera") >= 0,
            "hand_tags": _possible_tag_names(rig.hands_skeleton),
            "weapon_tags": _possible_tag_names(rig.weapon_skeleton),
            "mount_error_at_idle": rig.anchor_error(), "candidate_views": {}}
        if not info["camera_tag_found"]:
            report["guns"][gun] = {"error": "no original tag_camera", "tags": info}
            rig.queue_free()
            continue
        var hypotheses: Array[String] = ["bone_orientation", "iw3_forward_plus_x",
            "world_minus_x", "world_plus_z", "world_minus_z",
            "bone_forward_plus_x", "bone_forward_minus_z"]
        for hypothesis in hypotheses:
            _apply_camera(camera, hypothesis, eye)
            var actions: Dictionary = {}
            for action in ACTIONS:
                var anim_length: float = rig.hands_player.get_animation(action).length
                var when: float = 0.90 * anim_length if action == "ads" else 0.50 * anim_length
                if action == "idle":
                    when = 0.0
                rig.seek_action(action, when)
                await process_frame
                await process_frame
                RenderingServer.force_draw(false)
                var image: Image = viewport.get_texture().get_image()
                var values: Dictionary = _sample_image(image)
                values["time_seconds"] = snappedf(when, 0.0001)
                values["weapon_pivot"] = _point_projection(camera, rig.weapon_root.global_position, viewport)
                values["tag_camera_stationary"] = camera.global_position.distance_to(eye.origin) < 0.000001
                values["attachment_position_error_m"] = rig.anchor_error()["anchor_position_error"]
                for tag in ["tag_flash", "tag_aim", "tag_scope", "tag_sight", "tag_iron_sight", "tag_reflex_sight", "tag_acog", "tag_brass", "tag_clip"]:
                    if rig.weapon_skeleton.find_bone(tag) >= 0:
                        values[tag] = _point_projection(camera, _bone_pose(rig.weapon_skeleton, tag).origin, viewport)
                if rig.hands_skeleton.find_bone("tag_ads") >= 0:
                    values["hands_tag_ads"] = _point_projection(camera, _bone_pose(rig.hands_skeleton, "tag_ads").origin, viewport)
                actions[action] = values
            info["candidate_views"][hypothesis] = actions
        report["guns"][gun] = info
        rig.queue_free()
        await process_frame
    var file: FileAccess = FileAccess.open("res://godot-fps-camera-gate.json", FileAccess.WRITE)
    if file == null:
        printerr("Cannot store FPS camera metrics")
        quit(2)
        return
    file.store_string(JSON.stringify(report))
    file.close()
    var condensed: Dictionary = {}
    for gun in report["guns"]:
        condensed[gun] = {}
        for hypothesis in report["guns"][gun].get("candidate_views", {}):
            var values: Dictionary = {}
            for action in ACTIONS:
                var stat: Dictionary = report["guns"][gun]["candidate_views"][hypothesis][action]
                values[action] = stat.get("fraction", -1.0)
            condensed[gun][hypothesis] = values
    print("IW3_REAL_FPS_CAMERA_GATE: " + JSON.stringify({
       "renderer": report["renderer"], "camera_fixed": true,
       "render_occupancy": condensed,
       "confirmed_sight_alignment": false,
       "private_only": true}))
    quit(0 if report["guns"].size() == 3 else 1)

func _initialize() -> void:
    call_deferred("_run")
