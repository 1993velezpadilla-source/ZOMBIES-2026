"""Regression tests for compiling the authentic IW3 open/read/close lifecycle."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_fs_read import (
    SOURCE, SHARED_SOURCE, SIGNATURE, FUNCTIONS, REQUIRED, PROLOGUE, prepare,
    definition_source,
)

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalFSReadStageTests(unittest.TestCase):
    def test_exact_original_open_read_close_bodies_are_staged(self):
        source_paths = {source_path for _, source_path in FUNCTIONS}
        originals = {source_path: (ENGINE / source_path).read_bytes()
                     for source_path in source_paths}
        texts = {source_path: raw.decode("utf-8")
                 for source_path, raw in originals.items()}
        bodies = [definition_source(texts[source_path], signature)
                  for signature, source_path in FUNCTIONS]
        combined = "\n\n".join(bodies) + "\n"
        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "iw3_fs_read.cpp"
            report_path = Path(temp) / "evidence.json"
            report = prepare(ENGINE, output, report_path)
            staged = output.read_text(encoding="utf-8")
            self.assertEqual(staged, PROLOGUE + combined)
            self.assertTrue(report["original_FS_filelength_body_preserved_exactly"])
            self.assertTrue(report["original_handle_allocation_body_preserved_exactly"])
            self.assertTrue(report["original_FS_FOpenFileReadForThread_body_preserved_exactly"])
            self.assertTrue(report["original_FS_FileForHandle_body_preserved_exactly"])
            self.assertTrue(report["original_FS_Read_body_preserved_exactly"])
            self.assertTrue(report["original_FS_FCloseFile_body_preserved_exactly"])
            self.assertTrue(report["original_extension_and_purity_helpers_preserved_exactly"])
            self.assertTrue(report["full_original_open_read_close_lifecycle_compiled_into_diagnostic"])
            self.assertTrue(report["engine_shared_fsh_table_source_present"])
            self.assertFalse(report["full_original_com_files_translation_unit_linked"])
            self.assertTrue(report["report_is_static_staging_audit"])
            self.assertFalse(report["runtime_handle_path_executed"])
            self.assertFalse(report["gameplay_proven"])
            self.assertFalse(report["playable_apk"])
            self.assertEqual(report["source_sha256"][str(SOURCE)],
                             hashlib.sha256(originals[SOURCE]).hexdigest())
            self.assertEqual(report["source_sha256"][str(SHARED_SOURCE)],
                             hashlib.sha256(originals[SHARED_SOURCE]).hexdigest())
            for marker in REQUIRED:
                self.assertIn(marker, combined)
        for source_path, original in originals.items():
            self.assertEqual((ENGINE / source_path).read_bytes(), original)


    def test_original_q_shared_casefold_helpers_are_unsigned_char_safe(self):
        source = (ENGINE / "src/universal/q_shared.cpp").read_text(encoding="utf-8")
        istristr = definition_source(
            source,
            "const char *__cdecl I_stristr(const char *s0, const char *substr)",
        )
        wildcard = definition_source(
            source,
            "int __cdecl I_stricmpwild(const char *wild, const char *s)",
        )
        self.assertIn(
            "tolower(static_cast<unsigned char>(s0[substrChar + s0Char]))",
            istristr,
        )
        self.assertIn(
            "tolower(static_cast<unsigned char>(substr[substrChar]))",
            istristr,
        )
        self.assertIn("tolower(static_cast<unsigned char>(charWild))", wildcard)
        self.assertIn("tolower(static_cast<unsigned char>(charRef))", wildcard)
        for unsafe in (
            "tolower(s0[substrChar + s0Char])",
            "tolower(substr[substrChar])",
            "tolower(charWild)",
            "tolower(charRef)",
        ):
            self.assertNotIn(unsafe, source)
        self.assertIn(
            "const char *__cdecl I_stristr(const char *s0, const char *substr)",
            [signature for signature, _ in FUNCTIONS],
        )
        self.assertIn(
            "int __cdecl I_stricmpwild(const char *wild, const char *s)",
            [signature for signature, _ in FUNCTIONS],
        )

        smoke = (ROOT / "android/iw3-native/iw3_unzip_native_smoke.cpp").read_text(encoding="utf-8")
        host = (ROOT / "android/iw3-native/iw3_unzip_host_test.cpp").read_text(encoding="utf-8")
        jni = (ROOT / "android/iw3-native/iw3_android_jni.cpp").read_text(encoding="utf-8")
        verifier = (ROOT / "tools/iw3_android/verify_runtime_evidence.py").read_text(encoding="utf-8")
        self.assertIn("z2026_iw3_casefold_smoke", smoke)
        self.assertIn("z2026_iw3_casefold_smoke", host)
        self.assertIn("IW3_JNI_Q_SHARED_CASEFOLD_%s", jni)
        self.assertIn("IW3_JNI_Q_SHARED_CASEFOLD_PASS", verifier)

    def test_directory_fallback_uses_original_handle_lifecycle(self):
        smoke = (ROOT / "android/iw3-native/iw3_unzip_native_smoke.cpp").read_text(encoding="utf-8")
        jni = (ROOT / "android/iw3-native/iw3_android_jni.cpp").read_text(encoding="utf-8")
        verifier = (ROOT / "tools/iw3_android/verify_runtime_evidence.py").read_text(encoding="utf-8")
        adapter = (ROOT / "android/iw3-native/iw3_android_fs_read_io.cpp").read_text(encoding="utf-8")
        self.assertIn("read_directory_file_via_original_fs", smoke)
        self.assertIn("FS_FOpenFileReadForThread(", smoke)
        self.assertIn("FS_Read(bytes.data(), expected_length, handle)", smoke)
        self.assertIn("FS_FCloseFile(handle);", smoke)
        self.assertIn("z2026_iw3_fs_file_get_size", adapter)
        self.assertIn("IW3_JNI_FS_DIRECTORY_OPEN_READ_CLOSE_PASS", verifier)
        self.assertIn('"original_fs_directory_fallback_read_executed": True', verifier)
        self.assertIn("iwd_fs_disk_read_ok && math_ok", jni)

    def test_handle_table_is_shared_engine_source_not_android_owned(self):
        header = (ENGINE / "src/universal/com_files.h").read_text(encoding="utf-8")
        original = (ENGINE / "src/universal/com_files.cpp").read_text(encoding="utf-8")
        table = (ENGINE / "src/universal/com_files_handle_table.cpp").read_text(encoding="utf-8")
        common = (ENGINE / "scripts/common_files.cmake").read_text(encoding="utf-8")
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        adapter = (ROOT / "android/iw3-native/iw3_android_fs_read_io.cpp").read_text(encoding="utf-8")
        self.assertIn("extern fileHandleData_t fsh[65];", header)
        self.assertNotIn("static fileHandleData_t fsh[65];", original)
        self.assertIn("fileHandleData_t fsh[65] = {};", table)
        self.assertIn("com_files_handle_table.cpp", common)
        self.assertGreaterEqual(cmake.count("universal/com_files_handle_table.cpp"), 2)
        self.assertNotIn("fileHandleData_t fsh[65]{};", adapter)
        self.assertIn("sizeof(fileHandleData_t) == (sizeof(void *) == 8 ? 304u : 284u)", table)

if __name__ == "__main__":
    unittest.main()
