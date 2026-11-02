extends Node3D
class_name IW3FpsWeaponController

# Touch-ready first-person weapon state machine for locally generated COD4
# GLB weapon + viewhands scenes. It is intentionally independent of any UI:
# Android virtual buttons call toggle_ads(), set_ads_held(), press_fire(),
# start_reload(), and cancel_reload(). There is no hardcoded gun XYZ.
#
# Camera stays fixed while the gun rig is moved via original sight tags.
# Status is a prototype; render, IRONSIGHT ALIGNMENT and distribution are
# NOT approved without manual visual inspection and licensed replacements.

const Mount = preload("res://weapon_mount.gd")

enum State { IDLE, FIRE, RELOAD }

@export var ads_hold_mode: bool = false
@export_range(0.05, 1.0, 0.01) var ads_transition_seconds: float = 0.18

var mount: Node3D
var view_camera: Camera3D
var configured: bool = false
var ads_wanted: bool = false
var ads_blend: float = 0.0
var state: State = State.IDLE
var action_elapsed: float = 0.0
var action_count_fire: int = 0
var action_count_reload: int = 0
var fire_during_reload_cancels: int = 0
var failed_alignment_frames: int = 0
var last_alignment: Dictionary = {}

func configure(camera: Camera3D, hands: PackedScene, weapon: PackedScene) -> bool:
    if configured or camera == null or hands == null or weapon == null:
        return false
    mount = Mount.new()
    mount.name = "IW3_WeaponMount"
    add_child(mount)
    if not mount.configure(hands, weapon):
        mount.queue_free()
        mount = null
        return false
    view_camera = camera
    configured = true
    ads_wanted = false
    ads_blend = 0.0
    state = State.IDLE
    action_elapsed = 0.0
    return true

func toggle_ads() -> bool:
    if not configured or ads_hold_mode or state == State.RELOAD:
        return false
    ads_wanted = not ads_wanted
    return true

func set_ads_held(down: bool) -> bool:
    if not configured or not ads_hold_mode or state == State.RELOAD:
        return false
    ads_wanted = down
    return true

func start_reload() -> bool:
    if not configured or state == State.RELOAD:
        return false
    if not mount.hands_player.has_animation("reload"):
        return false
    state = State.RELOAD
    action_elapsed = 0.0
    ads_wanted = false
    action_count_reload += 1
    return true

func cancel_reload() -> bool:
    if state != State.RELOAD:
        return false
    state = State.IDLE
    action_elapsed = 0.0
    return true

func press_fire() -> bool:
    if not configured:
        return false
    if state == State.RELOAD:
        cancel_reload()
        fire_during_reload_cancels += 1
    if state == State.FIRE:
        # Automatic weapons can queue repeated shots in a higher-level rate-
        # of-fire system; this method guarantees one shot per completed cycle.
        return false
    state = State.FIRE
    action_elapsed = 0.0
    action_count_fire += 1
    return true

func action_duration(name: String) -> float:
    if not configured or not mount.hands_player.has_animation(name):
        return 0.0
    return mount.hands_player.get_animation(name).length

func _process(delta: float) -> void:
    tick(delta)

# Public deterministic step() for Android/Linux automated tests.
func tick(delta: float) -> Dictionary:
    if not configured or not is_finite(delta) or delta < 0.0:
        return {"ok": false, "error": "not configured or invalid delta"}
    # Don't allow one backgrounded-phone frame to skip full reload cycles.
    var dt: float = minf(delta, 0.05)
    var target: float = 1.0 if ads_wanted and state != State.RELOAD else 0.0
    var step_amount: float = dt / maxf(0.001, ads_transition_seconds)
    ads_blend = move_toward(ads_blend, target, step_amount)

    var action: String = "idle"
    var timestamp: float = 0.0
    if state == State.FIRE:
        action = "fire"
        action_elapsed += dt
        timestamp = action_elapsed
        if action_elapsed >= action_duration("fire"):
            state = State.IDLE
            action_elapsed = 0.0
    elif state == State.RELOAD:
        action = "reload"
        action_elapsed += dt
        timestamp = action_elapsed
        if action_elapsed >= action_duration("reload"):
            state = State.IDLE
            action_elapsed = 0.0
    elif ads_blend > 0.00001:
        action = "ads"
        timestamp = action_duration(action) * ads_blend

    if not mount.set_timed_action(action, timestamp):
        return {"ok": false, "error": "cannot scrub action", "action": action}

    # No procedural ADS adjustment during reload. Otherwise it drags the
    # hands toward the reticle while the magazine is in motion.
    var correction: float = ads_blend if state != State.RELOAD and action != "reload" else 0.0
    if correction > 0.0:
        last_alignment = mount.apply_procedural_ads_alignment(view_camera, correction)
        if not last_alignment.get("success", false):
            failed_alignment_frames += 1
    else:
        mount.reset_procedural_ads()
        last_alignment = {"success": true, "blend": 0.0, "translation_m": 0.0}
    return {"ok": true, "action": action, "state": State.keys()[state],
        "elapsed": snappedf(timestamp, 0.00001),
        "ads_blend": snappedf(ads_blend, 0.00001),
        "ads_wanted": ads_wanted, "aligned": last_alignment.get("success", false)}

func status() -> Dictionary:
    return {"configured": configured, "state": State.keys()[state],
        "ads_blend": ads_blend, "ads_wanted": ads_wanted,
        "fire_count": action_count_fire, "reload_count": action_count_reload,
        "cancelled_reload_to_fire": fire_during_reload_cancels,
        "failed_alignment_frames": failed_alignment_frames}

func reset_viewmodel() -> void:
    ads_wanted = false
    ads_blend = 0.0
    action_elapsed = 0.0
    state = State.IDLE
    if configured:
        mount.reset_procedural_ads()
        mount.set_timed_action("idle", 0.0)
