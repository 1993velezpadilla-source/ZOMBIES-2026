"""Regression tests for the authentic ClientEndFrame ARM64 frame-edge provider."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from tools.iw3_android.prepare_real_engine_client_end_frame import (
    DECLARATIONS,
    SIGNATURE,
    SOURCE,
    prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalClientEndFrameExtractionTests(unittest.TestCase):
    def test_original_client_end_frame_body_and_declarations_are_preserved(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        body = function_source(source, SIGNATURE)

        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_client_end_frame.cpp"
            report_path = Path(temp) / "iw3-original-client-end-frame.json"
            report = prepare(ENGINE, output, report_path)
            generated = output.read_text(encoding="utf-8")
            saved_report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(source_path.read_bytes(), original)
        self.assertIn(body, generated)
        self.assertEqual(generated.count(SIGNATURE), 1)
        self.assertEqual(
            report["function_body_sha256"],
            hashlib.sha256(body.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(
            report["generated_sha256"],
            hashlib.sha256(generated.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(saved_report, report)
        self.assertTrue(report["original_ClientEndFrame_body_preserved_verbatim"])
        self.assertTrue(report["level_global_declaration_verified_against_original_g_main_h"])
        self.assertEqual(len(report["external_declarations_verified_against_original_headers"]), len(DECLARATIONS))
        self.assertFalse(report["client_end_frame_service_stubs_added"])
        self.assertFalse(report["frame_edge_linked"])
        self.assertFalse(report["runtime_executed"])
        self.assertFalse(report["real_map_loaded"])
        self.assertFalse(report["gameplay_proven"])
        self.assertFalse(report["playable_apk"])

        for relative_path, declaration in DECLARATIONS:
            self.assertIn(declaration, (ENGINE / relative_path).read_text(encoding="utf-8"))

    def test_source_slice_contains_client_end_frame_calls_only(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "provider.cpp"
            report = prepare(ENGINE, output)
            generated = output.read_text(encoding="utf-8")
        for marker in (
            "turret_think_client(&level.gentities[ent->client->ps.viewlocked_entNum]);",
            "G_SetPlayerFixedLink(ent);",
            "G_UpdateGroundTilt(ent->client);",
            "Sentient_UpdateActualChainPos(ent->sentient);",
            "Player_UpdateLookAtEntity(ent);",
            "Player_UpdateCursorHints(ent);",
            "P_DamageFeedback(ent);",
            "G_PlayerStateToEntityStateExtrapolate(&v8->ps, &ent->s, v8->ps.commandTime, 1);",
        ):
            self.assertIn(marker, generated)
        self.assertNotIn("void __cdecl ClientThink(", generated)
        self.assertNotIn("void __cdecl G_UpdatePlayer(", generated)
        self.assertFalse(report["playable_apk"])

    def test_generator_refuses_to_overwrite_original_engine_source(self):
        with self.assertRaises(ValueError):
            prepare(ENGINE, ENGINE / SOURCE)

    def test_generator_rejects_missing_original_source(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises((FileNotFoundError, OSError)):
                prepare(Path(temp) / "missing-engine", Path(temp) / "missing.cpp")


if __name__ == "__main__":
    unittest.main()
