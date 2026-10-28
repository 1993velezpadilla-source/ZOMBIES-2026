from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.iw3_android.prepare_g_runframe_prereqs import function_source
from tools.iw3_android.prepare_real_engine_q_shared_strings import (
    FUNCTIONS,
    prepare,
)

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalQSharedStringServicesTests(unittest.TestCase):
    def test_original_string_helpers_are_staged_and_com_sprintf_is_ported_safely(self):
        source_path = ENGINE / "src/universal/q_shared.cpp"
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        with TemporaryDirectory() as temp:
            output = Path(temp) / "stage" / "iw3_q_shared_strings.cpp"
            report_path = Path(temp) / "iw3-original-q-shared-strings.json"
            report = prepare(ENGINE, output, report_path)
            staged = output.read_text(encoding="utf-8")
            saved_report = json.loads(report_path.read_text(encoding="utf-8"))

            for signature in FUNCTIONS[:-1]:
                self.assertIn(function_source(source, signature), staged)
            self.assertIn("std::vsnprintf(dest, static_cast<std::size_t>(size), fmt, va)", staged)
            self.assertIn("if (size == 0) { va_end(va); return -1; }", staged)
            self.assertIn("if (result >= 0 && static_cast<uint32_t>(result) >= size) result = -1;", staged)
            self.assertIn("dest[size - 1] = 0;", staged)
            self.assertNotIn("_vsnprintf(", staged)
            self.assertTrue(report["original_I_strncat_I_strncpyz_I_stricmp_bodies_staged_verbatim"])
            self.assertTrue(report["com_sprintf_minus_one_on_truncation_preserved"])
            self.assertFalse(report["filesystem_startup_invoked"])
            self.assertFalse(report["playable_apk"])
            self.assertEqual(report, saved_report)

        self.assertEqual(source_path.read_bytes(), original)

    def test_native_workflow_and_cmake_include_services_only_in_audit(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        gradle = (ROOT / "android/iw3-native/android_app/app/build.gradle").read_text(encoding="utf-8")

        self.assertIn("prepare_real_engine_q_shared_strings.py", workflow)
        self.assertIn("IW3_EXTRACTED_Q_SHARED_STRINGS", workflow)
        self.assertGreaterEqual(workflow.count("-DIW3_EXTRACTED_Q_SHARED_STRINGS="), 2)
        self.assertIn("libiw3_sp_q_shared_strings.a", workflow)
        self.assertIn("Com_sprintf(", workflow)
        self.assertIn("iw3_sp_q_shared_strings", cmake)
        self.assertIn("q_shared_strings_native_test.cpp", cmake)
        self.assertIn("IW3_EXTRACTED_Q_SHARED_STRINGS", cmake)
        self.assertNotIn("IW3_EXTRACTED_Q_SHARED_STRINGS", gradle)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)


if __name__ == "__main__":
    unittest.main()
