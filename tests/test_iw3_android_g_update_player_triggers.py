"""Regression tests for the authentic G_UpdatePlayerTriggers ARM64 frame provider."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from tools.iw3_android.prepare_real_engine_g_update_player_triggers import (
    DECLARATIONS,
    SIGNATURE,
    SOURCE,
    prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]


class OriginalGUpdatePlayerTriggersExtractionTests(unittest.TestCase):
    def test_original_body_and_engine_declarations_are_preserved(self):
        engine = ROOT / "third_party/KisakCOD"
        source_path = engine / SOURCE
        original = source_path.read_bytes()
        body = function_source(original.decode("utf-8"), SIGNATURE)

        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_g_update_player_triggers.cpp"
            report_path = Path(temp) / "iw3-original-g-update-player-triggers.json"
            report = prepare(engine, output, report_path)
            generated = output.read_text(encoding="utf-8")
            saved_report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(source_path.read_bytes(), original)
        self.assertIn(body, generated)
        self.assertEqual(generated.count(SIGNATURE), 1)
        self.assertEqual(
            report["function_body_sha256"],
            hashlib.sha256(body.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            report["source_sha256"],
            hashlib.sha256(original).hexdigest(),
        )
        self.assertEqual(saved_report, report)
        self.assertTrue(report["original_G_UpdatePlayerTriggers_body_preserved_verbatim"])
        self.assertTrue(report["actual_g_runframe_state_header_used"])
        self.assertEqual(len(report["external_declarations_verified_against_original_headers"]), 7)
        self.assertFalse(report["sentient_path_and_trigger_services_are_stubs"])
        self.assertFalse(report["frame_edge_linked"])
        self.assertFalse(report["runtime_executed"])
        self.assertFalse(report["map_loaded"])
        self.assertFalse(report["gameplay_proven"])
        self.assertFalse(report["playable_apk"])
        for relative_path, declaration in DECLARATIONS:
            self.assertIn(declaration, (engine / relative_path).read_text(encoding="utf-8"))

    def test_slice_contains_trigger_update_not_player_packet_update(self):
        engine = ROOT / "third_party/KisakCOD"
        with TemporaryDirectory() as temp:
            output = Path(temp) / "provider.cpp"
            report = prepare(engine, output)
            generated = output.read_text(encoding="utf-8")
        self.assertEqual(generated.count(SIGNATURE), 1)
        self.assertIn("Sentient_NearestNodeDirty(ent->sentient, v3 == 0)", generated)
        self.assertIn("G_DoTouchTriggers(ent);", generated)
        self.assertNotIn("CL_WritePacket();", generated)
        self.assertNotIn("void __cdecl G_UpdatePlayer(gentity_s *ent)", generated)
        self.assertFalse(report["playable_apk"])

    def test_generator_refuses_to_overwrite_original_engine_source(self):
        engine = ROOT / "third_party/KisakCOD"
        with self.assertRaises(ValueError):
            prepare(engine, engine / SOURCE)

    def test_generator_rejects_missing_original_source(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises((FileNotFoundError, OSError)):
                prepare(Path(temp), Path(temp) / "missing.cpp")


if __name__ == "__main__":
    unittest.main()
