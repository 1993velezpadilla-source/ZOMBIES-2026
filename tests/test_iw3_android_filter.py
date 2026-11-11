"""Regression coverage for the portable provider of KisakCOD's filter service."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OriginalFilterProviderTests(unittest.TestCase):
    def test_provider_is_compiled_and_audited_with_original_filesystem(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        source = (ROOT / "android/iw3-native/iw3_android_filter.cpp").read_text(encoding="utf-8")
        self.assertIn('add_library(iw3_sp_filter STATIC', cmake)
        self.assertIn('add_executable(iw3_filter_host_test', cmake)
        self.assertIn('add_test(NAME iw3_original_filter_path_semantics', cmake)
        self.assertIn('libiw3_sp_filter.a', workflow)
        self.assertIn('Com_FilterPath', workflow)
        self.assertIn('Com_Filter(', workflow)
        self.assertIn('Com_FilterPath', source)
        self.assertIn('MAX_QPATH - 1', source)
        self.assertIn('std::toupper(static_cast<unsigned char>', source)
        self.assertIn('IW3_PLAYABLE_APK=false', workflow)

    def test_provider_is_explicitly_not_claimed_as_gameplay(self):
        source = (ROOT / "android/iw3-native/iw3_android_filter.cpp").read_text(encoding="utf-8")
        self.assertIn('not a', source)
        self.assertIn('replacement filesystem', source)


if __name__ == "__main__":
    unittest.main()
