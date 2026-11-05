extends SceneTree

# CLI --script must inherit from SceneTree/MainLoop (not EditorScript).
# Runs under --headless --editor; editor settings get persisted on exit.
func _configure() -> void:
    var java_path: String = OS.get_environment("JAVA_HOME")
    var android_path: String = OS.get_environment("ANDROID_HOME")
    if java_path.is_empty() or android_path.is_empty():
        printerr("Missing JAVA_HOME or ANDROID_HOME")
        quit(2)
        return
    var settings: EditorSettings = EditorInterface.get_editor_settings()
    if settings == null:
        printerr("EditorSettings unavailable: pass --editor")
        quit(3)
        return
    settings.set_setting("export/android/java_sdk_path",java_path)
    settings.set_setting("export/android/android_sdk_path",android_path)
    var configured: bool = settings.get_setting("export/android/java_sdk_path") == java_path and \
        settings.get_setting("export/android/android_sdk_path") == android_path
    print("IW3_ANDROID_SDK_SETTINGS: configured=" + str(configured))
    await process_frame
    quit(0 if configured else 4)

func _initialize() -> void:
    call_deferred("_configure")
