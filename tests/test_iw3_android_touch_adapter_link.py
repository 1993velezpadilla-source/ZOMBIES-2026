"""Regression coverage for resolving the real Android touch adapter in the original client-input link audit."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OriginalClientTouchAdapterLinkTests(unittest.TestCase):
    def test_adapter_mutates_the_original_usercmd_and_consumes_look_delta_once(self):
        platform = (ROOT / "android/iw3-native/iw3_android_platform.cpp").read_text(encoding="utf-8")
        native_test = (ROOT / "android/iw3-native/platform_native_test.cpp").read_text(encoding="utf-8")

        self.assertIn(
            'extern "C" IW3_ANDROID_EXPORT void z2026_platform_apply_touch_to_usercmd(',
            platform,
        )
        self.assertIn("usercmd_s *command, float *viewangles)", platform)
        self.assertIn("if (!command || !viewangles) return;", platform)
        self.assertIn("std::lock_guard<std::mutex> lock(g_touch_mutex);", platform)
        self.assertIn("g_pending_pitch_degrees = 0.0f;", platform)
        self.assertIn("g_pending_yaw_degrees = 0.0f;", platform)
        self.assertIn("z2026_platform_apply_touch_to_usercmd(&actual_command, actual_viewangles);", native_test)
        self.assertIn("assert((actual_command.buttons & BUTTON_ATTACK) != 0);", native_test)
        self.assertIn("assert(actual_command.forwardmove > 0 && actual_command.rightmove > 0);", native_test)
        self.assertIn("assert(actual_viewangles[0] == applied_pitch && actual_viewangles[1] == applied_yaw);", native_test)

    def test_arm64_gate_compiles_and_links_adapter_into_original_command_chain(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("Compile the real Android touch adapter and resolve the original client hook (NOT RUNTIME)", workflow)
        self.assertIn('platform_source="$GITHUB_WORKSPACE/android/iw3-native/iw3_android_platform.cpp"', workflow)
        self.assertIn('"$ndk/ld.lld" -m aarch64linux -r "$client_input" "$platform_object" -o "$combined"', workflow)
        self.assertIn("IW3_ORIGINAL_CLIENT_TOUCH_ADAPTER_EDGE_RESOLVED_AARCH64_GREEN", workflow)
        self.assertIn('if grep -F \'z2026_platform_apply_touch_to_usercmd\' "$RUNNER_TEMP/iw3-client-input-plus-touch-undefined.txt"; then', workflow)
        self.assertIn("IW3_CLIENT_RUNTIME_LINKED=false", workflow)
        self.assertIn("IW3_TOUCH_ADAPTER_RUNTIME_INVOKED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)


if __name__ == "__main__":
    unittest.main()
