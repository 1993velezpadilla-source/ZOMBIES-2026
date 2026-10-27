"""Regression tests for the authentic IW3 filesystem-startup source slice."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_fs_startup import (
    SOURCE, FUNCTIONS, REQUIRED, FORBIDDEN, prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalFilesystemStartupTests(unittest.TestCase):
    def test_startup_functions_are_exact_original_bodies_and_not_claimed_as_runtime(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        bodies = [function_source(source, signature) for signature in FUNCTIONS]
        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "iw3_fs_startup.cpp"
            report_path = Path(temp) / "evidence.json"
            report = prepare(ENGINE, output, report_path)
            staged = output.read_text(encoding="utf-8")
            for body in bodies:
                self.assertIn(body, staged)
            self.assertEqual(report["source_sha256"],
                             hashlib.sha256(original).hexdigest())
            self.assertTrue(report["original_FS_RegisterDvars_body_preserved_verbatim"])
            self.assertTrue(report["original_FS_Startup_body_preserved_verbatim"])
            self.assertTrue(report["original_FS_SetRestrictions_body_preserved_verbatim"])
            self.assertTrue(report["original_FS_IsBasePathValid_body_preserved_verbatim"])
            self.assertTrue(report["original_FS_InitFilesystem_body_preserved_verbatim"])
            self.assertTrue(report["string_dvars_use_native_pointer_members"])
            self.assertIn("homePath = nullptr;", staged)
            self.assertNotIn("homePath = (char *)RETURN_ZERO32();", staged)
            self.assertFalse(report["dvar_registry_linked"])
            self.assertFalse(report["startup_runtime_invoked"])
            self.assertFalse(report["licensed_fastfile_or_map_loaded"])
            self.assertFalse(report["renderer_or_gameplay_proven"])
            self.assertFalse(report["playable_apk"])
            for marker in REQUIRED:
                self.assertIn(marker, staged)
            for marker in FORBIDDEN:
                self.assertNotIn(marker, staged)
            saved_report = report_path.read_text(encoding="utf-8")
            self.assertIn('"startup_runtime_invoked": false', saved_report)
        self.assertEqual(source_path.read_bytes(), original)

    def test_android_path_service_uses_configured_private_root_not_process_cwd(self):
        platform = (ROOT / "android/iw3-native/iw3_android_platform.cpp").read_text(encoding="utf-8")
        header = (ROOT / "android/iw3-native/iw3_android_platform.h").read_text(encoding="utf-8")
        adapter = (ROOT / "android/iw3-native/iw3_android_fs_startup_io.cpp").read_text(encoding="utf-8")
        compat = (ROOT / "android/iw3-native/iw3_android_fs_startup_compat.h").read_text(encoding="utf-8")
        native_test = (ROOT / "android/iw3-native/platform_native_test.cpp").read_text(encoding="utf-8")
        jni = (ROOT / "android/iw3-native/iw3_android_jni.cpp").read_text(encoding="utf-8")
        self.assertIn("z2026_platform_copy_data_root", platform)
        self.assertIn("z2026_platform_copy_data_root", header)
        self.assertIn("char *Sys_Cwd()", adapter)
        self.assertIn("z2026_platform_copy_data_root", adapter)
        self.assertIn("Sys_DefaultCDPath()", adapter)
        self.assertIn("typedef int BOOL;", compat)
        self.assertIn("FS_GameDirDomainFunc", compat)
        self.assertIn("z2026_platform_copy_data_root", native_test)
        self.assertIn("IW3_JNI_FS_STARTUP_PATH_%s", jni)


if __name__ == "__main__":
    unittest.main()
