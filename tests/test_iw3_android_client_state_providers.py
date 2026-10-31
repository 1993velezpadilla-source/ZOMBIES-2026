"""Regression tests for authentic IW3 aim-assist and predicted-state providers."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source
from tools.iw3_android.prepare_real_engine_client_state_providers import (
    AIM_GLOBAL, AIM_SIGNATURE, AIM_SOURCE, CG_GLOBAL, CG_SIGNATURE, CG_SOURCE,
    prepare,
)

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalClientStateProviderTests(unittest.TestCase):
    def test_original_bodies_and_state_globals_are_staged_verbatim(self):
        aim_path = ENGINE / AIM_SOURCE
        cg_path = ENGINE / CG_SOURCE
        aim_bytes = aim_path.read_bytes()
        cg_bytes = cg_path.read_bytes()
        aim_text = aim_bytes.decode("utf-8")
        cg_text = cg_bytes.decode("utf-8")
        aim_body = function_source(aim_text, AIM_SIGNATURE)
        cg_body = function_source(cg_text, CG_SIGNATURE)

        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "iw3_client_state_providers.cpp"
            report_path = Path(temp) / "evidence.json"
            report = prepare(ENGINE, output, report_path)
            staged = output.read_text(encoding="utf-8")
            for original in (aim_body, cg_body):
                self.assertIn(original, staged)
            self.assertIn(AIM_GLOBAL, staged)
            self.assertIn(CG_GLOBAL, staged)
            self.assertEqual(report["aim_source_sha256"], hashlib.sha256(aim_bytes).hexdigest())
            self.assertEqual(report["cg_source_sha256"], hashlib.sha256(cg_bytes).hexdigest())
            self.assertTrue(report["original_AimAssist_UpdateMouseInput_body_preserved_verbatim"])
            self.assertTrue(report["original_CG_GetPredictedPlayerState_body_preserved_verbatim"])
            self.assertTrue(report["original_aaGlobArray_definition_preserved"])
            self.assertTrue(report["original_cgArray_definition_preserved"])
            self.assertTrue(report["source_files_unchanged"])
            self.assertFalse(report["client_state_runtime_initialized"])
            self.assertFalse(report["client_input_runtime_linked"])
            self.assertFalse(report["runtime_invoked"])
            self.assertFalse(report["real_map_loaded"])
            self.assertFalse(report["renderer_verified"])
            self.assertFalse(report["gameplay_proven"])
            self.assertFalse(report["playable_apk"])
            saved = report_path.read_text(encoding="utf-8")
            self.assertIn('"playable_apk": false', saved)

        self.assertEqual(aim_path.read_bytes(), aim_bytes)
        self.assertEqual(cg_path.read_bytes(), cg_bytes)

    def test_generator_refuses_to_overwrite_upstream_sources(self):
        for source in (AIM_SOURCE, CG_SOURCE):
            with self.subTest(source=source), TemporaryDirectory() as temp:
                with self.assertRaises(ValueError):
                    prepare(ENGINE, ENGINE / source)

    def test_generated_provider_keeps_real_aimassist_helpers_visible(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_client_state_providers.cpp"
            prepare(ENGINE, output)
            source = output.read_text(encoding="utf-8")
            for symbol in (
                "AimAssist_UpdateTweakables(input);",
                "AimAssist_UpdateAdsLerp(input);",
                "AimAssist_ApplyAutoMelee(input, output);",
                "AimAssist_ApplyMeleeCharge(input, output);",
                "MyAssertHandler(",
            ):
                self.assertIn(symbol, source)


if __name__ == "__main__":
    unittest.main()
