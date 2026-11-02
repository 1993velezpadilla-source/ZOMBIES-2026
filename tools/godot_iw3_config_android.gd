@tool
extends EditorScript

# Only executed inside Godot editor CI. SDK paths come from environment,
# never hardcoded to an individual user's computer.
func _run() -> void:
    var java_path: String = OS.get_environment("JAVA_HOME")
    var android_path: String = OS.get_environment("ANDROID_HOME")
    if java_path.is_empty() or android_path.is_empty():
        push_error("Set JAVA_HOME and ANDROID_HOME for debug Android export")
        return
    var settings: EditorSettings = EditorInterface.get_editor_settings()
    settings.set_setting("export/android/java_sdk_path", java_path)
    settings.set_setting("export/android/android_sdk_path", android_path)
    print("IW3_ANDROID_SDK_SETTINGS: configured=" + str(
        settings.get_setting("export/android/java_sdk_path") == java_path and
        settings.get_setting("export/android/android_sdk_path") == android_path))
