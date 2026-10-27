"""Regression tests for the Android adapter of original Sys_DirectoryHasContents."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AndroidFsStartupDirectoryTests(unittest.TestCase):
    def test_adapter_is_rooted_fails_closed_and_uses_posix_abi(self):
        source = (ROOT / "android/iw3-native/iw3_android_directory_has_contents.cpp").read_text(encoding="utf-8")
        self.assertIn("int Sys_DirectoryHasContents(const char *directory)", source)
        # This adapter is compiled on POSIX host and Android; __cdecl is a
        # Win32 spelling and must not leak into this translation unit.
        self.assertNotIn("__cdecl Sys_DirectoryHasContents", source)
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
        self.assertIn('ld.lld -r --whole-archive "$startup_archive" --no-whole-archive', workflow)
        self.assertIn('iw3-fs-startup-combined.o', workflow)
        self.assertIn('iw3-fs-startup-undefined.txt', workflow)
        self.assertIn("Android rooted Sys_DirectoryHasContents adapter failed", workflow)
        # Do not test a symbol-level undefined entry from an individual archive
        # member as if it were unresolved by the complete archive.
        self.assertNotIn('grep -F "Sys_DirectoryHasContents" "$RUNNER_TEMP/iw3-fs-startup-member-undefined.txt"', workflow)
        self.assertNotIn("SEH_InitLanguage Sys_DirectoryHasContents; do", workflow)


if __name__ == "__main__":
    unittest.main()
