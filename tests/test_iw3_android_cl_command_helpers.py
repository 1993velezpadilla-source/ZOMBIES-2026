"""Regression coverage for staging the authentic SP client keyboard/button providers for ARM64."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalCLCommandHelpersTests(unittest.TestCase):
    def test_stages_sp_keymove_and_command_buttons_verbatim_without_mutating_upstream(self):
        source_path = ENGINE / "src/client/cl_input.cpp"
        original = source_path.read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_cl_command_helpers.cpp"
            report_path = Path(temp) / "evidence.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_cl_command_helpers.py"),
                 "--engine", str(ENGINE), "--output", str(output), "--report", str(report_path)],
                cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            staged = output.read_text(encoding="utf-8")
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(source_path.read_bytes(), original)

        self.assertIn('#include "client.h"', staged)
        self.assertIn('#include "cl_input.h"', staged)
        self.assertIn("#define KEY_FORWARD 2", staged)
        self.assertIn("#define KEY_SPRINT 27", staged)
        self.assertIn("#define BUTTON_ATTACK", staged)
        self.assertIn("#define BUTTON_LOC_SELECTING", staged)
        self.assertIn("static bool s_scriptWasNoProne;", staged)
        self.assertIn("static bool s_scriptSuppressCrouch;", staged)
        self.assertIn("void __cdecl CL_KeyMove(usercmd_s *cmd)", staged)
        self.assertIn("void __cdecl CL_UpdateCmdButton(int *cmdButtons, int kbButton, int buttonFlag)", staged)
        self.assertIn("void __cdecl CL_CmdButtons(usercmd_s *cmd)", staged)
        self.assertIn("CL_StanceButtonUpdate();", staged)
        self.assertIn("CL_AddCurrentStanceToCmd(cmd);", staged)
        self.assertIn("cmd->forwardmove = ClampChar(forward);", staged)
        self.assertIn("CL_UpdateCmdButton(&cmd->buttons, 14, BUTTON_ATTACK);", staged)
        self.assertIn("clients[0].snap.ps.pm_type == PM_NOCLIP", staged)
        self.assertNotIn("#include <win32/win_local.h>", staged)
        self.assertNotIn("#include <cgame/cg_main.h>", staged)
        self.assertTrue(report["sp_branch_selected"])
        self.assertTrue(report["original_key_button_macros_preserved_verbatim"])
        self.assertTrue(report["original_sp_stance_state_preserved_verbatim"])
        self.assertTrue(report["original_bodies_preserved_verbatim"])
        self.assertFalse(report["key_move_and_cmd_buttons_linked_to_client_chain"])
        self.assertFalse(report["client_runtime_linked"])
        self.assertFalse(report["client_runtime_invoked"])
        self.assertFalse(report["playable_apk"])

    def test_generator_refuses_to_overwrite_vendored_cl_input(self):
        source_path = ENGINE / "src/client/cl_input.cpp"
        original = source_path.read_bytes()
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_cl_command_helpers.py"),
             "--engine", str(ENGINE), "--output", str(source_path),
             "--report", str(ROOT / "build/should-not-be-written-cl-command-helpers.json")],
            cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to overwrite authentic KisakCOD cl_input.cpp",
                      result.stdout + result.stderr)
        self.assertEqual(source_path.read_bytes(), original)

    def test_arm64_workflow_compiles_and_combines_real_helpers_without_claiming_runtime(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("prepare_real_engine_cl_command_helpers.py", workflow)
        self.assertIn("Cross-compile original CL_KeyMove and CL_CmdButtons (NOT RUNTIME)", workflow)
        self.assertIn("iw3-original-client-input-touch-and-keyboard-arm64.o", workflow)
        self.assertIn("CL_KeyMove(usercmd_s*)", workflow)
        self.assertIn("CL_CmdButtons(usercmd_s*)", workflow)
        self.assertIn("IW3_ORIGINAL_CL_KEYMOVE_CMDBUTTONS_EDGE_RESOLVED_AARCH64_GREEN", workflow)
        self.assertIn("IW3_CLIENT_COMMAND_RUNTIME_INVOKED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)


if __name__ == "__main__":
    unittest.main()
