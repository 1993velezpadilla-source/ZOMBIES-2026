extends SceneTree

# OFFSCREEN visual occupancy gate: renders original first-person meshes only
# inside the throwaway CI runner via Xvfb/Mesa. The screenshots never leave
# the runner, are not committed and are not uploaded to GitHub artifacts.
# A non-blank frame is NOT proof of anatomically correct hands/ADS/reload.

const WeaponMount = preload("res://weapon_mount.gd")
const GUNS := ["m4", "ak47", "mp5"]
const ACTIONS := ["idle", "ads", "fire", "reload"]

func _frame_stats(image: Image) -> Dictionary:
    if image == null or image.is_empty():
        return {"valid_image": false}
    var w: int = image.get_width()
    var h: int = image.get_height()
    var background: Color = image.get_pixel(0, 0)
    var examined: int = 0
    var foreground: int = 0
    var bbox: Rect2i = Rect2i()
    var lo_x: int = w
    var lo_y: int = h
    var hi_x: int = 0
    var hi_y: int = 0
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            var p: Color = image.get_pixel(x, y)
            var diff: float = maxf(absf(p.r - background.r),
                         maxf(absf(p.g - background.g),absf(p.b - background.b)))
            examined += 1
            if diff > 0.08:
                foreground += 1
                lo_x = mini(lo_x,x)
                lo_y = mini(lo_y,y)
                hi_x = maxi(hi_x,x)
                hi_y = maxi(hi_y,y)
    var box: Array = []
    if foreground > 0:
        box = [lo_x, lo_y, hi_x, hi_y]
    return {"valid_image": true, "width": w, "height": h,
            "sampled_pixels": examined, "foreground_pixels": foreground,
            "foreground_fraction": snappedf(float(foreground)/maxf(1.0,float(examined)),0.0001),
            "bbox": box}

func _make_viewport() -> Dictionary:
    var viewport := SubViewport.new()
    viewport.size = Vector2i(640, 360)
    viewport.transparent_bg = false
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    root.add_child(viewport)
    var world := Node3D.new()
    viewport.add_child(world)
    var env := WorldEnvironment.new()
    env.environment = Environment.new()
    env.environment.background_mode = Environment.BG_COLOR
    env.environment.background_color = Color(0.12,0.16,0.22)
    env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.environment.ambient_light_color = Color(1.0,1.0,1.0)
    env.environment.ambient_light_energy = 1.4
    world.add_child(env)
    var light := DirectionalLight3D.new()
    light.rotation_degrees = Vector3(-30.0,-30.0,0.0)
    light.light_energy = 2.0
    world.add_child(light)
    var camera := Camera3D.new()
    camera.fov = 80.0
    camera.near = 0.01
    camera.far = 50.0
    world.add_child(camera)
    camera.current = true
    return {"viewport": viewport, "world": world, "camera": camera}

func _run() -> void:
    var result: Dictionary = {"engine":Engine.get_version_info().get("string",""),
       "render_driver":RenderingServer.get_current_rendering_driver_name(),
       "guns":{},"images_private_only":true,
       "frames_visually_approved":false,"aim_down_sights_approved":false}
    var scene_parts: Dictionary = _make_viewport()
    var viewport: SubViewport = scene_parts["viewport"]
    var world: Node3D = scene_parts["world"]
    var camera: Camera3D = scene_parts["camera"]
    await process_frame
    for gun in GUNS:
        var hands: Resource = load("res://weapons/" + str(gun) + "_hands_animated_experimental.glb")
        var weapon: Resource = load("res://weapons/" + str(gun) + "_animated_experimental.glb")
        if not (hands is PackedScene) or not (weapon is PackedScene):
            result["guns"][gun] = {"error":"missing PackedScene"}
            continue
        var rig = WeaponMount.new()
        rig.scale = Vector3.ONE * 0.0254  # IW3 1 unit ~ inch; test conversion to Godot metres.
        world.add_child(rig)
        if not rig.configure(hands as PackedScene, weapon as PackedScene):
            result["guns"][gun] = {"error":"could not attach gun to tag_weapon"}
            rig.queue_free()
            continue
        await process_frame
        rig.seek_action("idle",0.0)
        await process_frame
        var idx: int = rig.hands_skeleton.find_bone("tag_camera")
        var baseline: Transform3D = rig.hands_skeleton.global_transform * rig.hands_skeleton.get_bone_global_pose(idx)
        camera.global_position = baseline.origin
        camera.look_at(rig.weapon_root.global_position, Vector3.UP)
        var per_action: Dictionary = {"baseline_camera_distance_meters":snappedf(
               camera.global_position.distance_to(rig.weapon_root.global_position),0.0001),
               "actions":{}}
        for action in ACTIONS:
            var length: float = rig.hands_player.get_animation(action).length
            var tm: float = minf(length*0.5, maxf(0.0,length - 0.001))
            rig.seek_action(action,tm)
            await process_frame
            await process_frame
            RenderingServer.force_draw(false)
            var img: Image = viewport.get_texture().get_image()
            var metrics: Dictionary = _frame_stats(img)
            metrics["sample_time"]=snappedf(tm,0.0001)
            metrics["mounted"]=rig.anchor_error()
            # Only numeric occupancy metadata; no image files saved.
            per_action["actions"][action]=metrics
        result["guns"][gun]=per_action
        rig.queue_free()
        await process_frame
    var outputs: FileAccess = FileAccess.open("res://godot-render-gate.json",FileAccess.WRITE)
    if outputs == null:
        printerr("Failed storing visual-render metadata")
        quit(2)
        return
    outputs.store_string(JSON.stringify(result))
    outputs.close()
    var view_rates := {}
    for gun in result["guns"]:
        var actions := {}
        for action in result["guns"][gun].get("actions",{}):
            actions[action]=result["guns"][gun]["actions"][action].get("foreground_fraction",-1)
        view_rates[gun]=actions
    print("IW3_RENDER_GATE: " + JSON.stringify({
       "render_driver":result["render_driver"],"occupancy_fraction":view_rates,
       "visual_pose_approved":false,"screenshots_uploaded":false}))
    quit(0)

func _initialize() -> void:
    call_deferred("_run")
