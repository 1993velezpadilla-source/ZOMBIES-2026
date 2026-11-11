"""Regression tests for authentic IW3 auto-melee providers staged for ARM64."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source
from tools.iw3_android.prepare_real_engine_aimassist_melee_providers import (
    DVAR_NAMES, FUNCTIONS, SOURCE, prepare,
)

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalAimAssistMeleeProviderTests(unittest.TestCase):
    def test_original_bodies_and_dvar_lines_are_preserved_verbatim(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        bodies = [function_source(source, signature) for signature, _ in FUNCTIONS]
        lines = source.splitlines()
        dvar_lines = {
            name: next(
                line for line in lines
                if name in line and "= nullptr;" in line
            )
            for name in DVAR_NAMES
        }

        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "iw3_aimassist_melee.cpp"
            report_path = Path(temp) / "evidence.json"
            report = prepare(ENGINE, output, report_path)
            staged = output.read_text(encoding="utf-8")
            for body in bodies:
                self.assertIn(body, staged)
            for line in dvar_lines.values():
                self.assertIn(line, staged)
            self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
            self.assertTrue(report["source_unchanged"])
            self.assertEqual(len(report["resolved_original_aimassist_edges"]), len(FUNCTIONS))
            self.assertFalse(report["dvars_registered_at_runtime"])
            self.assertFalse(report["cgame_state_initialized"])
            self.assertFalse(report["client_runtime_linked"])
            self.assertFalse(report["runtime_invoked"])
            self.assertFalse(report["real_map_loaded"])
            self.assertFalse(report["renderer_verified"])
            self.assertFalse(report["gameplay_proven"])
            self.assertFalse(report["playable_apk"])
            self.assertIn('"playable_apk": false', report_path.read_text(encoding="utf-8"))

        self.assertEqual(source_path.read_bytes(), original)

    def test_auto_melee_providers_reference_shared_state_not_duplicate_it(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_aimassist_melee.cpp"
            report = prepare(ENGINE, output)
            staged = output.read_text(encoding="utf-8")
            self.assertIn("extern AimAssistGlobals aaGlobArray[1];", staged)
            self.assertIn("extern const dvar_t *player_meleeRange;", staged)
            self.assertNotIn("AimAssistGlobals aaGlobArray[1] = { 0 };", staged)
            self.assertTrue(report["player_meleeRange_is_external_engine_dependency"])
            for symbol in (
                "AimAssist_ApplyAutoMelee",
                "AimAssist_ApplyMeleeCharge",
                "AimAssist_GetBestTarget",
                "AimAssist_UpdateAutoMeleeTarget",
            ):
                self.assertIn(symbol, staged)

        workflow = (
            ROOT / ".github/workflows/iw3-original-native-android.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("prepare_real_engine_aimassist_melee_providers.py", workflow)
        self.assertIn("IW3_ORIGINAL_CLIENT_AIMASSIST_MELEE_EDGE_RESOLVED_AARCH64_GREEN", workflow)

    def test_generator_refuses_to_overwrite_original_engine_source(self):
        with self.assertRaises(ValueError):
            prepare(ENGINE, ENGINE / SOURCE)

    def test_no_fake_runtime_or_melee_stubs_are_emitted(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_aimassist_melee.cpp"
            report = prepare(ENGINE, output)
            staged = output.read_text(encoding="utf-8")
            self.assertIn("AimAssist_ApplyAutoMelee", staged)
            self.assertIn("AimAssist_ApplyMeleeCharge", staged)
            self.assertNotIn("void __cdecl AimAssist_ApplyAutoMelee() {}", staged)
            self.assertNotIn("void __cdecl AimAssist_ApplyMeleeCharge() {}", staged)
            self.assertFalse(report["playable_apk"])
            self.assertFalse(report["gameplay_proven"])


if __name__ == "__main__":
    unittest.main()
