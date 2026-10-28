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
        self.assertIn('"$ld_lld" -m aarch64linux -r --whole-archive "$startup_archive" --no-whole-archive', workflow)
        self.assertIn('iw3-fs-startup-combined.o', workflow)
        self.assertIn('iw3-fs-startup-undefined.txt', workflow)
        self.assertIn("Android rooted Sys_DirectoryHasContents adapter failed", workflow)
        # Do not test a symbol-level undefined entry from an individual archive
        # member as if it were unresolved by the complete archive.
        self.assertNotIn('grep -F "Sys_DirectoryHasContents" "$RUNNER_TEMP/iw3-fs-startup-member-undefined.txt"', workflow)
        self.assertNotIn("SEH_InitLanguage Sys_DirectoryHasContents; do", workflow)


    def test_directory_service_audit_links_real_adapter_and_keeps_runtime_gates(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        generator = (ROOT / "tools/iw3_android/prepare_real_engine_iwd_directory_services.py").read_text(encoding="utf-8")
        adapter = (ROOT / "android/iw3-native/iw3_android_iwd_directory_io.cpp").read_text(encoding="utf-8")
        self.assertIn("add_library(iw3_sp_iwd_directory_services STATIC", cmake)
        self.assertIn("IW3_EXTRACTED_IWD_DIRECTORY_SERVICES", cmake)
        self.assertIn("iw3_android_platform.cpp", cmake)
        self.assertIn("prepare_real_engine_iwd_directory_services.py", workflow)
        self.assertIn('libiw3_sp_iwd_directory_services.a', workflow)
        self.assertIn("FS_FreeFileList", workflow)
        self.assertIn("SEH_InitLanguage", workflow)
        self.assertIn("playable_apk", generator)
        self.assertIn("runtime_execution_proven", generator)
        self.assertIn("#if !defined(IW3_IWD_DIRECTORY_LINK_AUDIT)", adapter)
        self.assertIn("void __cdecl Com_Printf", adapter)
        self.assertIn("IW3_IWD_DIRECTORY_LINK_AUDIT=1", cmake)

    def test_directory_helper_generator_extracts_only_nonduplicated_upstream_helpers(self):
        import json
        import subprocess
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "iwd_directory_services.cpp"
            report = Path(temporary) / "report.json"
            completed = subprocess.run(
                [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_iwd_directory_services.py"),
                 "--engine", str(ROOT / "third_party/KisakCOD"),
                 "--output", str(output), "--report", str(report)],
                cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            evidence = json.loads(report.read_text(encoding="utf-8"))
            staged = output.read_text(encoding="utf-8")
            self.assertTrue(evidence["helper_bodies_preserved_verbatim"])
            self.assertTrue(evidence["native_pointer_width_qsort_verified_in_original_scanner"])
            self.assertFalse(evidence["runtime_execution_proven"])
            self.assertFalse(evidence["playable_apk"])
            self.assertIn("int __cdecl I_strncmp", staged)
            self.assertIn("int __cdecl FS_PathCmp", staged)
            self.assertIn("int __cdecl iwdsort", staged)
            self.assertNotIn("void __cdecl FS_AddIwdFilesForGameDirectory(", staged)
            self.assertNotIn("void __cdecl FS_AddGameDirectory(", staged)

if __name__ == "__main__":
    unittest.main()
