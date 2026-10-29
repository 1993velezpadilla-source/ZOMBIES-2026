"""Regression test for the JNI boundary's sparse Android touch-pointer IDs."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class JniSparsePointerIdTests(unittest.TestCase):
    def test_jni_snapshot_uses_android_pointer_id_domain_not_touch_slot_count(self):
        jni = (ROOT / "android/iw3-native/iw3_android_jni.cpp").read_text(encoding="utf-8")
        platform = (ROOT / "android/iw3-native/iw3_android_platform.cpp").read_text(encoding="utf-8")
        activity = (ROOT / "android/iw3-native/android_app/app/src/main/java/org/z2026/iw3nativeprobe/MainActivity.java").read_text(encoding="utf-8")

        self.assertRegex(jni, r"constexpr\s+int\s+kAndroidPointerIdCount\s*=\s*32\s*;")
        snapshot = jni.split("Java_org_z2026_iw3nativeprobe_EngineBridge_nativeTouchSnapshot(", 1)[1]
        snapshot = snapshot.split("Java_org_z2026_iw3nativeprobe_EngineBridge_nativeTouchReset(", 1)[0]
        self.assertIn("id >= kAndroidPointerIdCount", snapshot)
        self.assertNotRegex(snapshot, r"id\s*>=\s*10\b")

        self.assertIn("constexpr int kAndroidPointerIdCount = 32;", platform)
        self.assertIn("MAX_ANDROID_POINTER_ID_COUNT = 32", activity)
        native_test = (ROOT / "android/iw3-native/platform_native_test.cpp").read_text(encoding="utf-8")
        self.assertIn("z2026_platform_touch_snapshot(31, &x, &y)", native_test)

    def test_jni_touch_event_and_snapshot_share_the_same_valid_id_range(self):
        jni = (ROOT / "android/iw3-native/iw3_android_jni.cpp").read_text(encoding="utf-8")
        self.assertIn("z2026_platform_touch_event(static_cast<int>(id)", jni)
        self.assertIn("id >= kAndroidPointerIdCount", jni)
        self.assertNotIn("id >= 10", jni)


if __name__ == "__main__":
    unittest.main()
