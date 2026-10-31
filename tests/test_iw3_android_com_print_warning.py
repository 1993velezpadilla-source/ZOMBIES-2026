"""Regression tests for the original KisakCOD warning service on Android."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_com_print_warning import (
    SOURCE, SIGNATURE, REQUIRED_SOURCE, FORBIDDEN, prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalComPrintWarningTests(unittest.TestCase):
    def test_original_warning_body_is_staged_with_narrow_android_adaptation(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        body = function_source(source, SIGNATURE)
        for marker in REQUIRED_SOURCE:
            self.assertIn(marker, body)

        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "iw3_com_print_warning.cpp"
            report_path = Path(temp) / "com-print-warning.json"
            report = prepare(ENGINE, output, report_path)
            staged = output.read_text(encoding="utf-8")
            self.assertIn("std::vsnprintf", staged)
            self.assertIn("va_end(va);", staged)
            self.assertIn("dest[0] = '^';", staged)
            self.assertIn("dest[1] = '3';", staged)
            self.assertIn("v3 = 2;", staged)
            self.assertIn("Com_PrintMessage(channel, dest, 2);", staged)
            self.assertNotIn("_vsnprintf(", staged)
            for marker in FORBIDDEN:
                self.assertNotIn(marker, staged)
            self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
            self.assertTrue(report["original_com_print_warning_body_staged"])
            self.assertTrue(report["android_vsnprintf_portability_adaptation_only"])
            self.assertTrue(report["warning_color_prefix_and_type_2_preserved"])
            self.assertFalse(report["full_common_translation_unit_linked"])
            self.assertFalse(report["filesystem_startup_invoked"])
            self.assertFalse(report["fastfile_or_map_loaded"])
            self.assertFalse(report["renderer_or_gameplay_proven"])
            self.assertFalse(report["playable_apk"])
            self.assertIn('"playable_apk": false', report_path.read_text(encoding="utf-8"))

        self.assertEqual(source_path.read_bytes(), original)

    def test_native_workflow_compiles_and_requires_the_warning_provider(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        adapter = (ROOT / "android/iw3-native/iw3_android_com_print_message.cpp").read_text(encoding="utf-8")
        self.assertIn("prepare_real_engine_com_print_warning.py", workflow)
        self.assertGreaterEqual(workflow.count("IW3_EXTRACTED_COM_PRINT_WARNING"), 2)
        self.assertIn("IW3_ORIGINAL_COM_PRINT_WARNING_AARCH64_RESOLVED", workflow)
        self.assertIn("iw3_sp_com_print_warning", cmake)
        self.assertIn("if(IW3_EXTRACTED_COM_PRINT_WARNING)", cmake)
        self.assertIn("if(IW3_EXTRACTED_COM_PRINT_WARNING)\n        add_executable(iw3_com_print_warning_host_test", cmake)
        self.assertNotIn(r"\${", cmake)
        self.assertIn("Com_PrintMessage", adapter)
        self.assertIn("__android_log_write", adapter)
        self.assertIn("iw3_original_com_print_warning_android_sink", cmake)
        directory_io = (ROOT / "android/iw3-native/iw3_android_iwd_directory_io.cpp").read_text(encoding="utf-8")
        self.assertIn("#if !defined(IW3_IWD_DIRECTORY_LINK_AUDIT)\n// Console output adapter for this isolated native file-system test.", directory_io)
        self.assertIn("#endif\n#if !defined(IW3_IWD_DIRECTORY_LINK_AUDIT)\n// The diagnostic shared library", directory_io)


if __name__ == "__main__":
    unittest.main()
