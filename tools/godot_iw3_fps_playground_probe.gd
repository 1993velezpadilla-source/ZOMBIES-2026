extends SceneTree

# Uses real user-owned COD4 animated GLBs that exist only within the temporary
# GitHub Actions runner. Exercises an actual interactive Godot FPS scene:
# arena collision, moving, aim, firing, ADS, reload, and weapon switching.
# Emits only counts and pass/fail; never exports or uploads proprietary assets.
const Scenario = preload("res://playground.tscn")

func _fail(issues: Array[String], reason: String) -> void:
    issues.append(reason)
    printerr("FPS_SCENE_ASSERT: " + reason)

func _run() -> void:
    var report: Dictionary = {"engine": Engine.get_version_info().get("string",""),
        "interactive_scene_loaded": false, "three_weapon_swap": false,
        "movement_works": false, "aim_works": false, "fire_and_hit": false,
        "reload_cancel_on_fire": false, "reload_completion": false,
        "ads_toggle": false, "touch_multifinger": false,
        "ammo_persists_between_swaps": false,
        "visual_correctness_approved": false, "android_device_verified": false,
        "rights_for_distribution": false, "errors": []}
    var errors: Array[String] = []
    var game = Scenario.instantiate()
    if game == null:
        _fail(errors, "Godot cannot instantiate interactive FPS scene")
    else:
        root.add_child(game)
        await process_frame
        await physics_frame
        await process_frame
        game.set_process(false) # deterministic fps state without wall clock
        var initial: Dictionary = game.metrics()
        report["interactive_scene_loaded"] = initial.get("scene_ready",false) and initial.get("gun_ready",false) and initial.get("touch_controls",0) >= 7
        if not report["interactive_scene_loaded"]:
            _fail(errors,"scene ready/3D viewmodel/7 touch buttons not initialized")

        var spawn: Vector3 = game.body.global_position
        var touch_start: InputEventScreenTouch = InputEventScreenTouch.new()
        touch_start.index = 1
        touch_start.pressed = true
        touch_start.position = Vector2(110, 440)
        game._unhandled_input(touch_start)
        var touch_move: InputEventScreenDrag = InputEventScreenDrag.new()
        touch_move.index = 1
        touch_move.position = Vector2(110, 355) # left thumb UP -> walk forward
        game._unhandled_input(touch_move)
        for _frame in range(16):
            await physics_frame
        var walked: float = game.body.global_position.distance_to(spawn)
        var touch_up: InputEventScreenTouch = InputEventScreenTouch.new()
        touch_up.index = 1
        touch_up.position = touch_move.position
        touch_up.pressed = false
        game._unhandled_input(touch_up)
        report["movement_works"] = walked > 0.15 and game.touch_move_id == -1
        if not report["movement_works"]:
            _fail(errors,"joystick forward movement did not displace collision body")

        var before_yaw: float = game.yaw_degrees
        var right_down: InputEventScreenTouch = InputEventScreenTouch.new()
        right_down.index = 2
        right_down.pressed = true
        right_down.position = Vector2(620, 180)
        game._unhandled_input(right_down)
        var right_drag: InputEventScreenDrag = InputEventScreenDrag.new()
        right_drag.index = 2
        right_drag.position = Vector2(645, 186)
        game._unhandled_input(right_drag)
        report["aim_works"] = absf(game.yaw_degrees - before_yaw) > 1.0
        var right_up: InputEventScreenTouch = InputEventScreenTouch.new()
        right_up.index = 2
        right_up.pressed = false
        right_up.position = right_drag.position
        game._unhandled_input(right_up)
        report["touch_multifinger"] = game.touch_move_id == -1 and game.touch_look_id == -1
        if not report["aim_works"] or not report["touch_multifinger"]:
            _fail(errors,"independent simultaneous touch look/joystick state failed")

        # Restore centre +X aim at target for raycast.
        game.yaw_degrees = 0.0
        game.pitch_degrees = 0.0
        game.body.rotation.y = 0.0
        game.camera.rotation = Vector3(0.0,-PI/2.0,0.0)
        await physics_frame
        game.body.global_position = spawn
        game.body.velocity = Vector3.ZERO
        await physics_frame
        var initial_mag: int = game.metrics()["magazine"]
        var fired: bool = game.fire()
        report["fire_and_hit"] = fired and game.shots == 1 and game.metrics()["magazine"] == initial_mag - 1 and game.impacts >= 1
        if not report["fire_and_hit"]:
            _fail(errors,"weapon ray did not hit target or consumed incorrect ammo")
        for frame in range(90):
            game.controller.tick(1.0 / 60.0)

        var toggle: bool = game.toggle_ads()
        for frame in range(30):
            game.controller.tick(1.0 / 60.0)
        var sight: Dictionary = game.controller.mount.aim_tag_info()
        report["ads_toggle"] = toggle and game.controller.ads_blend > 0.95 and not sight.get("name","").is_empty()
        if not report["ads_toggle"]:
            _fail(errors,"toggle ADS failed to reach steady state with original sight tag")

        var began: bool = game.reload()
        game.controller.tick(1.0 / 60.0)
        var interrupts: bool = game.fire()
        report["reload_cancel_on_fire"] = began and interrupts and game.controller.fire_during_reload_cancels == 1 and not game.reload_pending
        if not report["reload_cancel_on_fire"]:
            _fail(errors,"fire didn't cancel active reload")
        for frame in range(90):
            game.controller.tick(1.0 / 60.0)
        var start_second: bool = game.reload()
        if start_second:
            for frame in range(180):
                game.controller.tick(1.0/60.0)
                if game.controller.state != game.controller.State.RELOAD:
                    game._finish_reload()
                    break
        report["reload_completion"] = start_second and game.metrics()["magazine"] == 30 and not game.reload_pending
        if not report["reload_completion"]:
            _fail(errors,"reload animation failed to refill magazine correctly")

        var saved_m4: int = game.magazines["m4"]
        var swap_a: bool = game.next_weapon()
        var ok_ak47: bool = swap_a and game.metrics()["weapon"] == "ak47" and game.metrics()["gun_ready"]
        await process_frame
        var swap_b: bool = game.next_weapon()
        var ok_mp5: bool = swap_b and game.metrics()["weapon"] == "mp5" and game.metrics()["gun_ready"]
        await process_frame
        var swap_c: bool = game.next_weapon()
        var ok_m4: bool = swap_c and game.metrics()["weapon"] == "m4" and game.metrics()["gun_ready"]
        report["three_weapon_swap"] = ok_ak47 and ok_mp5 and ok_m4
        report["ammo_persists_between_swaps"] = game.magazines["m4"] == saved_m4
        if not report["three_weapon_swap"] or not report["ammo_persists_between_swaps"]:
            _fail(errors,"weapon swap failed or ammo state lost")
        game.queue_free()
    report["errors"] = errors
    report["all_checks"] = report["interactive_scene_loaded"] and report["movement_works"] and report["aim_works"] and report["fire_and_hit"] and report["reload_cancel_on_fire"] and report["reload_completion"] and report["ads_toggle"] and report["touch_multifinger"] and report["three_weapon_swap"] and report["ammo_persists_between_swaps"]
    var output: FileAccess = FileAccess.open("res://godot-fps-playground-gate.json",FileAccess.WRITE)
    if output != null:
        output.store_string(JSON.stringify(report))
        output.close()
    print("IW3_FPS_INTERACTIVE_GATE: " + JSON.stringify({
        "pass": report["all_checks"], "movement": report["movement_works"],
        "touch_multifinger": report["touch_multifinger"],
        "real_target_hit": report["fire_and_hit"],
        "ads": report["ads_toggle"],
        "reload_interrupt": report["reload_cancel_on_fire"],
        "reload_completion": report["reload_completion"],
        "3_gun_swap": report["three_weapon_swap"],
        "errors": errors, "android_device_verified": false}))
    quit(0 if report["all_checks"] else 1)

func _initialize() -> void:
    call_deferred("_run")
