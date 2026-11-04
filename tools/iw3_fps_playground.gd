extends Node3D

# Interactive IW3 -> Godot FPS test chamber, intended for Godot on desktop
# and Android. The arena is generated from Godot primitives and has no COD4
# artwork. Weapons are read from LOCALLY EXTRACTED GLBs only, never checked in.
# Touch: left thumb moves, right thumb looks; dedicated ADS/FIRE/RELOAD/JUMP/SWAP.
# Desktop testing: WASD, mouse, Shift, Space, R, F, C, Tab, Escape.
#
# This is an integration playground, NOT a finished zombies game.

const GunController = preload("res://fps_controller.gd")
const ARM_SCALE: float = 0.0254 # hypothesis IW3 inch -> Godot metre
# Actual Pixel Fold comparison (2026-11-02):
#   unrolled: weapons' mesh top points to 9 o'clock;
#   previous -90 deg: mesh top points to 6 o'clock (user screenshots);
#   corrected +90 deg: original mesh top (-Z, NOT +Z) maps to camera +Y.
# Rotate the WHOLE first-person rig, NOT the weapon alone, so tag_weapon and
# hands retain their original shared hierarchy. Android visual retest required.
# +90 is verified *visually* in private OpenGL frames: sight up, magazine down.
# Pixel Fold screenshots resembling -90 suggest wrong/stale APK. Show an
# unmistakable version/roll HUD + live touch adjustment to resolve this.
const DEFAULT_VIEWMODEL_ROLL_DEGREES: float = 90.0
const ORIENTATION_BUILD_ID: String = "IW3 V7 ORIGINAL GUNS / LIVE CALIBRATION"
const CAL_PATH: String = "user://iw3_private_viewmodel_v7.cfg"
const CAL_AXES: Array[String] = ["hip_x", "hip_y", "hip_depth", "ads_depth"]
# Observed authentic GLB sight depths were only 0.20-0.30 m at hip,
# while 4 AABB corners were inside/behind camera, per Pixel Fold audit.
# Recenter the actual optical tag at a safe hip-fire screen position.
const HIP_SIGHT_IN_CAMERA_METRES: Vector3 = Vector3(0.12, -0.12, -0.55)
const GUNS: Array[String] = ["m4", "ak47", "mp5"]
const MAG_CAPACITY: int = 30

var body: CharacterBody3D
var eyes: Node3D
var camera: Camera3D
var controller: Node3D
var canvas: CanvasLayer
var status_label: Label
var message_label: Label
var crosshair: Label
var move_pad: ColorRect
var touch_move_id: int = -1
var touch_look_id: int = -1
var touch_move_origin: Vector2
var touch_move_vector: Vector2 = Vector2.ZERO
var last_look_position: Vector2
var yaw_degrees: float = 0.0
var pitch_degrees: float = 0.0
var look_sensitivity: float = 0.14
var weapon_index: int = 0
var magazines: Dictionary = {}
var reserves: Dictionary = {}
var reload_pending: bool = false
var shots: int = 0
var impacts: int = 0
var distance_travelled: float = 0.0
var run_down: bool = false
var crouch_down: bool = false
var jump_pending: bool = false
var deadzone: float = 0.18
var button_instances: Dictionary = {}
var targets: Array[StaticBody3D] = []
var scene_ready: bool = false
var gun_ready: bool = false
var viewmodel_roll_degrees: float = DEFAULT_VIEWMODEL_ROLL_DEGREES
var orientation_controls: HBoxContainer
# Original Marine sleeves are a separate skinned MeshInstance3D surface.
# In our camera conversion they point into the FPS camera and block the
# sight/gun. Toggle their *visibility only*, keeping original gloves,
# original arms animations, weapon GLB, and tag_weapon skeleton intact.
var sleeves_hidden: bool = true
var sleeve_meshes: Array[MeshInstance3D] = []
var sleeve_toggle_button: Button
var calibration_profiles: Dictionary = {}
var calibration_axis_index: int = 0
var calibration_controls: HBoxContainer
var calibration_axis_button: Button

func _ready() -> void:
    for gun in GUNS:
        magazines[gun] = MAG_CAPACITY
        reserves[gun] = 90
    _build_arena()
    _build_player()
    _build_hud()
    equip(0)
    scene_ready = true
    Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func _create_box(parent: Node3D, name: String, center: Vector3, dimensions: Vector3, color: Color, collider: bool = true) -> StaticBody3D:
    var box: StaticBody3D = StaticBody3D.new()
    box.name = name
    box.position = center
    parent.add_child(box)
    var mesh: MeshInstance3D = MeshInstance3D.new()
    var cube: BoxMesh = BoxMesh.new()
    cube.size = dimensions
    mesh.mesh = cube
    var material: StandardMaterial3D = StandardMaterial3D.new()
    material.albedo_color = color
    mesh.material_override = material
    box.add_child(mesh)
    if collider:
        var collision: CollisionShape3D = CollisionShape3D.new()
        var shape: BoxShape3D = BoxShape3D.new()
        shape.size = dimensions
        collision.shape = shape
        box.add_child(collision)
    return box

func _build_arena() -> void:
    var environment: WorldEnvironment = WorldEnvironment.new()
    environment.environment = Environment.new()
    environment.environment.background_mode = Environment.BG_COLOR
    environment.environment.background_color = Color(0.06, 0.09, 0.14)
    environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.environment.ambient_light_color = Color(0.8, 0.84, 0.95)
    environment.environment.ambient_light_energy = 0.75
    add_child(environment)
    var sunlight: DirectionalLight3D = DirectionalLight3D.new()
    sunlight.name = "LaboratoryLight"
    sunlight.rotation_degrees = Vector3(-48, -40, 0)
    sunlight.light_energy = 1.7
    add_child(sunlight)
    _create_box(self, "Floor", Vector3(0, -0.25, 0), Vector3(30, 0.5, 30), Color(0.23, 0.25, 0.28))
    _create_box(self, "BackWall", Vector3(-14, 2.3, 0), Vector3(0.5, 4.6, 30), Color(0.24, 0.28, 0.35))
    _create_box(self, "FrontWall", Vector3(14, 2.3, 0), Vector3(0.5, 4.6, 30), Color(0.19, 0.24, 0.31))
    _create_box(self, "LeftWall", Vector3(0, 2.3, -14), Vector3(30, 4.6, 0.5), Color(0.23, 0.24, 0.32))
    _create_box(self, "RightWall", Vector3(0, 2.3, 14), Vector3(30, 4.6, 0.5), Color(0.21, 0.26, 0.35))
    for i in range(3):
        var target: StaticBody3D = _create_box(self, "Target_%d" % i,
            Vector3(8 + float(i) * 1.7, 1.55, -2.5 + float(i) * 2.5),
            Vector3(0.32, 1.35, 0.75), Color(0.28, 0.7, 0.49))
        target.set_meta("hit_points", 20)
        targets.append(target)

func _build_player() -> void:
    body = CharacterBody3D.new()
    body.name = "Player"
    body.position = Vector3(0, 0.12, 0)
    add_child(body)
    var shape_node: CollisionShape3D = CollisionShape3D.new()
    var shape: CapsuleShape3D = CapsuleShape3D.new()
    shape.radius = 0.32
    shape.height = 1.7
    shape_node.shape = shape
    shape_node.position = Vector3(0, 0.86, 0)
    body.add_child(shape_node)
    eyes = Node3D.new()
    eyes.name = "Eyes"
    eyes.position = Vector3(0, 1.54, 0)
    body.add_child(eyes)
    camera = Camera3D.new()
    camera.name = "PlayerCamera"
    camera.fov = 80.0
    camera.near = 0.01
    camera.far = 75.0
    eyes.add_child(camera)
    camera.current = true
    # Original IW3 viewmodels are X-forward. Camera looks forward +X
    # but viewmodel is rotated Y=+90 degrees to face Godot camera -Z.
    camera.rotation.y = -PI / 2.0

func _label(txt: String, x: float, y: float, w: float, h: float) -> Label:
    var label: Label = Label.new()
    label.text = txt
    label.position = Vector2(x, y)
    label.size = Vector2(w, h)
    label.mouse_filter = Control.MOUSE_FILTER_IGNORE
    canvas.add_child(label)
    return label

func _button(name: String, right: float, bottom: float, width: float, height: float) -> Button:
    var button: Button = Button.new()
    button.name = name
    button.text = name
    button.anchor_left = 1.0
    button.anchor_right = 1.0
    button.anchor_top = 1.0
    button.anchor_bottom = 1.0
    button.offset_left = -right - width
    button.offset_right = -right
    button.offset_top = -bottom - height
    button.offset_bottom = -bottom
    button.focus_mode = Control.FOCUS_NONE
    button.custom_minimum_size = Vector2(width, height)
    button_instances[name] = button
    return button

func _build_hud() -> void:
    canvas = CanvasLayer.new()
    canvas.name = "TouchHUD"
    add_child(canvas)
    var layout: Control = Control.new()
    layout.name = "Layout"
    layout.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    layout.mouse_filter = Control.MOUSE_FILTER_IGNORE
    canvas.add_child(layout)
    # Top status is always readable regardless of orientation.
    status_label = Label.new()
    status_label.name = "Status"
    status_label.position = Vector2(20, 14)
    status_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
    layout.add_child(status_label)
    message_label = Label.new()
    message_label.position = Vector2(20, 43)
    message_label.text = "IW3 → GODOT | FPS LAB / LOCAL PRIVATE ASSETS"
    message_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
    layout.add_child(message_label)
    crosshair = Label.new()
    crosshair.text = "+"
    crosshair.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    crosshair.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    crosshair.anchor_left = 0.5
    crosshair.anchor_right = 0.5
    crosshair.anchor_top = 0.5
    crosshair.anchor_bottom = 0.5
    crosshair.offset_left = -15
    crosshair.offset_right = 15
    crosshair.offset_top = -20
    crosshair.offset_bottom = 20
    crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
    layout.add_child(crosshair)
    move_pad = ColorRect.new()
    move_pad.name = "MoveArea"
    move_pad.color = Color(0.25, 0.35, 0.43, 0.28)
    move_pad.anchor_top = 1.0
    move_pad.anchor_bottom = 1.0
    move_pad.offset_left = 30
    move_pad.offset_right = 210
    move_pad.offset_top = -215
    move_pad.offset_bottom = -35
    move_pad.mouse_filter = Control.MOUSE_FILTER_IGNORE
    layout.add_child(move_pad)
    var move_title: Label = Label.new()
    move_title.text = "MOVE"
    move_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    move_title.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    move_title.mouse_filter = Control.MOUSE_FILTER_IGNORE
    move_pad.add_child(move_title)

    for spec in [
        ["FIRE", 20.0, 105.0, 96.0, 90.0],
        ["ADS", 130.0, 110.0, 83.0, 72.0],
        ["RELOAD", 20.0, 15.0, 90.0, 66.0],
        ["JUMP", 226.0, 22.0, 82.0, 70.0],
        ["SWAP", 335.0, 18.0, 80.0, 60.0],
        ["SPRINT", 325.0, 95.0, 80.0, 64.0],
        ["CROUCH", 224.0, 108.0, 80.0, 64.0]
    ]:
        var button: Button = _button(spec[0], spec[1], spec[2], spec[3], spec[4])
        layout.add_child(button)
    button_instances["FIRE"].pressed.connect(fire)
    button_instances["ADS"].pressed.connect(toggle_ads)
    button_instances["RELOAD"].pressed.connect(reload)
    button_instances["JUMP"].pressed.connect(jump)
    button_instances["SWAP"].pressed.connect(next_weapon)
    button_instances["SPRINT"].button_down.connect(func() -> void: run_down = true)
    button_instances["SPRINT"].button_up.connect(func() -> void: run_down = false)
    button_instances["CROUCH"].pressed.connect(func() -> void: crouch_down = not crouch_down)
    # Dedicated build-identifiable, Android-touch live roll calibration.
    # Allows verifying the *real rendered weapon* without uploading another
    # ~36 MB APK for each 90-degree sign hypothesis.
    orientation_controls = HBoxContainer.new()
    orientation_controls.name = "IW3_V4_Live_Roll_Touch"
    orientation_controls.anchor_left = 1.0
    orientation_controls.anchor_right = 1.0
    orientation_controls.offset_left = -410
    orientation_controls.offset_right = -12
    orientation_controls.offset_top = 12
    orientation_controls.offset_bottom = 68
    layout.add_child(orientation_controls)
    var rotate_left: Button = Button.new()
    rotate_left.text = "ROLL -90"
    rotate_left.custom_minimum_size = Vector2(128, 55)
    rotate_left.focus_mode = Control.FOCUS_NONE
    orientation_controls.add_child(rotate_left)
    rotate_left.pressed.connect(func() -> void: shift_viewmodel_roll(-90.0))
    var rotate_right: Button = Button.new()
    rotate_right.text = "ROLL +90"
    rotate_right.custom_minimum_size = Vector2(128, 55)
    rotate_right.focus_mode = Control.FOCUS_NONE
    orientation_controls.add_child(rotate_right)
    rotate_right.pressed.connect(func() -> void: shift_viewmodel_roll(90.0))
    sleeve_toggle_button = Button.new()
    sleeve_toggle_button.text = "SLEEVES ON"
    sleeve_toggle_button.name = "ToggleOriginalSleeveGeometry"
    sleeve_toggle_button.custom_minimum_size = Vector2(130, 55)
    sleeve_toggle_button.focus_mode = Control.FOCUS_NONE
    orientation_controls.add_child(sleeve_toggle_button)
    sleeve_toggle_button.pressed.connect(toggle_original_sleeves)
    # Touch-friendly second toolbar: original mesh placement in the same APK.
    calibration_controls = HBoxContainer.new()
    calibration_controls.name = "IW3_V7_Gun_Camera_Calibration"
    calibration_controls.anchor_left = 1.0
    calibration_controls.anchor_right = 1.0
    calibration_controls.offset_left = -410
    calibration_controls.offset_right = -12
    calibration_controls.offset_top = 74
    calibration_controls.offset_bottom = 127
    layout.add_child(calibration_controls)
    calibration_axis_button = Button.new()
    calibration_axis_button.name = "SelectCalibrationAxis"
    calibration_axis_button.custom_minimum_size = Vector2(122, 48)
    calibration_axis_button.focus_mode = Control.FOCUS_NONE
    calibration_controls.add_child(calibration_axis_button)
    calibration_axis_button.pressed.connect(cycle_calibration_axis)
    var decrease: Button = Button.new()
    decrease.text = "-"
    decrease.custom_minimum_size = Vector2(54, 48)
    decrease.focus_mode = Control.FOCUS_NONE
    calibration_controls.add_child(decrease)
    decrease.pressed.connect(func() -> void: adjust_current_calibration(-1.0))
    var increase: Button = Button.new()
    increase.text = "+"
    increase.custom_minimum_size = Vector2(54, 48)
    increase.focus_mode = Control.FOCUS_NONE
    calibration_controls.add_child(increase)
    increase.pressed.connect(func() -> void: adjust_current_calibration(1.0))
    var save_button: Button = Button.new()
    save_button.text = "SAVE"
    save_button.custom_minimum_size = Vector2(70, 48)
    save_button.focus_mode = Control.FOCUS_NONE
    calibration_controls.add_child(save_button)
    save_button.pressed.connect(func() -> void: save_camera_calibration())
    var reset_button: Button = Button.new()
    reset_button.text = "RESET"
    reset_button.custom_minimum_size = Vector2(70, 48)
    reset_button.focus_mode = Control.FOCUS_NONE
    calibration_controls.add_child(reset_button)
    reset_button.pressed.connect(func() -> void: reset_current_calibration())
    _refresh_calibration_button()
    _refresh_status()

func _input(event: InputEvent) -> void:
    if event is InputEventKey and event.pressed and not event.echo:
        match event.keycode:
            KEY_F:
                fire()
            KEY_R:
                reload()
            KEY_TAB:
                next_weapon()
            KEY_C:
                crouch_down = not crouch_down
            KEY_G:
                Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
            KEY_ESCAPE:
                Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
    if event is InputEventMouseButton and event.pressed:
        if event.button_index == MOUSE_BUTTON_LEFT and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
            fire()
        if event.button_index == MOUSE_BUTTON_RIGHT:
            toggle_ads()
    if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
        look_by(event.relative)

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        var position: Vector2 = event.position
        if event.pressed:
            if position.x < get_viewport().get_visible_rect().size.x * 0.42 and touch_move_id == -1:
                touch_move_id = event.index
                touch_move_origin = position
                touch_move_vector = Vector2.ZERO
            elif touch_look_id == -1:
                touch_look_id = event.index
                last_look_position = position
        else:
            if event.index == touch_move_id:
                touch_move_id = -1
                touch_move_vector = Vector2.ZERO
            if event.index == touch_look_id:
                touch_look_id = -1
    if event is InputEventScreenDrag:
        if event.index == touch_move_id:
            touch_move_vector = ((event.position - touch_move_origin) / 85.0).limit_length(1.0)
            if touch_move_vector.length() < deadzone:
                touch_move_vector = Vector2.ZERO
        elif event.index == touch_look_id:
            look_by(event.position - last_look_position)
            last_look_position = event.position

func look_by(relative: Vector2) -> void:
    yaw_degrees -= relative.x * look_sensitivity
    pitch_degrees = clampf(pitch_degrees - relative.y * look_sensitivity, -82.0, 82.0)
    if is_instance_valid(body) and is_instance_valid(camera):
        body.rotation.y = deg_to_rad(yaw_degrees)
        camera.rotation.x = deg_to_rad(pitch_degrees)

func _keyboard_move() -> Vector2:
    var direction: Vector2 = Vector2.ZERO
    if Input.is_key_pressed(KEY_W):
        direction.y -= 1.0
    if Input.is_key_pressed(KEY_S):
        direction.y += 1.0
    if Input.is_key_pressed(KEY_A):
        direction.x -= 1.0
    if Input.is_key_pressed(KEY_D):
        direction.x += 1.0
    return direction.normalized()

func _physics_process(delta: float) -> void:
    if not scene_ready:
        return
    var axis: Vector2 = touch_move_vector if touch_move_id >= 0 else _keyboard_move()
    var camera_basis: Basis = camera.global_transform.basis
    var desired: Vector3 = camera_basis.x * axis.x + camera_basis.z * axis.y
    desired.y = 0.0
    desired = desired.normalized() if desired.length() > 0.01 else Vector3.ZERO
    var running: bool = run_down or Input.is_key_pressed(KEY_SHIFT)
    var speed: float = 7.0 if running else 4.1
    if crouch_down or Input.is_key_pressed(KEY_CTRL):
        speed = 2.25
    var before: Vector3 = body.global_position
    body.velocity.x = desired.x * speed
    body.velocity.z = desired.z * speed
    if body.is_on_floor():
        if jump_pending or Input.is_key_pressed(KEY_SPACE):
            body.velocity.y = 5.3
        else:
            body.velocity.y = -0.3
    else:
        body.velocity.y -= 15.0 * delta
    jump_pending = false
    body.move_and_slide()
    distance_travelled += before.distance_to(body.global_position)

func _process(delta: float) -> void:
    if not scene_ready:
        return
    if gun_ready and is_instance_valid(controller):
        controller.tick(delta)
        if reload_pending and controller.state != controller.State.RELOAD:
            _finish_reload()
    if is_instance_valid(crosshair) and is_instance_valid(controller):
        crosshair.visible = not gun_ready or controller.ads_blend < 0.9
    _refresh_status()

func equip(index: int) -> bool:
    if not is_instance_valid(camera):
        return false
    if is_instance_valid(controller):
        controller.queue_free()
        controller = null
    weapon_index = posmod(index, GUNS.size())
    var name: String = GUNS[weapon_index]
    reload_pending = false
    gun_ready = false
    var gun_file: String = "res://weapons/" + name + "_animated_experimental.glb"
    var hands_file: String = "res://weapons/" + name + "_hands_animated_experimental.glb"
    var gun_scene: Resource = load(gun_file)
    var hand_scene: Resource = load(hands_file)
    if not (gun_scene is PackedScene) or not (hand_scene is PackedScene):
        if is_instance_valid(message_label):
            message_label.text = "NO LOCAL GLB: " + name + " (requires private extraction)"
        return false
    controller = GunController.new()
    controller.name = name + "_FPS"
    # All three real GLB guns + original hands are rotated together.
    # Default +90 is a tested hypothesis, with direct V4 touch controls to
    # verify actual visual output on hardware. Do not infer it from a basis
    # vector alone; see the private original-mesh capture CI.
    camera.add_child(controller)
    controller.set_process(false)
    if not controller.configure(camera, hand_scene as PackedScene, gun_scene as PackedScene):
        controller.queue_free()
        controller = null
        return false
    # Hide ONLY the malformed camera-facing Marine cloth surface, not the
    # gloves or weapons. Tests confirm the actual imported GLBs have two
    # distinct materials: 'mtl_marine_glove' and 'mtl_marine_glovesleeve'.
    _index_original_sleeve_meshes()
    _set_original_sleeves_visible(not sleeves_hidden)
    controller.mount.ads_target_camera_depth_metres = float(_calibration_for(name)["ads_depth"])
    # Derive original eye/tag_camera offset from exported skeleton, instead of
    # manually positioning the gun on screen for each model.
    var bone_idx: int = controller.mount.hands_skeleton.find_bone("tag_camera")
    if bone_idx < 0:
        controller.queue_free()
        controller = null
        return false
    if not _apply_viewmodel_roll_and_center(viewmodel_roll_degrees):
        controller.queue_free()
        controller = null
        return false
    gun_ready = true
    _refresh_calibration_button()
    message_label.text = ORIENTATION_BUILD_ID + " | " + name.to_upper() + " | " + str(viewmodel_roll_degrees) + " deg"
    return true

func _index_original_sleeve_meshes() -> void:
    sleeve_meshes.clear()
    if not is_instance_valid(controller) or not is_instance_valid(controller.mount):
        return
    var rig: Node3D = controller.mount
    var pending: Array[Node] = [rig.hands_root]
    while not pending.is_empty():
        var node: Node = pending.pop_back()
        # Weapon GLB is parented under the hand skeleton's tag_weapon. Do
        # not alter or hide ANY of the actual gun submeshes.
        if node == rig.weapon_root:
            continue
        for child in node.get_children():
            pending.append(child)
        if not node is MeshInstance3D:
            continue
        var mesh_instance: MeshInstance3D = node as MeshInstance3D
        if mesh_instance.mesh == null:
            continue
        var has_cloth_surface: bool = false
        for i in range(mesh_instance.mesh.get_surface_count()):
            var material: Material = mesh_instance.get_active_material(i)
            if material != null and material.resource_name.contains("mtl_marine_glovesleeve"):
                has_cloth_surface = true
        if has_cloth_surface:
            sleeve_meshes.append(mesh_instance)

func _set_original_sleeves_visible(should_show: bool) -> void:
    for sleeve in sleeve_meshes:
        if is_instance_valid(sleeve):
            sleeve.visible = should_show
    if is_instance_valid(sleeve_toggle_button):
        sleeve_toggle_button.text = "SLEEVES OFF" if should_show else "SLEEVES ON"

func toggle_original_sleeves() -> void:
    sleeves_hidden = not sleeves_hidden
    _set_original_sleeves_visible(not sleeves_hidden)
    if is_instance_valid(message_label):
        message_label.text = ORIENTATION_BUILD_ID + " | " + (
            "SLEEVES HIDDEN" if sleeves_hidden else "ORIGINAL SLEEVES VISIBLE")

# Camera-space parameters are scoped per real weapon and stored ONLY on device.
# No copyrighted model, texture, skeleton or screen capture goes into ConfigFile.
func _calibration_for(name: String) -> Dictionary:
    if calibration_profiles.has(name):
        return calibration_profiles[name]
    var values: Dictionary = {"hip_x": 0.12, "hip_y": -0.12, "hip_depth": 0.55, "ads_depth": 0.60}
    var disk: ConfigFile = ConfigFile.new()
    if disk.load(CAL_PATH) == OK:
        for axis in CAL_AXES:
            var candidate: Variant = disk.get_value(name, axis, values[axis])
            if candidate is float or candidate is int:
                var amount: float = float(candidate)
                if is_finite(amount):
                    var bounds: Vector2 = _calibration_limits(axis)
                    values[axis] = clampf(amount, bounds.x, bounds.y)
    calibration_profiles[name] = values
    return values

func _calibration_limits(axis: String) -> Vector2:
    match axis:
        "hip_x": return Vector2(-0.30, 0.35)
        "hip_y": return Vector2(-0.32, 0.20)
        "hip_depth": return Vector2(0.35, 1.10)
        "ads_depth": return Vector2(0.35, 1.20)
    return Vector2(0.0, 0.0)

func current_hip_camera_target() -> Vector3:
    var data: Dictionary = _calibration_for(GUNS[weapon_index])
    return Vector3(float(data["hip_x"]), float(data["hip_y"]), -float(data["hip_depth"]))

func _refresh_calibration_button() -> void:
    if not is_instance_valid(calibration_axis_button):
        return
    var axis: String = CAL_AXES[calibration_axis_index]
    var amount: float = float(_calibration_for(GUNS[weapon_index])[axis])
    calibration_axis_button.text = axis.to_upper().replace("_", " ") + " %.3f" % amount

func cycle_calibration_axis() -> void:
    calibration_axis_index = (calibration_axis_index + 1) % CAL_AXES.size()
    _refresh_calibration_button()

func adjust_current_calibration(direction: float) -> bool:
    if not gun_ready or not is_finite(direction) or is_zero_approx(direction):
        return false
    var axis: String = CAL_AXES[calibration_axis_index]
    var data: Dictionary = _calibration_for(GUNS[weapon_index])
    var previous: float = float(data[axis])
    var step_size: float = 0.025 if axis == "hip_x" or axis == "hip_y" else 0.05
    var bounds: Vector2 = _calibration_limits(axis)
    var value: float = snappedf(clampf(previous + signf(direction) * step_size, bounds.x, bounds.y), 0.001)
    if is_equal_approx(previous, value):
        return false
    data[axis] = value
    var success: bool = true
    if axis == "ads_depth":
        controller.mount.ads_target_camera_depth_metres = value
        success = controller.tick(0.0).get("ok", false)
    else:
        success = _apply_viewmodel_roll_and_center(viewmodel_roll_degrees)
    if not success:
        data[axis] = previous
        controller.mount.ads_target_camera_depth_metres = float(data["ads_depth"])
        _apply_viewmodel_roll_and_center(viewmodel_roll_degrees)
        return false
    _refresh_calibration_button()
    message_label.text = ORIENTATION_BUILD_ID + " | " + axis.to_upper() + " %.3f" % value + " UNSAVED"
    return true

func reset_current_calibration() -> bool:
    if not gun_ready:
        return false
    calibration_profiles[GUNS[weapon_index]] = {"hip_x": 0.12, "hip_y": -0.12, "hip_depth": 0.55, "ads_depth": 0.60}
    controller.mount.ads_target_camera_depth_metres = 0.60
    var succeeded: bool = _apply_viewmodel_roll_and_center(viewmodel_roll_degrees)
    _refresh_calibration_button()
    message_label.text = ORIENTATION_BUILD_ID + " | DEFAULTS RESTORED (UNSAVED)"
    return succeeded

func save_camera_calibration() -> bool:
    if not gun_ready:
        return false
    var data: ConfigFile = ConfigFile.new()
    for gun in GUNS:
        var profile: Dictionary = _calibration_for(gun)
        for axis in CAL_AXES:
            data.set_value(gun, axis, profile[axis])
    var saved: bool = data.save(CAL_PATH) == OK
    message_label.text = ORIENTATION_BUILD_ID + (" | SAVED LOCALLY" if saved else " | SAVE FAILED")
    return saved

func _apply_viewmodel_roll_and_center(roll_degrees: float) -> bool:
    if not is_instance_valid(controller) or not is_instance_valid(camera):
        return false
    var rig: Node3D = controller.mount
    if not is_instance_valid(rig):
        return false
    var prior_ads_wanted: bool = controller.ads_wanted
    var prior_ads_blend: float = controller.ads_blend
    controller.reset_viewmodel()
    rig.position = Vector3.ZERO
    rig.initial_local_position = Vector3.ZERO
    var source_to_camera: Basis = Basis(Vector3.UP,PI/2.0) * \
        Basis(Vector3.RIGHT,deg_to_rad(roll_degrees))
    controller.transform = Transform3D(source_to_camera.scaled(
        Vector3.ONE * ARM_SCALE),Vector3.ZERO)
    if not rig.set_timed_action("idle",0.0):
        return false
    var index: int = rig.hands_skeleton.find_bone("tag_camera")
    if index < 0:
        return false
    rig.hands_skeleton.force_update_all_bone_transforms()
    var eye_global: Vector3 = (rig.hands_skeleton.global_transform *
        rig.hands_skeleton.get_bone_global_pose(index)).origin
    var eye_local: Vector3 = rig.to_local(eye_global)
    rig.position -= eye_local
    # SOURCE tag_camera is only a rig landmark, not a guarantee the optics,
    # weapon stock or animated arms stay in front of Godot's near plane.
    # After authentic tag_camera alignment, position the ORIGINAL sight tag
    # at the chosen HIP screen position and safe 55cm depth. This is one
    # geometry-derived calibration shared by all weapons; no fake meshes or
    # per-gun guessed XYZ are introduced. Keep tag_weapon hierarchy intact.
    var sight_info: Dictionary = rig.aim_tag_info()
    var sight_bone: String = sight_info.get("name", "")
    var sight_idx: int = rig.weapon_skeleton.find_bone(sight_bone)
    if sight_idx < 0:
        return false
    rig.weapon_skeleton.force_update_all_bone_transforms()
    var sight_world: Vector3 = (rig.weapon_skeleton.global_transform *
        rig.weapon_skeleton.get_bone_global_pose(sight_idx)).origin
    var sight_space: Vector3 = camera.to_local(sight_world)
    if not sight_space.is_finite():
        return false
    var camera_displacement: Vector3 = current_hip_camera_target() - sight_space
    if not camera_displacement.is_finite() or camera_displacement.length() > 5.0:
        return false
    rig.global_position += camera.global_transform.basis.orthonormalized() * camera_displacement
    rig.initial_local_position = rig.position
    # Keep current ADS when changing a calibration slider or roll mid-aim.
    controller.ads_wanted = prior_ads_wanted
    controller.ads_blend = prior_ads_blend
    if not controller.tick(0.0).get("ok", false):
        return false
    viewmodel_roll_degrees = wrapf(roll_degrees,-180.0,180.0)
    return true

func shift_viewmodel_roll(delta_degrees: float) -> bool:
    if not gun_ready:
        return false
    var result: bool = _apply_viewmodel_roll_and_center(
        viewmodel_roll_degrees + delta_degrees)
    if result:
        message_label.text = ORIENTATION_BUILD_ID + " | " + \
            GUNS[weapon_index].to_upper() + " | " + str(viewmodel_roll_degrees) + " deg"
        _refresh_status()
    return result

func next_weapon() -> bool:
    return equip(weapon_index + 1)

func toggle_ads() -> bool:
    return gun_ready and controller.toggle_ads()

func jump() -> void:
    jump_pending = true

func fire() -> bool:
    if not gun_ready or int(magazines[GUNS[weapon_index]]) <= 0:
        return false
    if not controller.press_fire():
        return false
    reload_pending = false
    magazines[GUNS[weapon_index]] -= 1
    shots += 1
    _trace_hit()
    return true

func _trace_hit() -> void:
    var origin: Vector3 = camera.global_position
    var forward: Vector3 = -camera.global_transform.basis.z
    var ray: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(origin, origin + forward * 50.0)
    ray.exclude = [body.get_rid()]
    var collision: Dictionary = get_world_3d().direct_space_state.intersect_ray(ray)
    if not collision.is_empty() and collision.get("collider") in targets:
        var target: StaticBody3D = collision["collider"]
        target.set_meta("hit_points", int(target.get_meta("hit_points", 0)) - 1)
        impacts += 1

func reload() -> bool:
    if not gun_ready:
        return false
    var name: String = GUNS[weapon_index]
    if int(magazines[name]) >= MAG_CAPACITY or int(reserves[name]) <= 0:
        return false
    if not controller.start_reload():
        return false
    reload_pending = true
    return true

func _finish_reload() -> void:
    if not reload_pending:
        return
    reload_pending = false
    var name: String = GUNS[weapon_index]
    var needed: int = MAG_CAPACITY - int(magazines[name])
    var amount: int = mini(needed, int(reserves[name]))
    magazines[name] = int(magazines[name]) + amount
    reserves[name] = int(reserves[name]) - amount

func set_ads_hold(enabled: bool) -> void:
    if gun_ready:
        controller.ads_hold_mode = enabled

func _refresh_status() -> void:
    if status_label == null:
        return
    var gun: String = GUNS[weapon_index].to_upper()
    var state: String = "NO ASSETS"
    if gun_ready and is_instance_valid(controller):
        state = controller.status()["state"] + "  ADS " + str(snappedf(controller.ads_blend * 100.0, 1.0)) + "%"
    status_label.text = gun + "  " + str(magazines[GUNS[weapon_index]]) + "/" + str(reserves[GUNS[weapon_index]]) + " | " + state + " | Hits " + str(impacts) + " | V7 ROLL " + str(viewmodel_roll_degrees)

func metrics() -> Dictionary:
    return {"scene_ready": scene_ready, "gun_ready": gun_ready, "weapon": GUNS[weapon_index],
        "magazine": int(magazines[GUNS[weapon_index]]), "reserve": int(reserves[GUNS[weapon_index]]),
        "shots": shots, "hits": impacts,
        "distance_travelled": snappedf(distance_travelled, 0.00001),
        "yaw": yaw_degrees, "pitch": pitch_degrees, "joystick_vector": [touch_move_vector.x, touch_move_vector.y],
        "touch_controls": button_instances.size(),
        "reload_pending": reload_pending,
        "weapon_status": controller.status() if gun_ready else {},
        "viewmodel_roll_degrees": viewmodel_roll_degrees,
        "orientation_build_id": ORIENTATION_BUILD_ID,
        "hip_sight_target_camera_m": [current_hip_camera_target().x, current_hip_camera_target().y, current_hip_camera_target().z],
        "ads_target_depth_m": float(_calibration_for(GUNS[weapon_index])["ads_depth"]),
        "calibration_controls_available": calibration_controls != null,
        "live_roll_calibration_buttons": orientation_controls != null,
        "sleeve_meshes_identified": sleeve_meshes.size(),
        "original_sleeves_hidden": sleeves_hidden}
