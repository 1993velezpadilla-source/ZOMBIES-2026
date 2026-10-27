"""Regression tests for the Android implementation of the original dvar sleep service."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AndroidDvarSleepPortTests(unittest.TestCase):
    def test_adapter_maps_zero_sleep_to_yield_and_positive_delay_to_nanosleep(self):
        adapter = (ROOT / "android/iw3-native/iw3_android_dvar_io.cpp").read_text(encoding="utf-8")
        self.assertIn("void NET_Sleep(int msec)", adapter)
        self.assertIn("sched_yield()", adapter)
        self.assertIn("nanosleep(&remaining, &remaining)", adapter)
        self.assertIn("errno != EINTR", adapter)
        self.assertNotIn("Sleep(msec);", adapter)

    def test_win32_reference_semantics_are_not_modified(self):
        original = (ROOT / "third_party/KisakCOD/src/win32/win_net.cpp").read_text(encoding="utf-8")
        self.assertIn("void NET_Sleep( int msec )", original)
        self.assertIn("Sleep(msec);", original)

    def test_real_dvar_translation_unit_and_service_are_archived_together(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn('"${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_dvar_io.cpp"', cmake)
        self.assertIn("add_library(iw3_sp_dvar_android STATIC $<TARGET_OBJECTS:iw3_sp_full_dvar>)", cmake)
        self.assertIn("iw3_android_dvar_net_sleep_semantics", cmake)
        self.assertIn("dvar_sleep_native_test.cpp", cmake)

    def test_arm64_ci_requires_a_relocatable_link_to_resolve_net_sleep(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("libiw3_sp_dvar_android.a", workflow)
        self.assertIn("-m aarch64linux -r --whole-archive", workflow)
        self.assertIn("Android NET_Sleep provider failed to resolve", workflow)
        self.assertIn("IW3_ORIGINAL_DVAR_ANDROID_SLEEP_SERVICE_RESOLVED_REMAINING_ENGINE_SERVICES_VISIBLE", workflow)


if __name__ == "__main__":
    unittest.main()
