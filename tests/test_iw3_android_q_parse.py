"""Regression tests for staging and auditing the authentic IW3 q_parse implementation."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from tools.iw3_android.prepare_real_engine_q_parse import (
    FUNCTIONS,
    SOURCE,
    prepare,
    punctuation_source,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]


class OriginalQParseExtractionTests(unittest.TestCase):
    def test_original_parser_functions_and_tables_are_preserved(self):
        engine = ROOT / "third_party/KisakCOD"
        source_path = engine / SOURCE
        before = source_path.read_bytes()
        source = before.decode("utf-8")
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_q_parse.cpp"
            report_path = Path(temp) / "iw3-q-parse.json"
            report = prepare(engine, output, report_path)
            generated = output.read_text(encoding="utf-8")
            saved_report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(source_path.read_bytes(), before)
        self.assertTrue(report["original_parser_bodies_preserved"])
        self.assertTrue(report["original_parse_thread_state_preserved"])
        self.assertTrue(report["original_punctuation_table_preserved"])
        self.assertFalse(report["parser_runtime_linked"])
        self.assertFalse(report["filesystem_startup_invoked"])
        self.assertFalse(report["real_game_data_mounted"])
        self.assertFalse(report["playable_apk"])
        self.assertEqual(saved_report, report)
        self.assertEqual(
            report["source_sha256"],
            hashlib.sha256(before).hexdigest(),
        )
        self.assertEqual(
            report["punctuation_table_sha256"],
            hashlib.sha256(punctuation_source(source).encode("utf-8")).hexdigest(),
        )
        for signature in FUNCTIONS:
            body = function_source(source, signature)
            self.assertIn(body, generated)
            self.assertEqual(
                report["function_body_sha256"][signature],
                hashlib.sha256(body.encode("utf-8")).hexdigest(),
            )
        self.assertIn("ParseThreadInfo g_parse[4];", generated)
        self.assertIn('const char *punctuation[15]', generated)
        self.assertIn("Com_ParseOnLine", generated)

    def test_generator_rejects_missing_original_source(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises((FileNotFoundError, OSError)):
                prepare(Path(temp) / "missing-engine", Path(temp) / "out.cpp")

    def test_native_parser_test_calls_real_parser_entrypoints(self):
        test_source = (
            ROOT / "android/iw3-native/parser_native_test.cpp"
        ).read_text(encoding="utf-8")
        for symbol in (
            "Com_InitParse()",
            "Com_BeginParseSession(",
            "Com_Parse(",
            "Com_UngetToken()",
            "Com_GetCurrentParseLine()",
            "Com_SetCSV(1)",
            "Com_EndParseSession()",
        ):
            self.assertIn(symbol, test_source)
        self.assertIn("IW3_ORIGINAL_Q_PARSE_HOST_RUNTIME_PASS", test_source)
        self.assertNotIn("fake Com_Parse", test_source)
        self.assertNotIn("void Com_Parse(", test_source)

    def test_arm64_archive_is_audited_but_never_added_to_jni_apk(self):
        cmake = (
            ROOT / "android/iw3-native/CMakeLists.txt"
        ).read_text(encoding="utf-8")
        workflow = (
            ROOT / ".github/workflows/iw3-original-native-android.yml"
        ).read_text(encoding="utf-8")
        jni = (
            ROOT / "android/iw3-native/iw3_android_jni.cpp"
        ).read_text(encoding="utf-8")

        self.assertIn("add_library(iw3_sp_q_parse STATIC", cmake)
        self.assertIn("if(IW3_EXTRACTED_Q_PARSE)", cmake)
        self.assertNotIn("if(NOT IW3_EXTRACTED_Q_PARSE OR NOT EXISTS", cmake)
        self.assertIn("add_test(NAME iw3_original_q_parse_host_runtime", cmake)
        self.assertIn("prepare_real_engine_q_parse.py", workflow)
        self.assertIn('-DIW3_EXTRACTED_Q_PARSE="$RUNNER_TEMP/iw3-source/iw3_q_parse.cpp"', workflow)
        self.assertIn('libiw3_sp_q_parse.a', workflow)
        self.assertIn("IW3_ORIGINAL_Q_PARSE_AARCH64_LINK_GREEN", workflow)
        self.assertIn("IW3_FS_STARTUP_RUNTIME_INVOKED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)
        self.assertNotIn("iw3_sp_q_parse", jni)
        self.assertNotIn("iw3_q_parse.cpp", jni)


if __name__ == "__main__":
    unittest.main()
