"""Regression: Android Activity teardown must release the JNI-owned window.

This is a source-contract test, not proof of a playable IW3 Android APK.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ACTIVITY = ROOT / "android/iw3-native/android_app/app/src/main/java/org/z2026/iw3nativeprobe/MainActivity.java"
JNI = ROOT / "android/iw3-native/iw3_android_jni.cpp"


def test_activity_destroy_releases_native_window_even_without_surface_callback():
    source = ACTIVITY.read_text()
    destroy = re.search(r"@Override protected void onDestroy\(\) \{(.*?)\n    \}", source, re.S)
    assert destroy, "Activity onDestroy missing"
    body = destroy.group(1)
    assert "EngineBridge.nativeSurfaceDetach();" in body
    assert body.index("nativeSurfaceDetach()") < body.index("super.onDestroy()")


def test_native_surface_detach_is_idempotent():
    source = JNI.read_text()
    detach = re.search(
        r"Java_org_z2026_iw3nativeprobe_EngineBridge_nativeSurfaceDetach\("
        r".*?\n\}", source, re.S
    )
    assert detach, "JNI detach missing"
    body = detach.group(0)
    assert "std::lock_guard<std::mutex> lock(g_surface_mutex)" in body
    assert "if (g_surface_window)" in body
    assert "ANativeWindow_release(g_surface_window)" in body
    assert "g_surface_window = nullptr" in body
