extends Node3D
## ZOMBIES-2026 / first *original* Android FPS vertical slice.
## GODOT prototype, NOT a port of IW3. No COD game assets or weapon stats.

const ZOMBIE_SCENE_SCRIPT = preload("res://zombie.gd")
const ARENA_RADIUS := 14.0
const CLIP_SIZE := 24 # Original PROTOTYPE placeholders, not COD4 weapon timing.
const FIRE_INTERVAL := 0.19
const RELOAD_SECONDS := 1.9

var player: CharacterBody3D
var view: Camera3D
var gun: Node3D
var hud: Control
var status_label: Label
var ammo_label: Label
var wave_label: Label
var hint_label: Label
var crosshair: Label
var menu: Control
var menu_title: Label
var menu_button: Button
var fire_button: Button
var reload_button: Button
var ads_button: Button
var sprint_button: Button
var joy_background: Panel
var joy_dot: Panel

var started := false
var dead := false
var fire_held := false
var ads_held := false
var sprint_held := false
var left_touch := -1
var right_touch := -1
var joystick := Vector2.ZERO
var yaw := 0.0
var pitch := 0.0
var player_health := 100
var score := 0
var wave := 0
var clip := CLIP_SIZE
var reserve := 144
var shot_cooldown := 0.0
var reload_timer := 0.0
var spawn_timer := 0.0
var remaining_to_spawn := 0
var round_wait := 0.0
var shoot_flash := 0.0
var ambient_lamp: OmniLight3D

func _ready() -> void:
	# Android/Foldables: enforce landscape, not portrait letterboxing.
	if OS.has_feature("mobile") and DisplayServer.has_feature(DisplayServer.FEATURE_ORIENTATION):
		DisplayServer.screen_set_orientation(DisplayServer.SCREEN_SENSOR_LANDSCAPE)
	randomize()
	_build_world()
	_build_player()
	_build_hud()
	get_viewport().size_changed.connect(_layout_hud)
	_layout_hud()
	_update_labels()
	if not OS.has_feature("mobile"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func _material(color: Color, roughness: float = 0.9) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = roughness
	return mat

func _box(where: Vector3, dimensions: Vector3, tint: Color) -> void:
	var body := StaticBody3D.new()
	body.position = where
	var visible_box := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = dimensions
	visible_box.mesh = box
	visible_box.material_override = _material(tint)
	body.add_child(visible_box)
	var shape := CollisionShape3D.new()
	var collision := BoxShape3D.new()
	collision.size = dimensions
	shape.shape = collision
	body.add_child(shape)
	add_child(body)

func _build_world() -> void:
	var world_env := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.035, 0.045, 0.067)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.31, 0.35, 0.43)
	env.ambient_light_energy = 0.55
	world_env.environment = env
	add_child(world_env)
	var moon := DirectionalLight3D.new()
	moon.rotation_degrees = Vector3(-50, -20, 0)
	moon.light_color = Color(0.55, 0.72, 1.0)
	moon.light_energy = 0.75
	moon.shadow_enabled = false
	add_child(moon)
	_box(Vector3(0, -0.35, 0), Vector3(28, 0.7, 28), Color(0.16, 0.17, 0.2))
	_box(Vector3(0, 2.2, -14), Vector3(28, 4.4, 0.65), Color(0.19, 0.19, 0.23))
	_box(Vector3(0, 2.2, 14), Vector3(28, 4.4, 0.65), Color(0.19, 0.19, 0.23))
	_box(Vector3(-14, 2.2, 0), Vector3(0.65, 4.4, 28), Color(0.18, 0.18, 0.23))
	_box(Vector3(14, 2.2, 0), Vector3(0.65, 4.4, 28), Color(0.18, 0.18, 0.23))
	for i in range(5):
		var px := -10.5 + float(i) * 5.25
		_box(Vector3(px, 0.015, 0), Vector3(0.12, 0.025, 27), Color(0.24, 0.24, 0.27))
	for z in [-7.5, 7.5]:
		for x in [-7.5, 7.5]:
			_box(Vector3(x, 1.55, z), Vector3(1.05, 3.1, 1.05), Color(0.28, 0.27, 0.3))
	ambient_lamp = OmniLight3D.new()
	ambient_lamp.position = Vector3(0, 3.5, 0)
	ambient_lamp.omni_range = 17
	ambient_lamp.light_color = Color(1.0, 0.34, 0.15)
	ambient_lamp.light_energy = 0.52
	ambient_lamp.shadow_enabled = false
	add_child(ambient_lamp)

func _build_player() -> void:
	player = CharacterBody3D.new()
	player.name = "OriginalFPSPlayer"
	player.position = Vector3(0, 1.0, 5)
	var shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.36
	capsule.height = 1.8
	shape.shape = capsule
	player.add_child(shape)
	add_child(player)
	view = Camera3D.new()
	view.position = Vector3(0, 0.51, 0)
	view.fov = 75
	view.current = true
	player.add_child(view)
	gun = Node3D.new()
	view.add_child(gun)
	gun.position = Vector3(0.37, -0.35, -0.72)
	_gun_box(Vector3(0, 0, 0), Vector3(0.16, 0.18, 0.57), Color(0.13, 0.14, 0.17))
	_gun_box(Vector3(0, 0.08, -0.25), Vector3(0.10, 0.10, 0.32), Color(0.40, 0.40, 0.42))
	_gun_box(Vector3(0, -0.22, 0.12), Vector3(0.12, 0.28, 0.11), Color(0.28, 0.21, 0.16))
	_gun_box(Vector3(0, 0.17, -0.36), Vector3(0.025, 0.11, 0.025), Color(0.13, 0.13, 0.14))

func _gun_box(where: Vector3, dimensions: Vector3, tint: Color) -> void:
	var obj := MeshInstance3D.new()
	obj.position = where
	var mesh := BoxMesh.new()
	mesh.size = dimensions
	obj.mesh = mesh
	obj.material_override = _material(tint, 0.55)
	gun.add_child(obj)

func _make_label(message: String, font_size: int = 26) -> Label:
	var label := Label.new()
	label.text = message
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", Color(0.94, 0.95, 0.9))
	label.add_theme_color_override("font_shadow_color", Color(0, 0, 0))
	label.add_theme_constant_override("shadow_offset_x", 2)
	label.add_theme_constant_override("shadow_offset_y", 3)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(label)
	return label

func _button(caption: String, callback_down: Callable, callback_up: Callable) -> Button:
	var btn := Button.new()
	btn.text = caption
	btn.focus_mode = Control.FOCUS_NONE
	btn.add_theme_font_size_override("font_size", 23)
	btn.modulate.a = 0.83
	btn.button_down.connect(callback_down)
	btn.button_up.connect(callback_up)
	hud.add_child(btn)
	return btn

func _build_hud() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 2
	add_child(layer)
	hud = Control.new()
	hud.name = "TouchSafeHUD"
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(hud)
	status_label = _make_label("HP 100   SCORE 0")
	ammo_label = _make_label("24 / 144")
	wave_label = _make_label("ROUND 0")
	hint_label = _make_label("Offline / original Android prototype", 17)
	crosshair = _make_label("+", 34)
	joy_background = Panel.new()
	joy_background.modulate = Color(0.62, 0.72, 0.86, 0.34)
	joy_background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(joy_background)
	joy_dot = Panel.new()
	joy_dot.modulate = Color(0.84, 0.91, 1.0, 0.74)
	joy_dot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(joy_dot)
	fire_button = _button("FIRE", _fire_down, _fire_up)
	reload_button = _button("R", _reload_down, _nothing)
	ads_button = _button("ADS", _ads_down, _ads_up)
	sprint_button = _button("RUN", _sprint_down, _sprint_up)
	menu = Control.new()
	menu.mouse_filter = Control.MOUSE_FILTER_STOP
	hud.add_child(menu)
	var background := ColorRect.new()
	background.color = Color(0.01, 0.02, 0.035, 0.91)
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	menu.add_child(background)
	menu_title = Label.new()
	menu_title.text = "ZOMBIES-2026\nFIRST ANDROID APK\n\nORIGINAL GODOT PROTOTYPE\nNOT THE IW3 PORT"
	menu_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	menu_title.add_theme_font_size_override("font_size", 27)
	menu.add_child(menu_title)
	menu_button = Button.new()
	menu_button.text = "START SURVIVAL"
	menu_button.add_theme_font_size_override("font_size", 29)
	menu_button.pressed.connect(_start_pressed)
	menu.add_child(menu_button)

func _layout_hud() -> void:
	if hud == null:
		return
	var s := get_viewport().get_visible_rect().size
	hud.position = Vector2.ZERO
	hud.size = s
	status_label.position = Vector2(24, 14)
	ammo_label.position = Vector2(s.x - 215, 14)
	wave_label.position = Vector2(s.x * 0.48 - 60, 14)
	hint_label.position = Vector2(24, 54)
	crosshair.position = Vector2(s.x * 0.5 - 11, s.y * 0.5 - 28)
	var diameter := clampf(s.y * 0.28, 130, 210)
	var center := Vector2(diameter * 0.75, s.y - diameter * 0.75)
	joy_background.position = center - Vector2.ONE * diameter * 0.5
	joy_background.size = Vector2.ONE * diameter
	joy_dot.size = Vector2.ONE * (diameter * 0.29)
	_reposition_dot()
	var button_size := clampf(s.y * 0.21, 95, 158)
	fire_button.size = Vector2(button_size * 1.22, button_size)
	fire_button.position = Vector2(s.x - button_size * 1.45, s.y - button_size * 1.5)
	reload_button.size = Vector2(button_size * 0.7, button_size * 0.6)
	reload_button.position = Vector2(s.x - button_size * 2.3, s.y - button_size * 1.6)
	ads_button.size = Vector2(button_size, button_size * 0.64)
	ads_button.position = Vector2(s.x - button_size * 1.35, s.y - button_size * 2.4)
	sprint_button.size = Vector2(button_size * 0.95, button_size * 0.59)
	sprint_button.position = Vector2(s.x - button_size * 3.0, s.y - button_size * 0.78)
	menu.size = s
	menu.position = Vector2.ZERO
	(menu.get_child(0) as ColorRect).size = s
	menu_title.size = Vector2(s.x, s.y * 0.55)
	menu_title.position = Vector2(0, s.y * 0.11)
	menu_button.size = Vector2(minf(s.x * 0.55, 420), clampf(s.y * 0.15, 75, 110))
	menu_button.position = Vector2((s.x - menu_button.size.x) * 0.5, s.y * 0.7)

func _reposition_dot() -> void:
	if joy_dot == null:
		return
	var center := joy_background.position + joy_background.size * 0.5
	joy_dot.position = center + joystick * joy_background.size.x * 0.33 - joy_dot.size * 0.5

func _start_pressed() -> void:
	if dead:
		get_tree().reload_current_scene()
		return
	started = true
	menu.visible = false
	_start_round()

func _start_round() -> void:
	wave += 1
	remaining_to_spawn = mini(5 + wave * 2, 28)
	spawn_timer = 0.35
	round_wait = 0.0
	_update_labels()

func _process(delta: float) -> void:
	if not started or dead:
		return
	shot_cooldown = maxf(0.0, shot_cooldown - delta)
	if reload_timer > 0.0:
		reload_timer -= delta
		if reload_timer <= 0.0:
			var amount := mini(CLIP_SIZE - clip, reserve)
			clip += amount
			reserve -= amount
	if fire_held or Input.is_key_pressed(KEY_SPACE):
		_shoot()
	var target_gun_position := Vector3(0.0, -0.205, -0.57) if ads_held else Vector3(0.37, -0.35, -0.72)
	gun.position = gun.position.lerp(target_gun_position, minf(1.0, delta * 12.0))
	view.fov = lerpf(view.fov, 57.0 if ads_held else 75.0, minf(1.0, delta * 13.0))
	if shoot_flash > 0.0:
		shoot_flash -= delta
		crosshair.modulate = Color(1.0, 0.4, 0.3)
	else:
		crosshair.modulate = Color.WHITE
	if ambient_lamp != null:
		ambient_lamp.light_energy = 0.55 + sin(Time.get_ticks_msec() * 0.003) * 0.12
	if remaining_to_spawn > 0:
		spawn_timer -= delta
		if spawn_timer <= 0.0:
			_spawn_zombie()
			remaining_to_spawn -= 1
			spawn_timer = maxf(0.45, 1.7 - float(wave) * 0.07)
	elif get_tree().get_nodes_in_group("z2026_enemies").is_empty():
		round_wait += delta
		if round_wait > 2.3:
			_start_round()
	_update_labels()

func _physics_process(delta: float) -> void:
	if not started or dead:
		return
	var input_vector := joystick
	var keys := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if keys.length() > 0.1:
		input_vector = keys
	var forward := -player.global_transform.basis.z
	var right := player.global_transform.basis.x
	var desired := (right * input_vector.x - forward * input_vector.y)
	if desired.length() > 1.0:
		desired = desired.normalized()
	var speed := 7.2 if sprint_held or Input.is_key_pressed(KEY_SHIFT) else 4.65
	player.velocity.x = desired.x * speed
	player.velocity.z = desired.z * speed
	if not player.is_on_floor():
		player.velocity.y -= 24.0 * delta
	else:
		player.velocity.y = -0.1
	player.move_and_slide()

func _spawn_zombie() -> void:
	if get_tree().get_nodes_in_group("z2026_enemies").size() >= 15:
		return
	var theta := randf() * TAU
	var distance := randf_range(9.0, 11.8)
	var desired := player.position + Vector3(sin(theta) * distance, 0, cos(theta) * distance)
	desired.x = clampf(desired.x, -12.2, 12.2)
	desired.z = clampf(desired.z, -12.2, 12.2)
	desired.y = 1.0
	var zombie = CharacterBody3D.new()
	zombie.set_script(ZOMBIE_SCENE_SCRIPT)
	zombie.configure(player, wave)
	zombie.position = desired
	zombie.eliminated.connect(_enemy_killed)
	add_child(zombie)

func _shoot() -> void:
	if shot_cooldown > 0.0 or reload_timer > 0.0:
		return
	if clip == 0:
		_start_reload()
		return
	shot_cooldown = FIRE_INTERVAL
	clip -= 1
	shoot_flash = 0.09
	var from := view.global_position
	var to := from - view.global_transform.basis.z * 70.0
	var ray := PhysicsRayQueryParameters3D.create(from, to)
	ray.exclude = [player.get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(ray)
	if not hit.is_empty():
		var collider: Object = hit.get("collider")
		if collider != null and collider.has_method("take_damage"):
			collider.take_damage(35)
	_update_labels()

func _start_reload() -> void:
	if reload_timer <= 0.0 and clip < CLIP_SIZE and reserve > 0:
		reload_timer = RELOAD_SECONDS

func _enemy_killed(points: int) -> void:
	score += points
	_update_labels()

func receive_damage(amount: int) -> void:
	if dead:
		return
	player_health = maxi(0, player_health - amount)
	if player_health == 0:
		dead = true
		started = false
		menu_title.text = "GAME OVER\nROUND %d\nSCORE %d\n\nFIRST ANDROID PROTOTYPE" % [wave, score]
		menu_button.text = "RESTART"
		menu.visible = true
		_layout_hud()
	_update_labels()

func _update_labels() -> void:
	if status_label == null:
		return
	status_label.text = "HP %d   SCORE %d" % [player_health, score]
	ammo_label.text = "%d / %d%s" % [clip, reserve, "  RELOADING" if reload_timer > 0.0 else ""]
	wave_label.text = "ROUND %d" % wave

func _touch_on_button(point: Vector2) -> bool:
	if menu.visible:
		return true
	for btn in [fire_button, reload_button, ads_button, sprint_button]:
		if btn.get_global_rect().has_point(point):
			return true
	return false

func _input(event: InputEvent) -> void:
	if not started or dead:
		return
	if event is InputEventScreenTouch:
		if event.pressed:
			if _touch_on_button(event.position):
				return
			var width := get_viewport().get_visible_rect().size.x
			if event.position.x < width * 0.38 and left_touch == -1:
				left_touch = event.index
				_move_joystick(event.position)
			elif right_touch == -1:
				right_touch = event.index
		else:
			if event.index == left_touch:
				left_touch = -1
				joystick = Vector2.ZERO
				_reposition_dot()
			elif event.index == right_touch:
				right_touch = -1
	elif event is InputEventScreenDrag:
		if event.index == left_touch:
			_move_joystick(event.position)
		elif event.index == right_touch:
			_look(event.relative.x * 0.005, event.relative.y * 0.005)
	elif event is InputEventMouseMotion and not OS.has_feature("mobile"):
		if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
			_look(event.relative.x * 0.0026, event.relative.y * 0.0026)
	elif event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		elif event.keycode == KEY_R:
			_start_reload()
		elif event.keycode == KEY_F:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif event is InputEventMouseButton and not OS.has_feature("mobile"):
		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
				Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
			else:
				fire_held = event.pressed
		elif event.button_index == MOUSE_BUTTON_RIGHT:
			ads_held = event.pressed

func _move_joystick(point: Vector2) -> void:
	var center := joy_background.position + joy_background.size * 0.5
	var radius := joy_background.size.x * 0.37
	joystick = (point - center) / radius
	joystick = joystick.limit_length(1.0)
	if joystick.length() < 0.15:
		joystick = Vector2.ZERO
	_reposition_dot()

func _look(dx: float, dy: float) -> void:
	yaw -= dx
	pitch = clampf(pitch - dy, -1.25, 1.25)
	player.rotation.y = yaw
	view.rotation.x = pitch

func _fire_down() -> void:
	fire_held = true

func _fire_up() -> void:
	fire_held = false

func _reload_down() -> void:
	_start_reload()

func _ads_down() -> void:
	ads_held = true

func _ads_up() -> void:
	ads_held = false

func _sprint_down() -> void:
	sprint_held = true

func _sprint_up() -> void:
	sprint_held = false

func _nothing() -> void:
	pass
