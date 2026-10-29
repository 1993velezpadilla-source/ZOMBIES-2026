"""Regression tests for the original mover collision trace edge."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from tools.iw3_android.prepare_real_engine_mover_trace_services import (
    GAME_SOURCE,
    G_TRACE_SIGNATURE,
    TRACE_HIT_ID_SIGNATURE,
    TRACE_SOURCE,
    SV_SETUP_SIGNATURE,
    SV_TRACE_SIGNATURE,
    WORLD_SOURCE,
    prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalMoverTraceServiceTests(unittest.TestCase):
    def test_original_trace_bodies_are_preserved_and_hashed(self):
        game_path = ENGINE / GAME_SOURCE
        trace_path = ENGINE / TRACE_SOURCE
        game_bytes = game_path.read_bytes()
        trace_bytes = trace_path.read_bytes()
        world_path = ENGINE / WORLD_SOURCE
        world_bytes = world_path.read_bytes()
        world_source = world_bytes.decode("utf-8")
        g_trace = function_source(game_bytes.decode("utf-8"), G_TRACE_SIGNATURE)
        hit_id = function_source(trace_bytes.decode("utf-8"), TRACE_HIT_ID_SIGNATURE)
        setup_body = function_source(world_source, SV_SETUP_SIGNATURE)
        sv_trace_body = function_source(world_source, SV_TRACE_SIGNATURE)

        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_mover_trace_services.cpp"
            report_path = Path(temp) / "iw3-mover-trace-services.json"
            report = prepare(ENGINE, output, report_path)
            generated = output.read_text(encoding="utf-8")
            saved_report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(game_path.read_bytes(), game_bytes)
        self.assertEqual(trace_path.read_bytes(), trace_bytes)
        self.assertEqual(world_path.read_bytes(), world_bytes)
        self.assertIn(g_trace, generated)
        self.assertIn(hit_id, generated)
        self.assertIn(setup_body, generated)
        self.assertIn(sv_trace_body, generated)
        self.assertEqual(generated.count(G_TRACE_SIGNATURE), 1)
        self.assertEqual(generated.count(TRACE_HIT_ID_SIGNATURE), 1)
        self.assertEqual(generated.count(SV_SETUP_SIGNATURE), 1)
        self.assertEqual(generated.count(SV_TRACE_SIGNATURE), 1)
        self.assertEqual(report["SV_SetupIgnoreEntParams_body_sha256"],
                         hashlib.sha256(setup_body.encode("utf-8")).hexdigest())
        self.assertEqual(report["SV_Trace_body_sha256"],
                         hashlib.sha256(sv_trace_body.encode("utf-8")).hexdigest())
        self.assertTrue(report["original_server_trace_body_preserved_verbatim"])
        self.assertTrue(report["original_sv_gentitynum_declaration_verified"])
        self.assertTrue(report["SV_Trace_definition_extracted"])
        self.assertEqual(report["G_TraceCapsule_body_sha256"],
                         hashlib.sha256(g_trace.encode("utf-8")).hexdigest())
        self.assertEqual(report["Trace_GetEntityHitId_body_sha256"],
                         hashlib.sha256(hit_id.encode("utf-8")).hexdigest())
        self.assertEqual(saved_report, report)
        self.assertTrue(report["original_function_bodies_preserved_verbatim"])
        self.assertFalse(report["service_stubs_added"])
        self.assertFalse(report["SV_Trace_runtime_linked"])
        self.assertFalse(report["runtime_executed"])
        self.assertFalse(report["map_loaded"])
        self.assertFalse(report["gameplay_proven"])
        self.assertFalse(report["playable_apk"])

    def test_g_trace_capsule_keeps_original_world_trace_call_order(self):
        source = (ENGINE / GAME_SOURCE).read_text(encoding="utf-8")
        body = function_source(source, G_TRACE_SIGNATURE)
        self.assertLess(
            body.index("SV_SetupIgnoreEntParams(&ignoreEntParams, passEntityNum);"),
            body.index("SV_Trace(results, start, mins, maxs, end, &ignoreEntParams, contentmask, 0, 0, 0);"),
        )

    def test_trace_hit_id_preserves_entity_and_dynent_semantics(self):
        source = (ENGINE / TRACE_SOURCE).read_text(encoding="utf-8")
        body = function_source(source, TRACE_HIT_ID_SIGNATURE)
        self.assertIn("TRACE_HITTYPE_DYNENT_MODEL", body)
        self.assertIn("TRACE_HITTYPE_DYNENT_BRUSH", body)
        self.assertIn("return ENTITYNUM_WORLD;", body)
        self.assertIn("return trace->hitId;", body)
        self.assertIn("return ENTITYNUM_NONE;", body)

    def test_world_services_are_verified_but_not_stubbed(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_mover_trace_services.cpp"
            report = prepare(ENGINE, output)
            generated = output.read_text(encoding="utf-8")
        self.assertIn("#include <server/sv_world.h>", generated)
        self.assertIn("#include <universal/com_math.h>", generated)
        self.assertIn("SV_SetupIgnoreEntParams", generated)
        self.assertIn("SV_Trace(", generated)
        self.assertIn("CM_BoxTrace(results, start, end, mins, maxs, 0, contentmask);", generated)
        self.assertIn("CM_PointTraceToEntities(&clip, results);", generated)
        self.assertIn("CM_ClipMoveToEntities(&result, results);", generated)
        self.assertTrue(report["original_world_service_declarations_verified"])
        self.assertFalse(report["service_stubs_added"])

    def test_generator_refuses_to_overwrite_upstream_files(self):
        with self.assertRaises(ValueError):
            prepare(ENGINE, ENGINE / GAME_SOURCE)
        with self.assertRaises(ValueError):
            prepare(ENGINE, ENGINE / TRACE_SOURCE)
        with self.assertRaises(ValueError):
            prepare(ENGINE, ENGINE / WORLD_SOURCE)

    def test_generator_rejects_missing_engine_source(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises((FileNotFoundError, OSError)):
                prepare(Path(temp), Path(temp) / "out.cpp")

    def test_original_trace_edge_workflow_is_not_a_game_claim(self):
        workflow_path = ROOT / ".github/workflows/iw3-mover-trace-services-arm64.yml"
        if workflow_path.exists():
            workflow = workflow_path.read_text(encoding="utf-8")
            self.assertIn("IW3_ORIGINAL_MOVER_TRACE_EDGE_AARCH64_RESOLVED_GREEN", workflow)
            self.assertIn("IW3_MOVER_TRACE_RUNTIME_EXECUTED=false", workflow)
            self.assertIn("IW3_PLAYABLE_APK=false", workflow)


if __name__ == "__main__":
    unittest.main()
