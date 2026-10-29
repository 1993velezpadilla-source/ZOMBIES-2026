"""Regression tests for the original G_MoverTeam provider and native pushed state."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from tools.iw3_android.prepare_real_engine_g_mover_team import (
    GLOBAL_DECLARATIONS, SOURCE, TEAM_SIGNATURE, TRACK_SIGNATURE, prepare, struct_source,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalGMoverTeamTests(unittest.TestCase):
    def test_original_team_body_and_pushed_struct_are_preserved_and_hashed(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        body = function_source(source, TEAM_SIGNATURE)
        struct = struct_source(source, "struct pushed_t")
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_g_mover_team.cpp"
            report_path = Path(temp) / "iw3-g-mover-team.json"
            report = prepare(ENGINE, output, report_path)
            generated = output.read_text(encoding="utf-8")
            saved = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(source_path.read_bytes(), original)
        self.assertIn(body, generated)
        self.assertIn(struct, generated)
        self.assertEqual(generated.count(TEAM_SIGNATURE), 1)
        self.assertEqual(report["G_MoverTeam_body_sha256"],
                         hashlib.sha256(body.encode("utf-8")).hexdigest())
        self.assertEqual(report["pushed_t_struct_sha256"],
                         hashlib.sha256(struct.encode("utf-8")).hexdigest())
        self.assertEqual(saved, report)
        self.assertTrue(report["original_G_MoverTeam_body_preserved_verbatim"])
        self.assertFalse(report["service_stubs_added"])
        self.assertFalse(report["runtime_executed"])
        self.assertFalse(report["map_loaded"])
        self.assertFalse(report["gameplay_proven"])
        self.assertFalse(report["playable_apk"])

    def test_tracker_uses_native_array_size_not_win32_byte_constant(self):
        source = (ENGINE / SOURCE).read_text(encoding="utf-8")
        tracker = function_source(source, TRACK_SIGNATURE)
        self.assertIn('track_static_alloc_internal(pushed, sizeof(pushed), "pushed", 9);', tracker)
        self.assertNotIn('track_static_alloc_internal(pushed, 45056, "pushed", 9);', tracker)

    def test_pushed_state_declarations_are_unique_and_layout_is_native_width(self):
        source = (ENGINE / SOURCE).read_text(encoding="utf-8")
        for declaration in GLOBAL_DECLARATIONS:
            self.assertEqual(source.count(declaration), 1)
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_g_mover_team.cpp"
            report = prepare(ENGINE, output)
            generated = output.read_text(encoding="utf-8")
        self.assertIn("sizeof(pushed_t) == (sizeof(void *) == 8 ? 0x30 : 0x2C)", generated)
        self.assertTrue(report["pushed_tracker_uses_native_sizeof"])
        self.assertTrue(report["pushed_array_and_cursor_owned_once"])

    def test_sp_actor_path_and_sentient_invalidation_remain_original(self):
        source = (ENGINE / SOURCE).read_text(encoding="utf-8")
        body = function_source(source, TEAM_SIGNATURE)
        self.assertIn("Actor_ClearPath(p->ent->actor);", body)
        self.assertIn("Sentient_InvalidateNearestNode(p->ent->actor->sentient);", body)
        self.assertIn("G_MoverPush(ent, move, amove, &obstacle)", body)

    def test_workflow_compiles_and_resolves_only_the_mover_team_edge(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("prepare_real_engine_g_mover_team.py", workflow)
        self.assertIn("IW3_ORIGINAL_G_MOVER_TEAM_AARCH64_FRAME_EDGE_RESOLVED_GREEN", workflow)
        self.assertIn("IW3_G_MOVER_TEAM_RUNTIME_EXECUTED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)

    def test_generator_refuses_to_overwrite_original_source(self):
        with self.assertRaises(ValueError):
            prepare(ENGINE, ENGINE / SOURCE)


if __name__ == "__main__":
    unittest.main()
