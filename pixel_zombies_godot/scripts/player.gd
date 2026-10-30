extends CharacterBody3D

signal died

const MOVE_SPEED := 4.5
const SPRINT_SPEED := 7.0
const JUMP_SPEED := 5.6
const LOOK_SPEED := 0.0026
const MAG_CAPACITY := 32
const SHOT_PERIOD := 0.13

var health := 100
var ammo := MAG_CAPACITY
var reserve_ammo := 192
var trigger_held := false
var aiming := false
var sprint_touch := false
var jump_touch := false
var touch_movement := Vector2.ZERO
var _stick_pointer := -1
var _look_pointer := -1
var _stick_origin := Vector2.ZERO
var _pitch := 0.0
var _shot_timer := 0.0
var _reload_timer := 0.0
var _flash_timer := 0.0
var _recoil := 0.0
var camera: Camera3D
var gun: Node3D
var flash: MeshInstance3D

func _ready() -> void:
    var shape := CapsuleShape3D.new()
    shape.height = 1.7
    shape.radius = 0.34
    var col := CollisionShape3D.new()
    col.position.y = 0.86
    col.shape = shape
    add_child(col)
    camera = Camera3D.new()
    camera.position.y = 1.50
    camera.current = true
    camera.fov = 74.0
    add_child(camera)
    _make_placeholder_weapon()
    if not DisplayServer.is_touchscreen_available():
        Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _physics_process(delta: float) -> void:
    if health <= 0:
        return
    var move_axes := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    if touch_movement.length_squared() > 0.01:
        move_axes = touch_movement
    var direction := (basis * Vector3(move_axes.x, 0, move_axes.y)).normalized()
    var sprinting: bool = Input.is_action_pressed("sprint") or sprint_touch
    var speed := SPRINT_SPEED if sprinting and not aiming else MOVE_SPEED
    velocity.x = direction.x * speed
    velocity.z = direction.z * speed
    if not is_on_floor():
        velocity.y -= 19.0 * delta
    elif Input.is_action_just_pressed("jump") or jump_touch:
        velocity.y = JUMP_SPEED
    jump_touch = false
    move_and_slide()

func _process(delta: float) -> void:
    if health <= 0:
        return
    _shot_timer = maxf(0.0, _shot_timer - delta)
    _flash_timer = maxf(0.0, _flash_timer - delta)
    _recoil = move_toward(_recoil, 0.0, delta * 5.0)
    flash.visible = _flash_timer > 0.0
    if _reload_timer > 0.0:
        _reload_timer -= delta
        if _reload_timer <= 0.0:
            var loaded: int = mini(MAG_CAPACITY - ammo, reserve_ammo)
            ammo += loaded
            reserve_ammo -= loaded
    if trigger_held and _shot_timer <= 0.0:
        _shoot()
    var target_x := 0.26 if aiming else 0.34
    var target_y := -0.16 if aiming else -0.27
    if _reload_timer > 0.0:
        target_y -= 0.18 * sin(PI * (2.1 - _reload_timer) / 2.1)
    gun.position.x = lerpf(gun.position.x, target_x, minf(1.0, delta * 11.0))
    gun.position.y = lerpf(gun.position.y, target_y - _recoil * 0.06, minf(1.0, delta * 11.0))
    gun.rotation.y = lerpf(gun.rotation.y, 0.10 if aiming else -0.10, minf(1.0, delta * 11.0))
    camera.fov = lerpf(camera.fov, 59.0 if aiming else 74.0, minf(1.0, delta * 9.0))

func _shoot() -> void:
    if _reload_timer > 0.0:
        if ammo > 0:
            _reload_timer = 0.0
        else:
            return
    if ammo <= 0:
        reload()
        _shot_timer = 0.25
        return
    ammo -= 1
    _shot_timer = SHOT_PERIOD
    _flash_timer = 0.045
    _recoil = minf(1.0, _recoil + 0.65)
    var origin := camera.global_position
    var end := origin - camera.global_transform.basis.z * 45.0
    var ray := PhysicsRayQueryParameters3D.create(origin, end)
    ray.exclude = [get_rid()]
    var hit := get_world_3d().direct_space_state.intersect_ray(ray)
    if hit.has("collider"):
        var collider: Object = hit["collider"]
        if collider.has_method("take_damage"):
            collider.call("take_damage", 50)

func reload() -> void:
    if _reload_timer > 0.0 or ammo >= MAG_CAPACITY or reserve_ammo <= 0:
        return
    _reload_timer = 2.1

func toggle_ads() -> void:
    if health > 0:
        aiming = not aiming

func take_damage(amount: int) -> void:
    if health <= 0:
        return
    health = maxi(0, health - amount)
    if health == 0:
        trigger_held = false
        died.emit()

func is_reloading() -> bool:
    return _reload_timer > 0.0

func _input(event: InputEvent) -> void:
    if health <= 0:
        return
    if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
        _look(event.relative)
    elif event is InputEventMouseButton and not DisplayServer.is_touchscreen_available():
        if event.button_index == MOUSE_BUTTON_LEFT:
            trigger_held = event.pressed
        elif event.button_index == MOUSE_BUTTON_RIGHT and event.pressed:
            toggle_ads()
    elif event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
        if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
            Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
        else:
            Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
    elif event is InputEventScreenTouch:
        var screen := get_viewport().get_visible_rect().size
        if event.pressed:
            if event.position.x < screen.x * 0.38 and event.position.y > screen.y * 0.43:
                _stick_pointer = event.index
                _stick_origin = event.position
                touch_movement = Vector2.ZERO
            elif event.position.y < screen.y * 0.68 or event.position.x < screen.x * 0.70:
                _look_pointer = event.index
        else:
            if event.index == _stick_pointer:
                _stick_pointer = -1
                touch_movement = Vector2.ZERO
            if event.index == _look_pointer:
                _look_pointer = -1
    elif event is InputEventScreenDrag:
        if event.index == _stick_pointer:
            touch_movement = ((event.position - _stick_origin) / 52.0).limit_length()
        elif event.index == _look_pointer:
            _look(event.relative * 1.6)

func _look(relative: Vector2) -> void:
    rotation.y -= relative.x * LOOK_SPEED
    _pitch = clampf(_pitch - relative.y * LOOK_SPEED, -1.25, 1.25)
    camera.rotation.x = _pitch

# Lightweight stand-in: the actual licensed/original MP40 model can replace this node later.
# Hipfire front post is near screen center, with receiver extending lower/right.
func _make_placeholder_weapon() -> void:
    gun = Node3D.new()
    gun.name = "MP40_Placeholder"
    gun.position = Vector3(0.34, -0.27, -0.60)
    camera.add_child(gun)
    var steel := Color(0.25, 0.28, 0.30)
    var dark := Color(0.10, 0.11, 0.12)
    _weapon_box(Vector3(0.0, 0, 0.0), Vector3(0.18, 0.13, 0.36), steel)
    _weapon_box(Vector3(-0.04, -0.21, -0.02), Vector3(0.08, 0.37, 0.10), dark)
    _weapon_box(Vector3(0.025, -0.18, 0.12), Vector3(0.11, 0.27, 0.10), dark)
    _weapon_barrel(Vector3(-0.02, 0.015, -0.13), Vector3(-0.28, 0.04, -0.75), 0.027, steel)
    _weapon_box(Vector3(-0.28, 0.11, -0.75), Vector3(0.03, 0.11, 0.025), steel)
    _weapon_box(Vector3(-0.005, 0.11, 0.02), Vector3(0.10, 0.07, 0.025), steel)
    flash = MeshInstance3D.new()
    var flash_mesh := SphereMesh.new()
    flash_mesh.radius = 0.08
    flash_mesh.height = 0.13
    flash.mesh = flash_mesh
    var flash_mat := StandardMaterial3D.new()
    flash_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    flash_mat.albedo_color = Color(1.0, 0.63, 0.12)
    flash.material_override = flash_mat
    flash.position = Vector3(-0.28, 0.04, -0.80)
    flash.visible = false
    gun.add_child(flash)

func _weapon_box(at: Vector3, dimensions: Vector3, tint: Color) -> void:
    var piece := MeshInstance3D.new()
    var geometry := BoxMesh.new()
    geometry.size = dimensions
    piece.mesh = geometry
    var material := StandardMaterial3D.new()
    material.albedo_color = tint
    material.metallic = 0.5
    material.roughness = 0.6
    piece.material_override = material
    piece.position = at
    gun.add_child(piece)

func _weapon_barrel(start: Vector3, finish: Vector3, radius: float, tint: Color) -> void:
    var piece := MeshInstance3D.new()
    var geometry := CylinderMesh.new()
    geometry.top_radius = radius
    geometry.bottom_radius = radius
    geometry.height = start.distance_to(finish)
    piece.mesh = geometry
    var material := StandardMaterial3D.new()
    material.albedo_color = tint
    material.roughness = 0.5
    piece.material_override = material
    piece.position = (start + finish) * 0.5
    piece.quaternion = Quaternion(Vector3.UP, (finish - start).normalized())
    gun.add_child(piece)
