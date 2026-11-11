"""Regression coverage for the Android platform provider of original dvar Com_Printf."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "android/iw3-native/iw3_android_dvar_log.cpp"


class AndroidDvarLogProviderTests(unittest.TestCase):
    def test_provider_formats_channel_and_routes_to_android_logcat(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("void QDECL Com_Printf(int channel, const char *fmt, ...)", source)
        self.assertIn("std::vsnprintf", source)
        self.assertIn('"[channel %d] "', source)
        self.assertIn('__android_log_write(ANDROID_LOG_INFO, "IW3-Dvar", line)', source)
        self.assertIn("std::fwrite(line", source)
        self.assertNotIn("TODO", source)
        self.assertNotIn("return 0;", source)

    def test_android_archive_and_arm64_link_audit_require_real_provider(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("iw3_android_dvar_log.cpp", cmake)
        self.assertIn("dvar_log_native_test.cpp", cmake)
        self.assertIn("iw3_android_dvar_com_printf_format_and_channel", cmake)
        self.assertIn("Com_Printf(int, char const*, ...)", workflow)
        self.assertIn("__android_log_write", workflow)
        self.assertIn("Android Com_Printf log provider failed", workflow)


if __name__ == "__main__":
    unittest.main()
