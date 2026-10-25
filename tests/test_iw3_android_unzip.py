import hashlib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.iw3_android.prepare_real_engine_unzip import (
    HEADER, PROLOGUE, REQUIRED_FIXED_FIELDS, REQUIRED_SOURCE, SOURCE, prepare,
)

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party" / "KisakCOD"


class OriginalIW3UnzipPortTests(unittest.TestCase):
    def test_zip32_public_and_internal_numeric_fields_are_fixed_width(self):
        header = (ENGINE / HEADER).read_text(encoding="utf-8")
        source = (ENGINE / SOURCE).read_text(encoding="utf-8")
        for marker in REQUIRED_FIXED_FIELDS:
            with self.subTest(marker=marker):
                self.assertIn(marker, header)
        for line in header.splitlines():
            if line.lstrip().startswith("//"):
                continue
            self.assertNotRegex(line, r"\bunsigned long\s+\w+\s*;")
        self.assertIn("uint32_t fileNameBufferSize", source)
        self.assertIn("uint32_t extraFieldBufferSize", source)
        self.assertIn("uint32_t commentBufferSize", source)
        self.assertIn("uint32_t *pos", source)
        self.assertIn("uint32_t pos", source)
        self.assertIn("static_assert(sizeof(unz_file_info) == 80", 
                      (ROOT / "android/iw3-native/iw3_unzip_native_smoke.cpp").read_text())

    def test_original_parser_body_is_staged_without_reimplementation(self):
        source_path = ENGINE / SOURCE
        header_path = ENGINE / HEADER
        source_bytes = source_path.read_bytes()
        header_bytes = header_path.read_bytes()
        source = source_bytes.decode("utf-8")
        self.assertEqual(source.count(PROLOGUE), 1)
        prologue_offset = source.index(PROLOGUE)
        for marker in REQUIRED_SOURCE:
            self.assertEqual(source.count(marker), 1)
        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "unzip.cpp"
            evidence = prepare(ENGINE, output)
            staged = output.read_text(encoding="utf-8")
            self.assertEqual(staged, source[:prologue_offset] +
                             '#include "iw3_android_unzip_compat.h"\n' +
                             source[prologue_offset + len(PROLOGUE):])
            self.assertEqual(evidence["source_sha256"], hashlib.sha256(source_bytes).hexdigest())
            self.assertEqual(evidence["header_sha256"], hashlib.sha256(header_bytes).hexdigest())
            self.assertTrue(evidence["parser_body_preserved_after_include_adapter"])
            self.assertTrue(evidence["zip32_numeric_fields_fixed_width"])
            self.assertFalse(evidence["archive_searchpath_integration"])
            self.assertFalse(evidence["map_loading_verified"])
            with self.assertRaisesRegex(ValueError, "Cannot overwrite"):
                prepare(ENGINE, source_path)
        self.assertEqual(source_path.read_bytes(), source_bytes)
        self.assertEqual(header_path.read_bytes(), header_bytes)

    def test_original_zip_reader_uses_root_confined_android_file_handles(self):
        adapter = (ROOT / "android/iw3-native/iw3_android_unzip_io.cpp").read_text(encoding="utf-8")
        smoke = (ROOT / "android/iw3-native/iw3_unzip_native_smoke.cpp").read_text(encoding="utf-8")
        platform = (ROOT / "android/iw3-native/iw3_android_platform.cpp").read_text(encoding="utf-8")
        platform_test = (ROOT / "android/iw3-native/platform_native_test.cpp").read_text(encoding="utf-8")
        activity = (ROOT / "android/iw3-native/android_app/app/src/main/java/org/z2026/iw3nativeprobe/MainActivity.java").read_text(encoding="utf-8")
        self.assertIn("z2026_platform_open_engine_path_fd(filename)", adapter)
        self.assertNotIn("std::fopen(filename", adapter)
        self.assertIn("z2026_platform_set_data_root(directory)", smoke)
        self.assertIn("z2026_platform_write_file(path", smoke)
        self.assertIn('iw3-unzip-smoke-%ld.iwd', smoke)
        self.assertIn("z2026_platform_list_iwd_files", smoke)
        self.assertIn("unzOpen(path)", smoke)
        self.assertIn("absolute_parse_ok", smoke)
        self.assertIn("z2026_platform_unlink_file(path)", smoke)
        self.assertIn("z2026_platform_open_engine_path_fd", platform)
        self.assertIn("z2026_platform_list_iwd_files", platform)
        self.assertIn("normalize_engine_path", platform)
        self.assertIn("O_NOFOLLOW", platform)
        self.assertIn("open_beneath_root(g_data_root_fd, relative)", platform)
        self.assertIn('z2026_platform_open_read_fd("../sample.txt") == -1', platform_test)
        self.assertIn("z2026_platform_open_engine_path_fd(path.c_str())", platform_test)
        self.assertIn("z2026_platform_list_iwd_files", platform_test)
        self.assertIn('z2026_platform_write_file("../escape.bin", "bad", 3) == -1', platform_test)
        self.assertIn('z2026_platform_write_file("outside", "bad", 3) == -1', platform_test)
        self.assertIn("nativeReport(getFilesDir().getAbsolutePath())", activity)

    def test_native_and_android_builds_require_real_parser(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        gradle = (ROOT / "android/iw3-native/android_app/app/build.gradle").read_text(encoding="utf-8")
        jni = (ROOT / "android/iw3-native/iw3_android_jni.cpp").read_text(encoding="utf-8")
        self.assertIn("IW3_EXTRACTED_UNZIP", cmake)
        self.assertIn("iw3_android_unzip_io.cpp", cmake)
        self.assertIn("iw3_unzip_native_smoke.cpp", cmake)
        self.assertIn("IW3_EXTRACTED_UNZIP", gradle)
        self.assertIn("z2026_iw3_unzip_smoke", jni)
        self.assertIn("IW3_JNI_UNZIP_PARSER_PASS", 
                      (ROOT / "tools/iw3_android/verify_runtime_evidence.py").read_text())

if __name__ == "__main__":
    unittest.main()
