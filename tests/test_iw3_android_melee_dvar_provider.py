"""Verify the original BGame melee dvar provider is extracted and ARM64-audited."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/iw3_android/prepare_real_engine_melee_dvar_services.py"
SOURCE = ROOT / "third_party/KisakCOD/src/bgame/bg_misc.cpp"


class OriginalMeleeDvarProviderTests(unittest.TestCase):
    def test_exact_original_globals_and_registration_blocks_are_staged(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_melee_dvars.cpp"
            report_path = Path(temp) / "report.json"
            result = subprocess.run(
                [
                    sys.executable, str(TOOL),
                    "--engine", str(ROOT / "third_party/KisakCOD"),
                    "--output", str(output),
                    "--report", str(report_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            generated = output.read_text(encoding="utf-8")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            original = SOURCE.read_text(encoding="utf-8")

            for name in (
                "player_meleeRange",
                "player_meleeWidth",
                "player_meleeHeight",
                "player_meleeChargeFriction",
            ):
                self.assertIn(f"const dvar_t *{name};", generated)
                self.assertIn(f"{name} = Dvar_RegisterFloat(", generated)
                self.assertIn(f"const dvar_t *{name};", original)

            self.assertIn('"player_meleeRange"', generated)
            self.assertIn("64.0f", generated)
            self.assertIn('"player_meleeWidth"', generated)
            self.assertIn('"player_meleeHeight"', generated)
            self.assertIn('"player_meleeChargeFriction"', generated)
            self.assertEqual(
                report["original_registration_blocks_preserved_verbatim"],
                ["player_meleeRange", "player_meleeWidth", "player_meleeHeight", "player_meleeChargeFriction"],
            )
            self.assertTrue(report["source_unchanged"])
            self.assertFalse(report["runtime_invoked"])
            self.assertFalse(report["dvars_registered_at_runtime"])
            self.assertFalse(report["playable_apk"])

    def test_arm64_gate_links_melee_dvar_globals_without_hiding_dvar_runtime(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("Stage original BGame melee dvars and resolve client aim-assist range (NOT RUNTIME)", workflow)
        self.assertIn("prepare_real_engine_melee_dvar_services.py", workflow)
        self.assertIn("IW3_ORIGINAL_BGAME_MELEE_DVAR_PROVIDER_EDGE_RESOLVED_AARCH64_GREEN", workflow)
        self.assertIn("Dvar_RegisterFloat", workflow)
        self.assertIn("IW3_BG_REGISTER_DVARS_RUNTIME_INVOKED=false", workflow)
        self.assertIn("IW3_MELEE_DVARS_REGISTERED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)


if __name__ == "__main__":
    unittest.main()
