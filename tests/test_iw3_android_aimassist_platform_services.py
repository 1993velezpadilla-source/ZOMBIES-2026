"""Guard the authentic Android client/aim-assist platform service edges."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AndroidAimAssistPlatformServiceTests(unittest.TestCase):
    def test_android_assert_provider_is_fatal_and_reports_context(self):
        source = (ROOT / "android/iw3-native/iw3_android_assert.cpp").read_text(encoding="utf-8")
        self.assertIn("void MyAssertHandler(", source)
        self.assertIn("__android_log_print(", source)
        self.assertIn("ANDROID_LOG_FATAL", source)
        self.assertIn("std::vsnprintf(", source)
        self.assertIn("std::abort();", source)
        self.assertNotIn("void MyAssertHandler(...) {}", source)

    def test_original_screen_placement_global_and_setup_are_compiled(self):
        source = (ROOT / "third_party/KisakCOD/src/client/screen_placement.cpp").read_text(encoding="utf-8")
        self.assertIn("ScreenPlacement scrPlaceView[1];", source)
        self.assertIn("void __cdecl ScrPlace_SetupFloatViewport(", source)
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn("add_library(iw3_sp_screen_placement_full_compile OBJECT", cmake)
        self.assertIn('"\u0024{IW3_ENGINE_SOURCE_ROOT}/client/screen_placement.cpp"', cmake)

    def test_aarch64_link_audit_resolves_only_the_two_platform_edges(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("Resolve original client aim-assist platform services (NOT RUNTIME)", workflow)
        self.assertIn("iw3_android_assert.cpp", workflow)
        self.assertIn("screen_placement.cpp", workflow)
        self.assertIn("IW3_ORIGINAL_CLIENT_AIMASSIST_PLATFORM_SERVICE_EDGES_RESOLVED_AARCH64_GREEN", workflow)
        self.assertIn("IW3_CLIENT_RUNTIME_LINKED=false", workflow)
        self.assertIn("IW3_AIMASSIST_DVARS_REGISTERED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)

    def test_host_assert_test_checks_abort_and_message(self):
        source = (ROOT / "android/iw3-native/assert_native_test.cpp").read_text(encoding="utf-8")
        self.assertIn("WTERMSIG(status) != SIGABRT", source)
        self.assertIn("ASSERTION FAIL AT android_assert_native_test.cpp:42", source)


if __name__ == "__main__":
    unittest.main()
