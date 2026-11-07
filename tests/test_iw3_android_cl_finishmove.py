"""Regression coverage for the original CL_FinishMove ARM64 dependency edge."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalCLFinishMoveTests(unittest.TestCase):
    def test_stages_verbatim_original_command_finalizer(self):
        source_path = ENGINE / "src/client/cl_input.cpp"
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_cl_finishmove.cpp"
            report_path = Path(temp) / "evidence.json"
            original = source_path.read_bytes()
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_cl_finishmove.py"),
                 "--engine", str(ENGINE), "--output", str(output), "--report", str(report_path)],
                cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            staged = output.read_text(encoding="utf-8")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(source_path.read_bytes(), original)

        required = (
            "cmd->weapon = clients[0].cgameUserCmdWeapon;",
            "cmd->offHandIndex = clients[0].cgameUserCmdOffHandIndex;",
            "cmd->serverTime = clients[0].serverTime;",
            "cmd->angles[KEY_FORWARD] =",
            "cmd->buttons = buttons | clients[0].cgameExtraButtons;",
            "clients[0].cgameExtraButtons = 0;",
            "if (clients[0].bCmdForceValues)",
            "clients[0].bCmdForceValues = 0;",
        )
        for marker in required:
            self.assertIn(marker, staged)
        self.assertTrue(report["original_CL_FinishMove_body_preserved_verbatim"])
        self.assertTrue(report["weapon_offhand_server_time_and_viewangles_copied"])
        self.assertTrue(report["extra_buttons_cleared_after_merge"])
        self.assertTrue(report["forced_command_values_cleared_after_use"])
        self.assertTrue(report["key_forward_constant_preserved_from_original_source"])
        self.assertFalse(report["client_runtime_linked"])
        self.assertFalse(report["client_runtime_invoked"])
        self.assertFalse(report["playable_apk"])

    def test_generator_refuses_to_overwrite_the_vendored_engine_source(self):
        source_path = ENGINE / "src/client/cl_input.cpp"
        original = source_path.read_bytes()
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_cl_finishmove.py"),
             "--engine", str(ENGINE), "--output", str(source_path),
             "--report", str(ROOT / "build/should-not-be-written-finishmove.json")],
            cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to overwrite authentic KisakCOD cl_input.cpp",
                      result.stdout + result.stderr)
        self.assertEqual(source_path.read_bytes(), original)

    def test_arm64_workflow_resolves_only_the_finishmove_edge(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("prepare_real_engine_cl_finishmove.py", workflow)
        self.assertIn("iw3-original-cl-finishmove-arm64.o", workflow)
        self.assertIn("IW3_ORIGINAL_CL_FINISHMOVE_EDGE_RESOLVED_AARCH64_GREEN", workflow)
        self.assertIn("IW3_CLIENT_RUNTIME_LINKED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)
        self.assertIn("CL_FinishMove(usercmd_s*)", workflow)


if __name__ == "__main__":
    unittest.main()
