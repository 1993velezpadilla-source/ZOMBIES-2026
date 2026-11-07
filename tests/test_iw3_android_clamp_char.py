"""Regression coverage for staging and linking the original KisakCOD ClampChar provider."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"
SOURCE = ENGINE / "src/universal/com_math.cpp"
SIGNATURE = "signed char ClampChar(int i)"


class OriginalClampCharTests(unittest.TestCase):
    def test_stages_original_clampchar_body_verbatim_without_mutating_upstream(self):
        from tools.iw3_android.prepare_g_runframe_prereqs import function_source

        original = SOURCE.read_bytes()
        source_text = original.decode("utf-8")
        expected_body = function_source(source_text, SIGNATURE)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_clamp_char.cpp"
            report_path = Path(temp) / "evidence.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_clamp_char.py"),
                 "--engine", str(ENGINE), "--output", str(output), "--report", str(report_path)],
                cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            staged = output.read_text(encoding="utf-8")
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(SOURCE.read_bytes(), original)
        self.assertEqual(staged, "#include <universal/com_math.h>" + chr(10) + chr(10) + expected_body + chr(10))
        self.assertIn("if (i < -128)", staged)
        self.assertIn("return -128;", staged)
        self.assertIn("if (i > 127)", staged)
        self.assertIn("return 127;", staged)
        self.assertIn("return i;", staged)
        self.assertTrue(report["original_ClampChar_body_preserved_verbatim"])
        self.assertTrue(report["clamps_to_signed_char_min_minus_128"])
        self.assertTrue(report["clamps_to_signed_char_max_127"])
        self.assertFalse(report["client_runtime_linked"])
        self.assertFalse(report["client_runtime_invoked"])
        self.assertFalse(report["playable_apk"])

    def test_generator_refuses_to_overwrite_upstream_com_math(self):
        original = SOURCE.read_bytes()
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_clamp_char.py"),
             "--engine", str(ENGINE), "--output", str(SOURCE),
             "--report", str(ROOT / "build/should-not-be-written-clamp-char.json")],
            cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to overwrite authentic KisakCOD com_math.cpp",
                      result.stdout + result.stderr)
        self.assertEqual(SOURCE.read_bytes(), original)

    def test_workflow_compiles_and_requires_original_clampchar_resolution(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        helpers = (ROOT / "tools/iw3_android/prepare_real_engine_cl_command_helpers.py").read_text(encoding="utf-8")
        self.assertIn("#include <universal/com_math.h>", helpers)
        self.assertIn("prepare_real_engine_clamp_char.py", workflow)
        self.assertIn('grep -F \'ClampChar(int)\'', workflow)
        self.assertIn("'ClampChar(int)'", workflow)
        self.assertIn("IW3_ORIGINAL_CLAMPCHAR_PROVIDER_EDGE_RESOLVED_AARCH64_GREEN", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)


if __name__ == "__main__":
    unittest.main()
