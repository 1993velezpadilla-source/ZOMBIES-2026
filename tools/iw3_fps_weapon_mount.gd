extends Node3D
class_name IW3FpsWeaponMount

# Reusable Godot 4 first-person prototype mount.
# Loads locally extracted first-person viewhands and weapon PackedScenes.
# Synchronizes original idle/ads/fire/reload AnimationPlayers.
# BoneAttachment3D follows the tag_weapon bone; no guessed XYZ offsets.
#
# CAUTION: Bone registration != visual alignment/animation correctness.
# Do not use original COD4 assets in a public build without permission.

var hands_root: Node3D
var weapon_root: Node3D
var hands_skeleton: Skeleton3D
var weapon_skeleton: Skeleton3D
var mount: BoneAttachment3D
var hands_player: AnimationPlayer
var weapon_player: AnimationPlayer
var configured: bool = false

func _find_skeleton(node: Node) -> Skeleton3D:
    if node is Skeleton3D:
        return node as Skeleton3D
    for child in node.get_children():
        var found: Skeleton3D = _find_skeleton(child)
        if found != null:
            return found
    return null

func _find_player(node: Node) -> AnimationPlayer:
    if node is AnimationPlayer:
        return node as AnimationPlayer
    for child in node.get_children():
        var found: AnimationPlayer = _find_player(child)
        if found != null:
            return found
    return null

func configure(hands_scene: PackedScene, weapon_scene: PackedScene) -> bool:
    if configured or hands_scene == null or weapon_scene == null:
        push_error("IW3FpsWeaponMount already configured or scene missing.")
        return false
    hands_root = hands_scene.instantiate() as Node3D
    weapon_root = weapon_scene.instantiate() as Node3D
    if hands_root == null or weapon_root == null:
        push_error("Expected two imported 3D GLB PackedScenes.")
        return false
    add_child(hands_root)
    hands_skeleton = _find_skeleton(hands_root)
    weapon_skeleton = _find_skeleton(weapon_root)
    hands_player = _find_player(hands_root)
    weapon_player = _find_player(weapon_root)
    if hands_skeleton == null or weapon_skeleton == null or hands_player == null or weapon_player == null:
        push_error("IW3 viewhands or weapon skeleton / AnimationPlayer missing.")
        return false
    if hands_skeleton.find_bone("tag_weapon") < 0:
        push_error("Original IW3 hand rig has no tag_weapon.")
        return false
    mount = BoneAttachment3D.new()
    mount.name = "IW3_tag_weapon_mount"
    hands_skeleton.add_child(mount)
    mount.bone_name = "tag_weapon"
    mount.override_pose = false
    mount.add_child(weapon_root)
    weapon_root.transform = Transform3D.IDENTITY
    configured = mount.bone_idx >= 0
    if not configured:
        push_error("BoneAttachment3D could not attach tag_weapon.")
    return configured

func play_action(action: String) -> bool:
    if not configured:
        return false
    if not hands_player.has_animation(action) or not weapon_player.has_animation(action):
        return false
    hands_player.stop()
    weapon_player.stop()
    hands_player.play(action)
    weapon_player.play(action)
    # Both clips start at the same local time.
    hands_player.seek(0.0, true)
    weapon_player.seek(0.0, true)
    return true

func seek_action(action: String, seconds: float) -> bool:
    if not play_action(action):
        return false
    # The hand XANIM is authoritative for the full action duration.
    # A weapon GLB can have only a one-frame static clip for ADS/fire; clamping
    # BOTH players to that shortest duration would incorrectly freeze hands.
    var hand_time: float = clampf(seconds, 0.0, hands_player.get_animation(action).length)
    var weapon_time: float = clampf(seconds, 0.0, weapon_player.get_animation(action).length)
    hands_player.seek(hand_time, true)
    weapon_player.seek(weapon_time, true)
    hands_player.advance(0.0)
    weapon_player.advance(0.0)
    hands_skeleton.force_update_all_bone_transforms()
    weapon_skeleton.force_update_all_bone_transforms()
    mount.on_skeleton_update()
    return true

func tag_weapon_transform() -> Transform3D:
    if not configured:
        return Transform3D.IDENTITY
    var index: int = hands_skeleton.find_bone("tag_weapon")
    return hands_skeleton.global_transform * hands_skeleton.get_bone_global_pose(index)

func anchor_error() -> Dictionary:
    if not configured:
        return {"error": "unconfigured mount"}
    hands_skeleton.force_update_all_bone_transforms()
    mount.on_skeleton_update()
    var expected: Transform3D = tag_weapon_transform()
    var mounted: Transform3D = mount.global_transform
    var dp: float = expected.origin.distance_to(mounted.origin)
    var dq: float = clampf(absf(expected.basis.get_rotation_quaternion().dot(
        mounted.basis.get_rotation_quaternion())), 0.0, 1.0)
    return {
        "mount_bone": mount.bone_name,
        "bone_valid": mount.bone_idx >= 0,
        "weapon_parent_is_attachment": weapon_root.get_parent() == mount,
        "anchor_position_error": snappedf(dp, 0.000001),
        "anchor_rotation_error_radians": snappedf(2.0 * acos(dq), 0.000001),
        "weapon_pivot_error": snappedf(weapon_root.global_position.distance_to(mounted.origin), 0.000001),
        "tag_camera_present": hands_skeleton.find_bone("tag_camera") >= 0
    }

func diagnostic_camera_to_weapon_distance() -> float:
    # Not an ADS approval: diagnostic only for scale/position calibration.
    var camera_bone: int = hands_skeleton.find_bone("tag_camera")
    if not configured or camera_bone < 0:
        return -1.0
    var camera_pose: Transform3D = hands_skeleton.global_transform * hands_skeleton.get_bone_global_pose(camera_bone)
    return camera_pose.origin.distance_to(weapon_root.global_position)
