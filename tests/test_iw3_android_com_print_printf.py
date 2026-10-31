"""Regression tests for the original KisakCOD Com_Printf Android port."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_com_print_printf import (
    SOURCE, SIGNATURE, REQUIRED_SOURCE, FORBIDDEN, prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalComPrintfTests(unittest.TestCase):
    def test_original_body_is_staged_with_only_bounded_formatter_adaptation(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        body = function_source(original.decode("utf-8"), SIGNATURE)
        for marker in REQUIRED_SOURCE:
            self.assertIn(marker, body)

        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "iw3_com_print_printf.cpp"
            report_path = Path(temp) / "com-print-printf.json"
            report = prepare(ENGINE, output, report_path)
            staged = output.read_text(encoding="utf-8")
            self.assertIn("std::vsnprintf(string, 0x1000u, fmt, va);", staged)
            self.assertIn("va_end(va);", staged)
            self.assertIn("string[4095] = 0;", staged)
            self.assertIn("Com_PrintMessage(channel, string, 0);", staged)
            for marker in FORBIDDEN:
                self.assertNotIn(marker, staged)
            self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
            self.assertTrue(report["original_com_printf_body_staged"])
            self.assertTrue(report["android_vsnprintf_adaptation_only"])
            self.assertTrue(report["normal_message_type_0_and_channel_preserved"])
            self.assertFalse(report["full_common_translation_unit_linked"])
            self.assertFalse(report["filesystem_startup_invoked"])
            self.assertFalse(report["fastfile_or_map_loaded"])
            self.assertFalse(report["renderer_or_gameplay_proven"])
            self.assertFalse(report["playable_apk"])
            self.assertIn('"playable_apk": false', report_path.read_text(encoding="utf-8"))

        self.assertEqual(source_path.read_bytes(), original)

    def test_native_workflow_links_and_requires_original_printf_provider(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn("prepare_real_engine_com_print_printf.py", workflow)
        self.assertGreaterEqual(workflow.count("IW3_EXTRACTED_COM_PRINT_PRINTF"), 2)
        self.assertIn("print_printf_archive", workflow)
        self.assertIn("Com_Printf(int, char const*, ...)", workflow)
        self.assertIn("IW3_ORIGINAL_COM_PRINTF_AARCH64_LINK_GREEN", workflow)
        self.assertLess(workflow.index('-o "$RUNNER_TEMP/iw3-fs-startup-combined.o"'), workflow.index('"$llvm_nm" -C --defined-only "$RUNNER_TEMP/iw3-fs-startup-combined.o"'))
        self.assertIn("iw3_sp_com_print_printf", cmake)
        self.assertIn("iw3_original_com_print_printf_android_sink", cmake)
        generator = (ROOT / "tools/iw3_android/prepare_real_engine_com_print_printf.py").read_text(encoding="utf-8")
        self.assertIn("Com_PrintMessage(channel, string, 0);", generator)

    def test_source_only_probe_never_claims_gameplay(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("IW3_FS_STARTUP_RUNTIME_INVOKED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)


    def test_original_printf_replaces_dvar_log_fallback_in_combined_audit(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        dvar_log = (ROOT / "android/iw3-native/iw3_android_dvar_log.cpp").read_text(encoding="utf-8")
        self.assertIn("IW3_ORIGINAL_COM_PRINT_PRINTF_LINK_AUDIT=1", cmake)
        self.assertIn("#if !defined(IW3_ORIGINAL_COM_PRINT_PRINTF_LINK_AUDIT)", dvar_log)
        self.assertIn('"$dvar_full_archive" "$print_warning_archive" "$print_printf_archive"', workflow)
        self.assertIn("iw3-full-dvar-combined-defined.txt", workflow)

if __name__ == "__main__":
    unittest.main()
