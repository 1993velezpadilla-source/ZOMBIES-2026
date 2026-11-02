extends SceneTree

# Tests exported demo's actual interactive scene without proprietary assets.
# Tests same two-finger input, dummies and ammo events as private IW3 lab.
const Demo = preload("res://android_safe.tscn")
const FRAME: float = 1.0/60.0

func _run() -> void:
    var report: Dictionary = {"procedural_only": true, "scene_loaded":false,
        "two_finger_touch":false,"walks":false,"aims":false,
        "fire_hits":false,"ads":false,"reload_cancel":false,
        "reload_finishes":false,"swap_all_guns":false,
        "ammo_persists":false,"scene_processes_frames":false,
        "android_device_tested":false,"errors":[]}
    var game = Demo.instantiate()
    root.add_child(game)
    await process_frame
    await physics_frame
    await process_frame
    var start: Dictionary = game.metrics()
    report["scene_loaded"]=start["scene_ready"] and start["gun_ready"] and          start["safe_primitives"] and start["primitive_parts"] >= 7 and          start["touch_controls"] >= 7
    var viewport: Vector2 = game.get_viewport().get_visible_rect().size
    var pos: Vector2 = Vector2(maxf(2.0,viewport.x*0.15),maxf(50.0,viewport.y*0.75))
    var down: InputEventScreenTouch = InputEventScreenTouch.new()
    down.index=2
    down.pressed=true
    down.position=pos
    game._unhandled_input(down)
    var move: InputEventScreenDrag = InputEventScreenDrag.new()
    move.index=2
    move.position=pos + Vector2(0,-90)
    game._unhandled_input(move)
    var other: InputEventScreenTouch = InputEventScreenTouch.new()
    other.index=3
    other.pressed=true
    other.position=Vector2(viewport.x*0.75,viewport.y*0.3)
    game._unhandled_input(other)
    var look: InputEventScreenDrag = InputEventScreenDrag.new()
    look.index=3
    look.position=other.position + Vector2(40,6)
    game._unhandled_input(look)
    report["two_finger_touch"]=game.touch_move_id==2 and game.touch_look_id==3
    report["aims"]=absf(game.yaw_degrees) > 1.0
    var origin: Vector3 = game.body.global_position
    for _i in range(18):
        await physics_frame
    var displacement: Vector3 = game.body.global_position-origin
    report["walks"]=Vector2(displacement.x,displacement.z).length() > 0.12
    down.pressed=false
    game._unhandled_input(down)
    other.pressed=false
    game._unhandled_input(other)
    # Recenter +X camera.
    game.yaw_degrees=0.0
    game.pitch_degrees=0.0
    game.body.rotation.y=0.0
    game.camera.rotation = Vector3(0.0,-PI/2.0,0.0)
    game.body.global_position=origin
    game.body.velocity=Vector3.ZERO
    await physics_frame
    var before: int = game.metrics()["magazine"]
    var shot: bool = game.fire()
    report["fire_hits"]=shot and game.metrics()["magazine"]==before-1 and game.impacts>=1
    report["ads"]=game.toggle_ads()
    for _i in range(18):
        await process_frame
    report["ads"]=report["ads"] and game.demo_ads_blend > 0.9
    var reloading: bool = game.reload()
    var interrupt: bool = game.fire()
    report["reload_cancel"]=reloading and interrupt and game.demo_reload_cancel_count==1 and not game.demo_is_reloading
    var reload_started: bool=game.reload()
    for _i in range(80):
        await process_frame
    report["reload_finishes"]=reload_started and game.metrics()["magazine"]==30 and not game.reload_pending
    var original_ammo: int=game.magazines["m4"]
    var one: bool=game.next_weapon()
    var name_one: String=game.metrics()["weapon"]
    var two: bool=game.next_weapon()
    var name_two: String=game.metrics()["weapon"]
    var three: bool=game.next_weapon()
    report["swap_all_guns"]=one and two and three and name_one=="ak47" and name_two=="mp5" and game.metrics()["weapon"]=="m4"
    report["ammo_persists"]=game.magazines["m4"]==original_ammo
    report["scene_processes_frames"]=game.demo_frame_count>18
    var requirements: Array[String] = ["scene_loaded","two_finger_touch","walks","aims",
        "fire_hits","ads","reload_cancel","reload_finishes","swap_all_guns",
        "ammo_persists","scene_processes_frames"]
    for key in requirements:
        if not report[key]:
            report["errors"].append(key)
    report["all"]=report["errors"].is_empty()
    var file: FileAccess=FileAccess.open("res://android-safe-gate.json",FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(report))
        file.close()
    print("IW3_ANDROID_SAFE_FPS_GATE: "+JSON.stringify(report))
    game.queue_free()
    quit(0 if report["all"] else 1)

func _initialize() -> void:
    call_deferred("_run")
