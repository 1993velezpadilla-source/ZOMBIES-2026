"""Regression tests for original IW3 aim-assist tweakable providers."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source
from tools.iw3_android.prepare_real_engine_aimassist_tweakable_providers import (
    DVAR_NAMES, FUNCTIONS, SOURCE, prepare,
)

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalAimAssistTweakableProviderTests(unittest.TestCase):
    def test_original_bodies_and_dvar_state_are_staged_verbatim(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        bodies = [function_source(source, signature) for signature, _ in FUNCTIONS]
        lines = source.splitlines()
        dvar_lines = {
            name: next(line for line in lines if name in line and "= nullptr;" in line)
            for name in DVAR_NAMES
        }

        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "iw3_aimassist_tweakables.cpp"
            report_path = Path(temp) / "evidence.json"
            report = prepare(ENGINE, output, report_path)
            staged = output.read_text(encoding="utf-8")
            for body in bodies:
                self.assertIn(body, staged)
            for line in dvar_lines.values():
                self.assertIn(line, staged)
            self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
            self.assertTrue(report["source_unchanged"])
            self.assertEqual(
                report["resolved_original_client_edges"],
                ["AimAssist_UpdateTweakables", "AimAssist_UpdateAdsLerp"],
            )
            self.assertFalse(report["aimassist_dvars_registered_at_runtime"])
            self.assertFalse(report["cgame_state_initialized"])
            self.assertFalse(report["client_runtime_linked"])
            self.assertFalse(report["runtime_invoked"])
            self.assertFalse(report["real_map_loaded"])
            self.assertFalse(report["renderer_verified"])
            self.assertFalse(report["gameplay_proven"])
            self.assertFalse(report["playable_apk"])
            self.assertIn('"playable_apk": false', report_path.read_text(encoding="utf-8"))

        self.assertEqual(source_path.read_bytes(), original)

    def test_aa_glob_array_is_referenced_from_the_shared_original_state(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_aimassist_tweakables.cpp"
            report = prepare(ENGINE, output)
            staged = output.read_text(encoding="utf-8")
            self.assertIn("extern AimAssistGlobals aaGlobArray[1];", staged)
            self.assertNotIn("AimAssistGlobals aaGlobArray[1] = { 0 };", staged)
            self.assertTrue(report["aaGlobArray_declared_external"])
            self.assertTrue(report["aaGlobArray_definition_owned_by_client_state_provider"])

        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("grep -F 'aaGlobArray' \"$RUNNER_TEMP/iw3-aimassist-tweakables-undefined.txt\"", workflow)
        self.assertIn("AimAssist_UpdateTweakables AimAssist_UpdateAdsLerp aaGlobArray", workflow)

    def test_generator_refuses_to_overwrite_vendored_engine_source(self):
        with self.assertRaises(ValueError):
            prepare(ENGINE, ENGINE / SOURCE)

    def test_remaining_melee_and_assert_services_are_not_stubbed(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_aimassist_tweakables.cpp"
            prepare(ENGINE, output)
            staged = output.read_text(encoding="utf-8")
            for marker in (
                "AimAssist_UpdateTweakables",
                "AimAssist_UpdateAdsLerp",
                "aim_slowdown_region_width = nullptr;",
            ):
                self.assertIn(marker, staged)
            self.assertNotIn("void __cdecl AimAssist_ApplyAutoMelee(", staged)
            self.assertNotIn("void __cdecl AimAssist_ApplyMeleeCharge(", staged)


if __name__ == "__main__":
    unittest.main()
