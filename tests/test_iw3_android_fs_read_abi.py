"""Ensure the original FS_Read body is ABI-compiled but not misreported as runtime-linked."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OriginalFSReadAbiGateTests(unittest.TestCase):
    def test_original_fs_read_has_separate_compile_only_archive(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        header = (ROOT / "android/iw3-native/iw3_android_fs_read_compat.h").read_text(encoding="utf-8")
        gradle = (ROOT / "android/iw3-native/android_app/app/build.gradle").read_text(encoding="utf-8")
        self.assertIn("add_library(iw3_sp_fs_read STATIC", cmake)
        self.assertIn("IW3_EXTRACTED_FS_READ", cmake)
        self.assertIn("IW3_EXTRACTED_FS_READ", gradle)
        self.assertIn("static_assert(sizeof(fileHandleData_t) == 304", header)
        self.assertIn("offsetof(fileHandleData_t, zipFile) == 32", header)
        self.assertIn("offsetof(fileHandleData_t, name) == 44", header)
        self.assertIn("extern fileHandleData_t fsh[65]", header)

        start = cmake.index("add_library(iw3_sp_math SHARED")
        end = cmake.index("target_include_directories(iw3_sp_math PRIVATE", start)
        self.assertNotIn("IW3_EXTRACTED_FS_READ", cmake[start:end],
                         "FS_Read must not silently enter the diagnostic JNI library")

    def test_every_android_source_workflow_generates_the_exact_fs_read_body(self):
        workflows = (
            ".github/workflows/iw3-original-native-android.yml",
            ".github/workflows/iw3-original-android-jni.yml",
            ".github/workflows/iw3-original-android-emulator-jni.yml",
        )
        for path in workflows:
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                self.assertIn("prepare_real_engine_fs_read.py", text)
                self.assertIn("iw3_fs_read.cpp", text)

    def test_fs_read_generator_preserves_original_body_and_declines_runtime_claim(self):
        generator = (ROOT / "tools/iw3_android/prepare_real_engine_fs_read.py").read_text(encoding="utf-8")
        self.assertIn("FS_Read(uint8_t *buffer, uint32_t len, int h)", generator)
        self.assertIn('"android_file_handle_table_integrated": False', generator)
        self.assertIn('"playable_apk": False', generator)


if __name__ == "__main__":
    unittest.main()
