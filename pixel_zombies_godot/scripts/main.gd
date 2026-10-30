extends Node3D

const PlayerScript = preload("res://scripts/player.gd")
const ZombieScript = preload("res://scripts/zombie.gd")

var player: CharacterBody3D
var wave := 0
var score := 0
var enemies_alive := 0
var enemies_to_spawn := 0
var spawn_wait := 0.0
var next_wave_wait := -1.0
var game_over := false
var rng := RandomNumberGenerator.new()
var status: Label
var ammunition: Label
var crosshair: Label
var hint: Label
var restart_button: Button

func _ready() -> void:
    rng.randomize()
    _register_inputs()
    _make_level()
    player = PlayerScript.new()
    player.name = "Player"
    player.position = Vector3(0, 0.1, 3)
    add_child(player)
    player.died.connect(_on_player_died)
    _make_hud()
    _start_wave()

func _process(delta: float) -> void:
    if game_over:
        return
    if enemies_to_spawn > 0:
        spawn_wait -= delta
        if spawn_wait <= 0.0:
            _spawn_enemy()
            enemies_to_spawn -= 1
            spawn_wait = 1.15
    elif enemies_alive == 0:
        if next_wave_wait < 0.0:
            next_wave_wait = 3.0
        else:
            next_wave_wait -= delta
            if next_wave_wait <= 0.0:
                _start_wave()
    _refresh_hud()

func _start_wave() -> void:
    wave += 1
    enemies_to_spawn = 2 + wave * 2
    enemies_alive = 0
    spawn_wait = 0.5
    next_wave_wait = -1.0
    player.reserve_ammo += 32
    _refresh_hud()

func _spawn_enemy() -> void:
    var enemy := ZombieScript.new()
    var side := rng.randi_range(0, 3)
    var distance := rng.randf_range(-9.0, 9.0)
    var spawn_at := Vector3.ZERO
    if side == 0:
        spawn_at = Vector3(distance, 0.1, -9.5)
    elif side == 1:
        spawn_at = Vector3(distance, 0.1, 9.5)
    elif side == 2:
        spawn_at = Vector3(-9.5, 0.1, distance)
    else:
        spawn_at = Vector3(9.5, 0.1, distance)
    enemy.position = spawn_at
    enemy.target = player
    enemy.killed.connect(_on_enemy_killed)
    add_child(enemy)
    enemies_alive += 1

func _on_enemy_killed(_enemy: Node3D) -> void:
    enemies_alive = maxi(0, enemies_alive - 1)
    score += 100

func _on_player_died() -> void:
    game_over = true
    crosshair.hide()
    hint.text = "GAME OVER  |  R to restart"
    restart_button.show()

func _input(event: InputEvent) -> void:
    if game_over and event is InputEventKey and event.pressed and event.keycode == KEY_R:
        _restart()

func _restart() -> void:
    get_tree().reload_current_scene()

func _refresh_hud() -> void:
    if status == null or player == null:
        return
    status.text = "ROUND %d   HP %d   SCORE %d   ZOMBIES %d" % [wave, player.health, score, enemies_alive + enemies_to_spawn]
    ammunition.text = "RELOAD..." if player.is_reloading() else ("%d / %d" % [player.ammo, player.reserve_ammo])
    hint.text = "ROUND %d - incoming" % wave if next_wave_wait < 0.0 else "Next round in %.1f..." % next_wave_wait
    crosshair.visible = not player.aiming

func _make_hud() -> void:
    var layer := CanvasLayer.new()
    add_child(layer)
    var root := Control.new()
    root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    root.mouse_filter = Control.MOUSE_FILTER_IGNORE
    layer.add_child(root)

    status = _hud_label(root, Vector2(10, 8), Vector2(480, 30), 15)
    ammunition = _hud_label(root, Vector2(510, 8), Vector2(120, 34), 23)
    crosshair = _hud_label(root, Vector2(310, 163), Vector2(24, 35), 22)
    crosshair.text = "+"
    hint = _hud_label(root, Vector2(220, 32), Vector2(300, 30), 14)
    var move_hint := _hud_label(root, Vector2(15, 295), Vector2(170, 32), 17)
    move_hint.text = "◯ MOVE"

    var shoot := _button(root, "FIRE", Vector2(552, 222), Vector2(78, 64))
    shoot.button_down.connect(_fire_pressed)
    shoot.button_up.connect(_fire_released)
    var ads := _button(root, "ADS", Vector2(463, 282), Vector2(75, 54))
    ads.pressed.connect(_ads_pressed)
    var reload := _button(root, "RELOAD", Vector2(539, 295), Vector2(91, 45))
    reload.pressed.connect(_reload_pressed)
    var jump := _button(root, "JUMP", Vector2(463, 222), Vector2(74, 54))
    jump.pressed.connect(_jump_pressed)
    var sprint := _button(root, "RUN", Vector2(365, 289), Vector2(85, 50))
    sprint.button_down.connect(_sprint_down)
    sprint.button_up.connect(_sprint_up)
    restart_button = _button(root, "RESTART", Vector2(245, 195), Vector2(150, 46))
    restart_button.pressed.connect(_restart)
    restart_button.hide()

func _hud_label(root: Control, where: Vector2, bounds: Vector2, font_size: int) -> Label:
    var label := Label.new()
    label.position = where
    label.size = bounds
    label.add_theme_font_size_override("font_size", font_size)
    label.add_theme_color_override("font_color", Color(0.98, 0.92, 0.73))
    label.mouse_filter = Control.MOUSE_FILTER_IGNORE
    root.add_child(label)
    return label

func _button(root: Control, caption: String, where: Vector2, bounds: Vector2) -> Button:
    var button := Button.new()
    button.text = caption
    button.position = where
    button.size = bounds
    button.modulate.a = 0.75
    root.add_child(button)
    return button

func _fire_pressed() -> void:
    player.trigger_held = true

func _fire_released() -> void:
    player.trigger_held = false

func _ads_pressed() -> void:
    player.toggle_ads()

func _reload_pressed() -> void:
    player.reload()

func _jump_pressed() -> void:
    player.jump_touch = true

func _sprint_down() -> void:
    player.sprint_touch = true

func _sprint_up() -> void:
    player.sprint_touch = false

func _register_inputs() -> void:
    _map_key("move_forward", KEY_W)
    _map_key("move_back", KEY_S)
    _map_key("move_left", KEY_A)
    _map_key("move_right", KEY_D)
    _map_key("jump", KEY_SPACE)
    _map_key("sprint", KEY_SHIFT)
    _map_key("reload", KEY_R)

func _map_key(action: StringName, key: Key) -> void:
    if not InputMap.has_action(action):
        InputMap.add_action(action)
    var keyboard := InputEventKey.new()
    keyboard.physical_keycode = key
    InputMap.action_add_event(action, keyboard)

func _unhandled_key_input(event: InputEvent) -> void:
    if event.is_action_pressed("reload") and not game_over:
        player.reload()

func _make_level() -> void:
    var atmosphere := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.015, 0.025, 0.035)
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color(0.31, 0.38, 0.48)
    env.ambient_light_energy = 0.60
    atmosphere.environment = env
    add_child(atmosphere)

    _box(Vector3(0, -0.30, 0), Vector3(23.8, 0.6, 23.8), Color(0.23, 0.25, 0.24))
    _box(Vector3(-12, 2.5, 0), Vector3(0.5, 5.0, 24), Color(0.19, 0.21, 0.23))
    _box(Vector3(12, 2.5, 0), Vector3(0.5, 5.0, 24), Color(0.19, 0.21, 0.23))
    _box(Vector3(0, 2.5, -12), Vector3(24, 5.0, 0.5), Color(0.17, 0.18, 0.22))
    _box(Vector3(0, 2.5, 12), Vector3(24, 5.0, 0.5), Color(0.17, 0.18, 0.22))
    _box(Vector3(-4, 0.8, -3), Vector3(1.6, 1.6, 1.6), Color(0.35, 0.23, 0.14))
    _box(Vector3(5, 0.8, 4), Vector3(1.5, 1.6, 1.5), Color(0.35, 0.23, 0.14))
    _box(Vector3(0, 1.5, -6), Vector3(2.4, 3.0, 0.65), Color(0.20, 0.23, 0.23))
    _light(Vector3(0, 3.6, 0), Color(0.82, 0.83, 0.96), 2.0)
    _light(Vector3(-8, 3.1, -8), Color(1.0, 0.24, 0.14), 1.8)
    _light(Vector3(8, 3.1, 7), Color(0.15, 0.50, 1.0), 1.3)

func _box(where: Vector3, dimensions: Vector3, tint: Color) -> void:
    var obstacle := StaticBody3D.new()
    obstacle.position = where
    add_child(obstacle)
    var mesh := MeshInstance3D.new()
    var box := BoxMesh.new()
    box.size = dimensions
    mesh.mesh = box
    var material := StandardMaterial3D.new()
    material.albedo_color = tint
    material.roughness = 1.0
    mesh.material_override = material
    obstacle.add_child(mesh)
    var collision := CollisionShape3D.new()
    var shape := BoxShape3D.new()
    shape.size = dimensions
    collision.shape = shape
    obstacle.add_child(collision)

func _light(where: Vector3, tint: Color, energy: float) -> void:
    var lamp := OmniLight3D.new()
    lamp.position = where
    lamp.light_color = tint
    lamp.light_energy = energy
    lamp.omni_range = 14.0
    lamp.shadow_enabled = false
    add_child(lamp)
