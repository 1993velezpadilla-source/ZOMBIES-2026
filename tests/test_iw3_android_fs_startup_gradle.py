"""Keep the original filesystem-startup translation unit in both Android Gradle build paths."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AndroidFsStartupGradleTests(unittest.TestCase):
    def test_gradle_passes_the_generated_original_startup_source(self):
        gradle = (ROOT / "android/iw3-native/android_app/app/build.gradle").read_text(encoding="utf-8")
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn("IW3_EXTRACTED_FS_STARTUP=${new File(sourceDir, 'iw3_fs_startup.cpp').absolutePath}", gradle)
        self.assertIn("if(NOT IW3_EXTRACTED_FS_STARTUP OR NOT EXISTS", cmake)

    def test_both_android_workflows_generate_the_same_startup_source_before_gradle(self):
        for path in (
            ".github/workflows/iw3-original-android-jni.yml",
            ".github/workflows/iw3-original-android-emulator-jni.yml",
        ):
            workflow = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn("prepare_real_engine_fs_startup.py", workflow)
            self.assertIn('--output "$folder/iw3_fs_startup.cpp"', workflow)
            self.assertIn('--report "$RUNNER_TEMP/iw3-original-fs-startup.json"', workflow)
            self.assertIn("iw3-original-fs-startup.json", workflow)


if __name__ == "__main__":
    unittest.main()
