import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_SOURCE = ROOT / "third_party/KisakCOD/src/universal/com_files.cpp"
GENERATOR = ROOT / "tools/iw3_android/prepare_real_engine_fs_read.py"
COMPAT = ROOT / "android/iw3-native/iw3_android_fs_read_compat.h"
SMOKE = ROOT / "android/iw3-native/iw3_unzip_native_smoke.cpp"


class OriginalIW3FileHandleCloseTests(unittest.TestCase):
    def test_original_close_clears_native_width_record(self):
        source = ENGINE_SOURCE.read_text(encoding="utf-8")
        signature = "void __cdecl FS_FCloseFile(int h)"
        self.assertEqual(source.count(signature), 1)
        body = source[source.index(signature):]
        self.assertIn("Com_Memset((uint32_t *)&fsh[h], 0, sizeof(fsh[h]));", body)
        self.assertNotIn("Com_Memset((uint32_t *)&fsh[h], 0, 284);", body)

    def test_close_body_is_compiled_by_existing_original_source_gate(self):
        generator = GENERATOR.read_text(encoding="utf-8")
        self.assertIn('"void __cdecl FS_FCloseFile(int h)"', generator)
        self.assertIn('"Com_Memset((uint32_t *)&fsh[h], 0, sizeof(fsh[h]));"', generator)
        self.assertIn('"full_open_read_close_lifecycle_integrated": True', generator)
        self.assertIn('"original_upstream_fsh_table_integrated": False', generator)
        compat = COMPAT.read_text(encoding="utf-8")
        self.assertIn("#define FS_FileClose z2026_iw3_fs_file_close", compat)

    def test_android_fixture_calls_original_close_and_checks_full_record(self):
        smoke = SMOKE.read_text(encoding="utf-8")
        self.assertIn("FS_FOpenFileReadForThread(", smoke)
        self.assertIn("FS_FCloseFile(primary_handle);", smoke)
        self.assertIn("FS_FCloseFile(clone_handle);", smoke)
        self.assertIn("fsh[clone_handle].handleFiles.iwdIsClone == 1", smoke)
        self.assertIn("std::memcmp(&fsh[clone_handle], &cleared, sizeof(cleared)) == 0", smoke)


if __name__ == "__main__":
    unittest.main()
