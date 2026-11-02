extends SceneTree

# This exercises actual imported Godot AnimationPlayer evaluation at 0%, 50%,
# and 90% of idle/ADS/fire/reload. It reports numerical skeleton diagnostics.
# Not a visual or gameplay approval. No original game assets are distributed.

const GUNS := ["m4", "ak47", "mp5"]
const ACTIONS := ["idle", "ads", "fire", "reload"]
const TIMES := [0.0, 0.5, 0.9]

func _walk(node: Node, players: Array[AnimationPlayer], rigs: Array[Skeleton3D]) -> void:
    if node is AnimationPlayer:
        players.append(node as AnimationPlayer)
    if node is Skeleton3D:
        rigs.append(node as Skeleton3D)
    for child in node.get_children():
        _walk(child, players, rigs)

func _snapshot(rig: Skeleton3D) -> Dictionary:
    var sample := {}
    for i in range(rig.get_bone_count()):
        var name := rig.get_bone_name(i)
        var pose := rig.get_bone_global_pose(i)
        var p: Vector3 = pose.origin
        var basis: Basis = pose.basis
        if not p.is_finite() or not basis.x.is_finite() or not basis.y.is_finite() or not basis.z.is_finite():
            return {"error": "nonfinite skeleton transform", "bone": name}
        var rotation: Quaternion = basis.get_rotation_quaternion()
        sample[name] = {"p": [p.x, p.y, p.z], "q": [rotation.x, rotation.y, rotation.z, rotation.w]}
    return sample

func _measure(a: Dictionary, b: Dictionary) -> Dictionary:
    var max_shift: float = 0.0
    var total_shift: float = 0.0
    var max_rotation: float = 0.0
    var common: int = 0
    var moved: int = 0
    for name in a:
        if not b.has(name):
            continue
        var pa: Array = a[name]["p"]
        var pb: Array = b[name]["p"]
        var x := Vector3(float(pa[0]), float(pa[1]), float(pa[2]))
        var y := Vector3(float(pb[0]), float(pb[1]), float(pb[2]))
        var dist := x.distance_to(y)
        var qa: Array = a[name]["q"]
        var qb: Array = b[name]["q"]
        var q1 := Quaternion(float(qa[0]), float(qa[1]), float(qa[2]), float(qa[3]))
        var q2 := Quaternion(float(qb[0]), float(qb[1]), float(qb[2]), float(qb[3]))
        var cosine: float = clampf(absf(q1.dot(q2)), 0.0, 1.0)
        var angle: float = 2.0 * acos(cosine)
        common += 1
        total_shift += dist
        max_shift = maxf(max_shift, dist)
        max_rotation = maxf(max_rotation, angle)
        if dist > 0.001 or angle > 0.001:
            moved += 1
    return {"bones": common, "changed_bones": moved,
            "max_position_displacement": snappedf(max_shift, 0.00001),
            "total_position_displacement": snappedf(total_shift, 0.00001),
            "max_rotation_radians": snappedf(max_rotation, 0.00001)}

func _test_one(path: String) -> Dictionary:
    var scene: Resource = ResourceLoader.load(path)
    if not scene is PackedScene:
        return {"success": false, "error": "GLB did not become PackedScene"}
    var node: Node = (scene as PackedScene).instantiate()
    root.add_child(node)
    var players: Array[AnimationPlayer] = []
    var rigs: Array[Skeleton3D] = []
    _walk(node, players, rigs)
    if players.is_empty() or rigs.is_empty():
        node.queue_free()
        return {"success": false, "error": "AnimationPlayer or Skeleton3D missing",
                "players": players.size(), "rigs": rigs.size()}
    var player: AnimationPlayer = players[0]
    var rig: Skeleton3D = rigs[0]
    var bones: int = rig.get_bone_count()
    var output := {"success": true, "bone_count": bones, "actions": {}}
    var rest_snapshot: Dictionary = _snapshot(rig)
    if rest_snapshot.has("error"):
        node.queue_free()
        return {"success": false, "error": rest_snapshot}
    for action in ACTIONS:
        if not player.has_animation(action):
            output["success"] = false
            output["actions"][action] = {"error": "missing animation"}
            continue
        var clip: Animation = player.get_animation(action)
        var length: float = clip.length
        if length <= 0.0:
            output["success"] = false
            output["actions"][action] = {"error": "zero duration"}
            continue
        var samples := []
        for fraction in TIMES:
            player.stop()
            player.play(action)
            player.seek(length * fraction, true)
            player.advance(0.0)
            var pose := _snapshot(rig)
            if pose.has("error"):
                output["success"] = false
                samples.append({"fraction": fraction, "error": pose})
            else:
                samples.append({"fraction": fraction, "relative_to_import_rest": _measure(rest_snapshot, pose)})
        output["actions"][action] = {"duration_seconds": snappedf(length, 0.00001),
                                     "sampled": samples,
                                     "track_count": clip.get_track_count()}
    player.stop()
    node.free()
    return output

func _initialize() -> void:
    var output := {"engine": Engine.get_version_info().get("string", "unknown"),
                   "guns": {}, "all_actions_evaluated": true,
                   "poses_visually_approved": false, "fps_gameplay_approved": false}
    for gun in GUNS:
        output["guns"][gun] = {}
        for kind in ["weapon", "hands"]:
            var suffix: String = "_animated_experimental.glb" if kind == "weapon" else "_hands_animated_experimental.glb"
            var path := "res://weapons/" + gun + suffix
            var result := _test_one(path)
            output["guns"][gun][kind] = result
            if not result.get("success", false):
                output["all_actions_evaluated"] = false
    var target := FileAccess.open("res://godot-pose-gate.json", FileAccess.WRITE)
    if target == null:
        printerr("Pose gate JSON output could not be opened")
        quit(2)
        return
    target.store_string(JSON.stringify(output))
    target.close()
    print("IW3_GODOT_POSE_GATE: " + JSON.stringify({
        "all_actions_evaluated": output["all_actions_evaluated"],
        "engine": output["engine"],
        "gun_count": output["guns"].size(),
        "pose_visual_approval": false}))
    quit(0 if output["all_actions_evaluated"] else 1)
