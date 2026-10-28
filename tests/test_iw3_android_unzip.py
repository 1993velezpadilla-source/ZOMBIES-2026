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
        self.assertIn("unzOpen(archive_path)", smoke)
        self.assertIn("parse_original_iwd(path)", smoke)
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
        smoke = (ROOT / "android/iw3-native/iw3_unzip_native_smoke.cpp").read_text(encoding="utf-8")
        host_test = (ROOT / "android/iw3-native/iw3_unzip_host_test.cpp").read_text(encoding="utf-8")
        self.assertIn("IW3_EXTRACTED_UNZIP", cmake)
        self.assertIn("IW3_EXTRACTED_IWD_SERVICES", cmake)
        self.assertIn("IW3_EXTRACTED_IWD_SEARCHPATH", cmake)
        self.assertIn("\"${IW3_EXTRACTED_IWD_MOUNT}\"", cmake)
        self.assertIn("iw3_android_unzip_io.cpp", cmake)
        self.assertIn("iw3_android_iwd_lookup_io.cpp", cmake)
        self.assertIn("iw3_unzip_native_smoke.cpp", cmake)
        self.assertIn("IW3_EXTRACTED_UNZIP", gradle)
        self.assertIn("IW3_EXTRACTED_IWD_SERVICES", gradle)
        self.assertIn("IW3_EXTRACTED_IWD_SEARCHPATH", gradle)
        self.assertIn("z2026_iw3_unzip_smoke", jni)
        self.assertIn("IW3_JNI_IWD_MOUNT_%s", jni)
        self.assertIn("IW3_JNI_IWD_SEARCHPATH_%s", jni)
        self.assertIn("FS_LoadZipFile", smoke)
        self.assertIn("index_original_iwd(path, entries, &searchpath_ok, &fs_read_ok)", smoke)
        self.assertIn("FS_AddSearchPath(search)", smoke)
        self.assertIn("IW3_JNI_IWD_SEARCHPATH_PASS", (ROOT / "tools/iw3_android/verify_runtime_evidence.py").read_text())
        self.assertIn("IW3_JNI_IWD_DIRECTORY_SCAN_PASS", (ROOT / "tools/iw3_android/verify_runtime_evidence.py").read_text())
        self.assertIn("IW3_JNI_IWD_GAME_DIRECTORY_PASS", (ROOT / "tools/iw3_android/verify_runtime_evidence.py").read_text())
        self.assertIn("IW3_JNI_IWD_LOOKUP_PASS", (ROOT / "tools/iw3_android/verify_runtime_evidence.py").read_text())
        self.assertIn("FS_AddGameDirectory(root_copy, game_copy, 0, 0)", smoke)
        self.assertIn("directory_node->dir->gamedir", smoke)
        self.assertIn("scan_original_iwd_directory(\n        directory, entries, archiveBytes, &lookup_ok, &fs_disk_read_ok)", smoke)
        self.assertIn("z2026_iw3_original_searchpath_lookup", smoke)
        self.assertIn("iwd_directory_scan_ok != 1", host_test)
        self.assertIn("iwd_lookup_ok != 1", host_test)
        self.assertIn("iwd_fs_read_ok != 1", host_test)
        self.assertIn("iwd_fs_disk_read_ok != 1", host_test)
        self.assertIn("IW3_ORIGINAL_FS_READ_HOST_GREEN", host_test)
        self.assertIn("IW3_ORIGINAL_FS_DIRECTORY_READ_HOST_GREEN", host_test)
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        arm64_config = workflow.split('cmake -S android/iw3-native -B "$RUNNER_TEMP/iw3-build-arm64"', 1)[1].split("cmake --build", 1)[0]
        self.assertIn('-DIW3_EXTRACTED_IWD_DIRECTORY="$RUNNER_TEMP/iw3-source/iw3_iwd_directory.cpp"', arm64_config)
        self.assertIn("iwd_mount_ok != 1", host_test)
        self.assertIn("iwd_searchpath_ok != 1", host_test)
        self.assertIn("IW3_ORIGINAL_FS_ADDSSEARCHPATH_HOST_GREEN", host_test)
        self.assertIn("IW3_ORIGINAL_FS_LOADZIPFILE_INDEX_HOST_GREEN", host_test)
        self.assertIn("IW3_JNI_UNZIP_PARSER_PASS", 
                      (ROOT / "tools/iw3_android/verify_runtime_evidence.py").read_text())
        probe = (ROOT / "tools/iw3_android/run_emulator_probe.sh").read_text(encoding="utf-8")
        target_parser = (ROOT / "tools/iw3_android/parse_touch_target.py").read_text(encoding="utf-8")
        self.assertIn('node.get("class") == "android.widget.TextView"', target_parser)
        self.assertIn("parse_touch_target.py", probe)
        self.assertNotIn("ui_max_x = max(bounds[2] for bounds in all_bounds)", probe)
        self.assertNotIn("startswith('ORIGINAL KISAKCOD IW3 C++ CODE TEST')", probe)

if __name__ == "__main__":
    unittest.main()
