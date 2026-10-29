"""Regression coverage for the authentic CL_MouseMove ARM64 dependency edges."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalCLMouseMoveTests(unittest.TestCase):
    def test_stages_both_original_mouse_functions_without_mutating_source(self):
        source_path = ENGINE / "src/client/cl_input.cpp"
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_cl_mousemove.cpp"
            report_path = Path(temp) / "evidence.json"
            original = source_path.read_bytes()
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_cl_mousemove.py"),
                 "--engine", str(ENGINE), "--output", str(output), "--report", str(report_path)],
                cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            staged = output.read_text(encoding="utf-8")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(source_path.read_bytes(), original)

        self.assertIn("void __cdecl CL_GetMouseMovement(clientActive_t *cl, float *mx, float *my)", staged)
        self.assertIn("void __cdecl CL_MouseMove(usercmd_s *cmd)", staged)
        self.assertIn("AimAssist_UpdateMouseInput(&aimInput, &aimOutput);", staged)
        self.assertIn("CG_GetPredictedPlayerState(0)", staged)
        self.assertIn("#define KEY_STRAFE 8", staged)
        self.assertIn("#define KEY_MLOOK 13", staged)
        self.assertNotIn("#include <win32/win_local.h>", staged)
        self.assertTrue(report["original_CL_GetMouseMovement_body_preserved_verbatim"])
        self.assertTrue(report["original_CL_MouseMove_body_preserved_verbatim"])
        self.assertTrue(report["win32_input_header_excluded"])
        self.assertFalse(report["client_runtime_linked"])
        self.assertFalse(report["client_runtime_invoked"])
        self.assertFalse(report["playable_apk"])

    def test_generator_refuses_to_overwrite_the_vendored_engine_source(self):
        source_path = ENGINE / "src/client/cl_input.cpp"
        original = source_path.read_bytes()
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_cl_mousemove.py"),
             "--engine", str(ENGINE), "--output", str(source_path),
             "--report", str(ROOT / "build/should-not-be-written-mousemove.json")],
            cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to overwrite authentic KisakCOD cl_input.cpp",
                      result.stdout + result.stderr)
        self.assertEqual(source_path.read_bytes(), original)

    def test_arm64_workflow_links_mousemove_and_helper_without_claiming_runtime(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("prepare_real_engine_cl_mousemove.py", workflow)
        self.assertIn("iw3-original-cl-mousemove-arm64.o", workflow)
        self.assertIn("IW3_ORIGINAL_CL_MOUSEMOVE_EDGE_RESOLVED_AARCH64_GREEN", workflow)
        self.assertIn("CL_MouseMove(usercmd_s*)", workflow)
        self.assertIn("CL_GetMouseMovement(clientActive_t*, float*, float*)", workflow)
        self.assertIn("IW3_CLIENT_RUNTIME_LINKED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)


if __name__ == "__main__":
    unittest.main()
