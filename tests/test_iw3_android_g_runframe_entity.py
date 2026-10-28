"""Regression tests for original G_RunFrameForEntity ARM64 provider staging."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from tools.iw3_android.prepare_real_engine_g_runframe_entity import (
    DECLARATIONS,
    PROVIDER_DEFINITIONS,
    SIGNATURES,
    SOURCE,
    prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalGRunFrameForEntityExtractionTests(unittest.TestCase):
    def test_both_original_entity_frame_bodies_are_preserved_verbatim(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        expected_bodies = [function_source(source, signature) for signature in SIGNATURES]

        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_g_runframe_entity.cpp"
            report_path = Path(temp) / "iw3-original-g-runframe-entity.json"
            report = prepare(ENGINE, output, report_path)
            generated = output.read_text(encoding="utf-8")
            saved_report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(source_path.read_bytes(), original)
        for signature, body in zip(SIGNATURES, expected_bodies):
            self.assertIn(body, generated)
            self.assertEqual(generated.count(signature), 1)
            self.assertEqual(
                report["function_body_sha256"][signature],
                hashlib.sha256(body.encode("utf-8")).hexdigest(),
            )
        self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(report["generated_sha256"], hashlib.sha256(generated.encode("utf-8")).hexdigest())
        self.assertEqual(saved_report, report)
        self.assertTrue(report["original_G_RunFrameForEntity_bodies_preserved_verbatim"])
        self.assertTrue(report["actual_g_runframe_state_header_used"])
        self.assertTrue(report["complete_scr_vehicle_layout_header_used"])
        self.assertTrue(report["MAX_VEHICLES_verified_against_original_g_main_h"])
        self.assertFalse(report["gameplay_service_stubs_added"])
        self.assertFalse(report["frame_edge_linked"])
        self.assertFalse(report["runtime_executed"])
        self.assertFalse(report["map_loaded"])
        self.assertFalse(report["gameplay_proven"])
        self.assertFalse(report["playable_apk"])

    def test_original_entity_services_and_declarations_are_checked(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_g_runframe_entity_test.cpp"
            report = prepare(ENGINE, output)
            generated = output.read_text(encoding="utf-8")
        self.assertEqual(len(report["external_declarations_verified_against_original_headers"]), len(DECLARATIONS))
        self.assertEqual(len(report["original_entity_service_definitions_verified"]), len(PROVIDER_DEFINITIONS))
        for marker in (
            "G_RunMissile(ent);",
            "G_RunItem(v4);",
            "G_RunMover(ent);",
            "G_RunFrameForEntityInternal(ent);",
            "AimTarget_ProcessEntity(ent);",
            "G_DObjCalcPose(ent, partBits);",
            "SV_XModelDebugBoxes(ent);",
        ):
            self.assertIn(marker, generated)

    def test_generator_refuses_to_overwrite_original_engine_source(self):
        with self.assertRaises(ValueError):
            prepare(ENGINE, ENGINE / SOURCE)

    def test_generator_rejects_missing_original_source(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises((FileNotFoundError, OSError)):
                prepare(Path(temp), Path(temp) / "missing.cpp")


if __name__ == "__main__":
    unittest.main()
