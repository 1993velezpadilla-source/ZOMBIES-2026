"""Regression tests for the authentic G_RunMover ARM64 frame-edge pass."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from tools.iw3_android.prepare_real_engine_g_run_mover import (
    MOVER_TEAM_SIGNATURE,
    SIGNATURE,
    SOURCE,
    prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalGRunMoverExtractionTests(unittest.TestCase):
    def test_original_mover_body_is_verbatim_and_reported(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        expected = function_source(source, SIGNATURE)

        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_g_run_mover.cpp"
            report_path = Path(temp) / "iw3-original-g-run-mover.json"
            report = prepare(ENGINE, output, report_path)
            generated = output.read_text(encoding="utf-8")
            saved_report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(source_path.read_bytes(), original)
        self.assertIn(expected, generated)
        self.assertEqual(generated.count(SIGNATURE), 1)
        self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(report["function_body_sha256"], hashlib.sha256(expected.encode("utf-8")).hexdigest())
        self.assertEqual(report["generated_sha256"], hashlib.sha256(generated.encode("utf-8")).hexdigest())
        self.assertEqual(saved_report, report)
        self.assertTrue(report["original_G_RunMover_body_preserved_verbatim"])
        self.assertTrue(report["G_MoverTeam_original_definition_verified"])
        self.assertFalse(report["G_MoverTeam_body_included"])
        self.assertFalse(report["gameplay_service_stubs_added"])
        self.assertFalse(report["G_RunMover_frame_edge_linked"])
        self.assertFalse(report["runtime_executed"])
        self.assertFalse(report["map_loaded"])
        self.assertFalse(report["gameplay_proven"])
        self.assertFalse(report["playable_apk"])

    def test_real_mover_contract_and_unresolved_service_are_explicit(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_g_run_mover.cpp"
            report = prepare(ENGINE, output)
            generated = output.read_text(encoding="utf-8")
        for marker in (
            "G_Animscripted_Think(ent);",
            "G_SetOrigin(ent, ent->r.currentOrigin);",
            "G_SetAngle(ent, ent->r.currentAngles);",
            "G_MoverTeam(ent);",
            "G_RunThink(ent);",
            MOVER_TEAM_SIGNATURE,
        ):
            self.assertIn(marker, generated)
        self.assertTrue(report["G_MoverTeam_original_definition_verified"])

    def test_generated_mover_uses_narrow_portable_headers(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_g_run_mover.cpp"
            prepare(ENGINE, output)
            generated = output.read_text(encoding="utf-8")

        self.assertIn("#include <game/game_public.h>", generated)
        self.assertIn("#include <game/g_local.h>", generated)
        self.assertIn("void __cdecl SV_LinkEntity(gentity_s *gEnt);", generated)
        self.assertIn("void __cdecl G_MoverTeam(gentity_s *ent);", generated)
        for forbidden in (
            "#include <server/sv_game.h>",
            "#include <server/sv_public.h>",
            '#include "g_main.h"',
            '#include "actor.h"',
            '#include "actor_orientation.h"',
            '#include "sentient.h"',
        ):
            self.assertNotIn(forbidden, generated)

    def test_generator_refuses_to_overwrite_original_engine_source(self):
        with self.assertRaises(ValueError):
            prepare(ENGINE, ENGINE / SOURCE)

    def test_generator_rejects_missing_original_source(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises((FileNotFoundError, OSError)):
                prepare(Path(temp), Path(temp) / "missing.cpp")

    def test_arm64_workflow_compiles_and_links_mover_without_claiming_runtime(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("prepare_real_engine_g_run_mover.py", workflow)
        self.assertIn("IW3_ORIGINAL_G_RUNMOVER_AARCH64_FRAME_EDGE_RESOLVED_GREEN", workflow)
        self.assertIn("G_MoverTeam(gentity_s*)", workflow)
        self.assertIn("IW3_G_RUNMOVER_RUNTIME_EXECUTED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)


if __name__ == "__main__":
    unittest.main()
