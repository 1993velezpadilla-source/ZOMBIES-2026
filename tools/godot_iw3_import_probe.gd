extends SceneTree

# Actual Godot 4.6.3 headless import of temporary, locally derived
# COD4 weapon animation GLBs. No game asset is committed or uploaded.

func _collect_animations(node: Node, results: Dictionary) -> void:
    if node is AnimationPlayer:
        var player: AnimationPlayer = node
        for name in player.get_animation_list():
            var animation: Animation = player.get_animation(name)
            results[str(name)] = animation.get_track_count() if animation != null else 0
    for child in node.get_children():
        _collect_animations(child, results)


func _initialize() -> void:
    var summary: Dictionary = {"engine": Engine.get_version_info().get("string", "unknown"), "guns": {}, "all_imported": false}
    var fatal: bool = false
    for gun in ["m4", "ak47", "mp5"]:
        var gun_results: Dictionary = {}
        for kind in ["weapon", "hands"]:
            var suffix: String = "_animated_experimental.glb" if kind == "weapon" else "_hands_animated_experimental.glb"
            var path: String = "res://weapons/" + gun + suffix
            var scene: Resource = ResourceLoader.load(path)
            if not (scene is PackedScene):
                gun_results[kind] = {"imported": false, "reason": "no PackedScene from GLB"}
                fatal = true
                continue
            var instance: Node = (scene as PackedScene).instantiate()
            var names: Dictionary = {}
            _collect_animations(instance, names)
            var ok: bool = true
            for expected_name in ["idle", "ads", "fire", "reload"]:
                if not names.has(expected_name) or int(names[expected_name]) < 1:
                    ok = false
            gun_results[kind] = {"imported": true, "animation_names": names, "four_named_actions": ok}
            if not ok:
                fatal = true
            instance.free()
        summary["guns"][gun] = gun_results
    summary["all_imported"] = not fatal
    summary["rendered_pose_verified"] = false
    summary["gameplay_verified"] = false
    summary["note"] = "GLB import and animation track presence only. Skeleton retargeting and pose playback not visual tested."
    var outfile: FileAccess = FileAccess.open("res://godot-import-gate.json", FileAccess.WRITE)
    if outfile == null:
        printerr("Failed to create Godot import metadata")
        quit(2)
        return
    outfile.store_string(JSON.stringify(summary))
    outfile.close()
    print("IW3_GODOT_IMPORT_GATE: " + JSON.stringify(summary))
    quit(1 if fatal else 0)
