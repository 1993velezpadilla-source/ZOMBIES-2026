"""Guard the Android diagnostic touch surface against UIAutomator invisibility."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ACTIVITY = ROOT / "android/iw3-native/android_app/app/src/main/java/org/z2026/iw3nativeprobe/MainActivity.java"
PLATFORM = ROOT / "android/iw3-native/iw3_android_platform.cpp"
PLATFORM_TEST = ROOT / "android/iw3-native/platform_native_test.cpp"
PROBE = ROOT / "tools/iw3_android/run_emulator_probe.sh"


class TouchSurfaceAccessibilityTests(unittest.TestCase):
    def test_activity_exposes_actual_touch_view_to_accessibility(self):
        source = ACTIVITY.read_text(encoding="utf-8")
        self.assertIn('setContentDescription("IW3 native diagnostic touch surface")', source)
        self.assertIn("setFocusable(true)", source)
        self.assertIn("setClickable(true)", source)
        self.assertIn("setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES)", source)

    def test_runtime_probe_targets_that_visible_view(self):
        source = PROBE.read_text(encoding="utf-8")
        self.assertIn("IW3 native diagnostic touch surface", source)
        self.assertIn("Native diagnostic view did not become visible after bounded UI recovery", source)
        self.assertNotIn("fallback to arbitrary coordinate", source.lower())

    def test_probe_recovers_only_a_launcher_anr_using_real_wait_button_bounds(self):
        source = PROBE.read_text(encoding="utf-8")
        self.assertIn("max_ui_attempts=5", source)
        self.assertIn("ensure_app_ready()", source)
        self.assertIn("ANDROID_SYSTEM_UI_RECOVERY_BEFORE_GESTURE", source)
        self.assertIn('input touchscreen swipe "$sprint_x" "$sprint_y" "$sprint_x" "$sprint_y" 600', source)
        self.assertIn("Quickstep isn't responding", source)
        self.assertIn("android:id/aerr_wait", source)
        self.assertIn('adb shell input tap "$ui_x" "$ui_y"', source)
        self.assertIn("Native diagnostic view did not become visible after bounded UI recovery", source)
        self.assertNotIn("fallback to arbitrary coordinate", source.lower())

    def test_uiautomator_bounds_are_scaled_to_physical_pixels_and_modal_anr_wins(self):
        source = PROBE.read_text(encoding="utf-8")
        self.assertIn('"$proof_dir/screen-before-touch.png" <<\'PY\'', source)
        self.assertIn("ui_max_x = max(bounds[2] for bounds in all_bounds)", source)
        self.assertIn("ui_max_y = max(bounds[3] for bounds in all_bounds)", source)
        self.assertIn("scale_x = screen_w / ui_max_x", source)
        self.assertIn("scale_y = screen_h / ui_max_y", source)
        self.assertLess(
            source.index('if any(node.get("text") == "Quickstep isn\'t responding"'),
            source.index("for node in nodes:\\n    if (node.get('package') == 'org.z2026.iw3nativeprobe'"),
        )

    def test_sparse_android_pointer_ids_are_mapped_to_native_touch_slots(self):
        native = PLATFORM.read_text(encoding="utf-8")
        activity = ACTIVITY.read_text(encoding="utf-8")
        self.assertIn("constexpr int kAndroidPointerIdCount = 32;", native)
        self.assertIn("find_touch_by_pointer_id", native)
        self.assertIn("allocate_touch_slot", native)
        self.assertIn("pointer_id = -1;", native)
        self.assertIn("MAX_ANDROID_POINTER_ID_COUNT = 32", activity)
        self.assertNotIn("id >= 10", activity)

    def test_native_regression_covers_pointer_id_above_slot_count(self):
        source = PLATFORM_TEST.read_text(encoding="utf-8")
        self.assertIn("z2026_platform_touch_event(31, .90f, .85f, 1)", source)
        self.assertIn("z2026_platform_touch_snapshot(31, &x, &y)", source)
        self.assertIn("z2026_platform_touch_event(32, .5f, .5f, 1) == -1", source)


    def test_off_view_coordinates_are_clamped_and_release_clears_buttons(self):
        native = PLATFORM.read_text(encoding="utf-8")
        regression = PLATFORM_TEST.read_text(encoding="utf-8")
        self.assertIn("x = std::clamp(x, 0.0f, 1.0f);", native)
        self.assertIn("y = std::clamp(y, 0.0f, 1.0f);", native)
        self.assertIn("!std::isfinite(x) || !std::isfinite(y)", native)
        self.assertIn("z2026_platform_touch_event(6, 1.25f, .85f, 0) == 0", regression)
        self.assertIn("off_view_release_cmd[1] & BUTTON_ATTACK", regression)


if __name__ == "__main__":
    unittest.main()
