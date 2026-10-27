"""Regression tests for the Android adapter of original Sys_DirectoryHasContents."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AndroidFsStartupDirectoryTests(unittest.TestCase):
    def test_adapter_is_rooted_and_fails_closed(self):
        source = (ROOT / "android/iw3-native/iw3_android_directory_has_contents.cpp").read_text(encoding="utf-8")
        self.assertIn("int Sys_DirectoryHasContents(const char *directory)", source)
        self.assertIn("z2026_platform_copy_data_root", source)
        self.assertIn("z2026_platform_directory_has_contents(relative)", source)
        self.assertIn("return result > 0 ? 1 : 0;", source)
        self.assertIn("Reject sibling paths", source)

    def test_native_test_and_arm64_audit_require_resolution(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("iw3_android_directory_has_contents.cpp", cmake)
        self.assertIn("fs_startup_directory_native_test.cpp", cmake)
        self.assertIn("iw3_original_fs_directory_probe_rooted", cmake)
        self.assertIn("Sys_DirectoryHasContents; do", workflow)
        self.assertIn("Android rooted Sys_DirectoryHasContents adapter failed", workflow)
        self.assertNotIn("SEH_InitLanguage Sys_DirectoryHasContents; do", workflow)


if __name__ == "__main__":
    unittest.main()
