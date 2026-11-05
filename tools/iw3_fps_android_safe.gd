extends "res://playground.gd"

# PUBLIC / DISTRIBUTABLE TEST BUILD: independently created procedural boxes.
# NO COD4 XMODEL, XANIM, IWI, DDS, GLB or weapon textures are referenced.
# Shares the actual touch, movement, camera, combat targets and arena code
# used by our PRIVATE IW3 lab; only its visual weapon backend is replaced.
#
# Users must NOT confuse this APK with the original IW3 arsenal integration.

const GUN_NAMES: Array[String] = ["M4 SHAPE", "AK47 SHAPE", "MP5 SHAPE"]
const STYLES: Array[Color] = [
    Color(0.24, 0.29, 0.35),
    Color(0.37, 0.30, 0.19),
    Color(0.16, 0.20, 0.23)
]

var demo_rig: Node3D
var demo_ads_wanted: bool = false
var demo_ads_blend: float = 0.0
var demo_shot_time: float = 0.0
var demo_reload_time: float = 0.0
var demo_is_reloading: bool = false
var demo_fire_total: int = 0
var demo_reload_cancel_count: int = 0
var demo_geometry_count: int = 0
var demo_flash: MeshInstance3D
var demo_frame_count: int = 0

func _ready() -> void:
    super._ready()
    if is_instance_valid(message_label):
        message_label.text = "ZOMBIES FPS LAB | SAFE SHAPES | NO COD4 ASSETS"

func _color_material(color: Color) -> Material:
    var mat: StandardMaterial3D = StandardMaterial3D.new()
    mat.albedo_color = color
    mat.metallic = 0.25
    mat.roughness = 0.72
    return mat

func _shape(parent: Node3D, label: String, size: Vector3, position: Vector3,
        color: Color) -> MeshInstance3D:
    var part: MeshInstance3D = MeshInstance3D.new()
    part.name = label
    var box: BoxMesh = BoxMesh.new()
    box.size = size
    part.mesh = box
    part.position = position
    part.material_override = _color_material(color)
    parent.add_child(part)
    demo_geometry_count += 1
    return part

func _build_demo_gun() -> void:
    if is_instance_valid(demo_rig):
        demo_rig.queue_free()
    demo_rig = Node3D.new()
    demo_rig.name = "IndependentlyCreatedPrimitiveWeapon_NoCOD4"
    demo_rig.position = Vector3(0.24, -0.25, -0.65)
    camera.add_child(demo_rig)
    var shade: Color = STYLES[weapon_index]
    _shape(demo_rig, "Original_TestReceiver", Vector3(0.15, 0.14, 0.44),
        Vector3(0, 0, -0.07), shade)
    _shape(demo_rig, "Original_TestBarrel", Vector3(0.058, 0.07, 0.42),
        Vector3(0, 0.04, -0.47), Color(0.13,0.14,0.15))
    _shape(demo_rig, "RearSight", Vector3(0.09, 0.06, 0.035),
        Vector3(0, 0.115, 0.05), Color(0.1,0.11,0.12))
    _shape(demo_rig, "FrontSight", Vector3(0.045, 0.075, 0.04),
        Vector3(0, 0.11, -0.64), Color(0.1,0.11,0.12))
    _shape(demo_rig, "IndependentMagazine", Vector3(0.1, 0.26, 0.14),
        Vector3(0, -0.20, -0.03), Color(0.17,0.17,0.19))
    _shape(demo_rig, "Hand_Left_Placeholder", Vector3(0.16, 0.13, 0.27),
        Vector3(-0.17,-0.12,-0.30), Color(0.46, 0.34, 0.43))
    _shape(demo_rig, "Hand_Right_Placeholder", Vector3(0.16, 0.16, 0.25),
        Vector3(0.15,-0.13,0.08), Color(0.46, 0.34, 0.43))
    demo_flash = _shape(demo_rig, "TestMuzzleFlash", Vector3(0.10, 0.10, 0.15),
        Vector3(0, 0.04, -0.73), Color(1.0,0.73,0.21))
    demo_flash.visible = false

func equip(index: int) -> bool:
    if not is_instance_valid(camera):
        return false
    weapon_index = posmod(index, GUNS.size())
    reload_pending = false
    demo_is_reloading = false
    demo_reload_time = 0.0
    demo_ads_wanted = false
    demo_ads_blend = 0.0
    demo_shot_time = 0.0
    gun_ready = true
    _build_demo_gun()
    if is_instance_valid(message_label):
        message_label.text = "SAFE TEST SHAPES: " + GUN_NAMES[weapon_index]
    return true

func toggle_ads() -> bool:
    if not gun_ready or demo_is_reloading:
        return false
    demo_ads_wanted = not demo_ads_wanted
    return true

func fire() -> bool:
    if not gun_ready:
        return false
    var name: String = GUNS[weapon_index]
    if int(magazines[name]) <= 0:
        return false
    if demo_is_reloading:
        demo_is_reloading = false
        reload_pending = false
        demo_reload_cancel_count += 1
    magazines[name] = int(magazines[name]) - 1
    shots += 1
    demo_fire_total += 1
    demo_shot_time = 0.13
    _trace_hit()
    return true

func reload() -> bool:
    if not gun_ready or demo_is_reloading:
        return false
    var name: String = GUNS[weapon_index]
    if int(magazines[name]) >= MAG_CAPACITY or int(reserves[name]) <= 0:
        return false
    demo_is_reloading = true
    reload_pending = true
    demo_reload_time = 0.0
    demo_ads_wanted = false
    return true

func _process(delta: float) -> void:
    if not scene_ready or not is_instance_valid(demo_rig):
        return
    demo_frame_count += 1
    var dt: float = clampf(delta, 0.0, 0.05)
    demo_ads_blend = move_toward(demo_ads_blend, 1.0 if demo_ads_wanted else 0.0, dt / 0.18)
    demo_shot_time = maxf(0.0,demo_shot_time - dt)
    if demo_is_reloading:
        demo_reload_time += dt
        if demo_reload_time >= 1.1:
            demo_is_reloading = false
            _finish_reload()
    demo_flash.visible = demo_shot_time > 0.075
    # Numeric first-person placeholder transition; not original IW3 offsets.
    var alpha: float = demo_ads_blend
    demo_rig.position = Vector3(lerpf(0.24,0.0,alpha),
        lerpf(-0.25,-0.145,alpha),
        lerpf(-0.65,-0.54,alpha))
    demo_rig.rotation.x = (-0.82 * minf(demo_reload_time / 1.1,1.0)) if demo_is_reloading else         (0.04 if demo_shot_time > 0.0 else 0.0)
    if is_instance_valid(crosshair):
        crosshair.visible = demo_ads_blend < 0.95
    _refresh_status()

func _refresh_status() -> void:
    if not is_instance_valid(status_label):
        return
    var name: String = GUNS[weapon_index]
    var action: String = "RELOAD" if demo_is_reloading else ("ADS" if demo_ads_blend > 0.95 else "HIP")
    status_label.text = GUN_NAMES[weapon_index] + "  " +         str(magazines[name]) + "/" + str(reserves[name]) +         " | " + action + " | HITS " + str(impacts)

func set_ads_hold(enabled: bool) -> void:
    # UI/inputs may choose hold mode in a later update. This demo uses toggle.
    pass

func metrics() -> Dictionary:
    var name: String = GUNS[weapon_index]
    return {"scene_ready": scene_ready, "gun_ready": gun_ready, "safe_primitives": true,
        "weapon": name, "magazine": int(magazines[name]),
        "reserve": int(reserves[name]), "shots": shots,
        "hits": impacts, "reload_pending": reload_pending,
        "ads_blend": demo_ads_blend, "reload_cancel_count": demo_reload_cancel_count,
        "primitive_parts": demo_geometry_count, "frames": demo_frame_count,
        "distance_travelled": snappedf(distance_travelled,0.00001),
        "touch_controls": button_instances.size(),
        "original_cod4_assets": false, "android_hardware_tested": false}
