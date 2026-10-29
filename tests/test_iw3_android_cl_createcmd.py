"""Regression tests for the original CL_CreateCmd Android touch hook."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalCLCreateCmdTests(unittest.TestCase):
    def test_stages_verbatim_original_command_builder_and_touch_order(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_cl_createcmd.cpp"
            report_path = Path(temp) / "evidence.json"
            original = (ENGINE / "src/client/cl_input.cpp").read_bytes()
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_cl_createcmd.py"),
                 "--engine", str(ENGINE), "--output", str(output), "--report", str(report_path)],
                cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            staged = output.read_text(encoding="utf-8")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual((ENGINE / "src/client/cl_input.cpp").read_bytes(), original)

        mouse = staged.index("CL_MouseMove(result);")
        touch = staged.index("z2026_platform_apply_touch_to_usercmd(result, clients[0].viewangles);")
        finish = staged.index("CL_FinishMove(result);")
        self.assertLess(mouse, touch)
        self.assertLess(touch, finish)
        self.assertEqual(staged.count("z2026_platform_apply_touch_to_usercmd(result, clients[0].viewangles);"), 1)
        self.assertTrue(report["original_CL_CreateCmd_body_preserved_verbatim"])
        self.assertTrue(report["touch_hook_after_CL_MouseMove"])
        self.assertTrue(report["touch_hook_before_CL_FinishMove"])
        self.assertFalse(report["client_runtime_linked"])
        self.assertFalse(report["client_runtime_invoked"])
        self.assertFalse(report["playable_apk"])

    def test_android_client_header_does_not_force_win32_d3d_resource_layouts(self):
        header = (ENGINE / "src/client/client.h").read_text(encoding="utf-8")
        self.assertIn("#if !defined(__ANDROID__)\\n#include <gfx_d3d/r_debug.h>", header)
        self.assertIn("struct Material;", header)
        self.assertIn("struct Font_s;", header)
        self.assertIn("struct refdef_s;", header)

    def test_arm64_workflow_compiles_and_audits_the_original_command_builder(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("prepare_real_engine_cl_createcmd.py", workflow)
        self.assertIn("aarch64-linux-android26-clang++", workflow)
        self.assertIn("IW3_ORIGINAL_CL_CREATECMD_TOUCH_HOOK_AARCH64_COMPILE_GREEN", workflow)
        self.assertIn("IW3_CL_CREATECMD_RUNTIME_INVOKED=false", workflow)
        self.assertIn("iw3-original-cl-createcmd-arm64.o", workflow)


if __name__ == "__main__":
    unittest.main()
