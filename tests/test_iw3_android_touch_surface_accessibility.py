"""Guard the Android diagnostic touch surface against UIAutomator invisibility."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ACTIVITY = ROOT / "android/iw3-native/android_app/app/src/main/java/org/z2026/iw3nativeprobe/MainActivity.java"
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
        self.assertIn("Native diagnostic view is not visible in the actual Android hierarchy", source)
        self.assertNotIn("fallback to arbitrary coordinate", source.lower())


if __name__ == "__main__":
    unittest.main()
