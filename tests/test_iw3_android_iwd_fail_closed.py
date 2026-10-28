"""Runtime regression guards for malformed original KisakCOD IWD indexes."""
from pathlib import Path
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE_SOURCE = ROOT / "third_party/KisakCOD/src/universal/com_files.cpp"
NATIVE_SMOKE = ROOT / "android/iw3-native/iw3_unzip_native_smoke.cpp"
EMULATOR_PROBE = ROOT / "tools/iw3_android/run_emulator_probe.sh"


class OriginalIwdFailClosedTests(unittest.TestCase):
    def test_original_loader_rejects_ambiguous_length_coded_names_before_allocating(self):
        source = ENGINE_SOURCE.read_text(encoding="utf-8")
        body = function_source(
            source, "iwd_t *__cdecl FS_LoadZipFile(char *zipfile, char *basename)"
        )
        guard = "if (!file_info.size_filename || strlen(filename_inzip) != file_info.size_filename)"
        self.assertIn(guard, body)
        self.assertLess(body.index(guard), body.index("Z_Malloc(buildBytes"))
        self.assertIn("unzClose(uf);", body[body.index(guard):body.index("Z_Malloc(buildBytes")])

    def test_android_smoke_executes_the_original_rejection_and_checks_global_state(self):
        smoke = NATIVE_SMOKE.read_text(encoding="utf-8")
        self.assertIn(r'std::string("maps/bad\0name.txt", 17)', smoke)
        self.assertIn("iwd_t *malformed_iwd = FS_LoadZipFile(", smoke)
        self.assertIn("malformed_iwd == nullptr", smoke)
        self.assertIn("fs_iwdFileCount == before_count", smoke)
        self.assertIn("fs_checksumFeed == 0x13579BDF", smoke)
        self.assertIn("IW3_JNI_MALFORMED_IWD_REJECTED_AND_CLEANUP_PASS", smoke)

    def test_emulator_gate_requires_the_new_runtime_marker(self):
        probe = EMULATOR_PROBE.read_text(encoding="utf-8")
        self.assertIn(
            "grep -F 'IW3_JNI_MALFORMED_IWD_REJECTED_AND_CLEANUP_PASS'",
            probe,
        )


if __name__ == "__main__":
    unittest.main()
