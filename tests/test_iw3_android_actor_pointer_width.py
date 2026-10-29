"""Regression tests for native pointer-width fixes in original IW3 actor code."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from tools.iw3_android.prepare_real_engine_actor_pointer_width import (
    SIGNATURES, SOURCE, prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalActorPointerWidthTests(unittest.TestCase):
    def test_extracted_original_routines_are_verbatim_and_hashed(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        expected = {sig: function_source(source, sig) for sig in SIGNATURES}
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_actor_pointer_width.cpp"
            report_path = Path(temp) / "iw3-actor-pointer-width.json"
            report = prepare(ENGINE, output, report_path)
            generated = output.read_text(encoding="utf-8")
            saved = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(source_path.read_bytes(), original)
        for sig, body in expected.items():
            self.assertIn(body, generated)
            self.assertEqual(generated.count(sig), 1)
            self.assertEqual(report["function_body_sha256"][sig],
                             hashlib.sha256(body.encode("utf-8")).hexdigest())
        self.assertEqual(saved, report)
        self.assertTrue(report["original_function_bodies_preserved_verbatim"])
        self.assertFalse(report["service_stubs_added"])
        self.assertFalse(report["runtime_executed"])
        self.assertFalse(report["map_loaded"])
        self.assertFalse(report["gameplay_proven"])
        self.assertFalse(report["playable_apk"])

    def test_sentient_info_clear_clears_complete_native_record(self):
        source = (ENGINE / SOURCE).read_text(encoding="utf-8")
        body = function_source(source, SIGNATURES[0])
        self.assertIn("memset(pInfo, 0, sizeof(*pInfo));", body)
        self.assertNotIn("(char *)v2 + 4", body)
        self.assertNotIn("v3 = 10", body)

    def test_known_enemy_region_uses_typed_sentient_info(self):
        source = (ENGINE / SOURCE).read_text(encoding="utf-8")
        body = function_source(source, SIGNATURES[1])
        self.assertIn("info = &self->sentientInfo[v9];", body)
        self.assertIn("v12 = info->lastKnownPosTime;", body)
        self.assertIn("i = info->vLastKnownPos;", body)
        self.assertNotIn("i += 10", body)
        self.assertNotIn("*((unsigned int *)i - 2)", body)

    def test_actor_goal_copy_copies_native_pointer_members(self):
        source = (ENGINE / SOURCE).read_text(encoding="utf-8")
        body = function_source(source, "int __cdecl SP_actor(gentity_s *ent)")
        self.assertIn("v3->codeGoal = v3->scriptGoal;", body)
        self.assertNotIn("(char *)p_scriptGoal + 4", body)
        self.assertNotIn("(char *)p_codeGoal + 4", body)
        nav = (ENGINE / "src/game/actor_navigation.h").read_text(encoding="utf-8")
        for field in ("float pos[3];", "float radius;", "float height;",
                      "pathnode_t *node;", "gentity_s *volume;"):
            self.assertIn(field, nav)

    def test_32bit_actor_layout_assertions_are_not_applied_to_arm64(self):
        header = (ENGINE / "src/game/actor.h").read_text(encoding="utf-8")
        self.assertIn("sizeof(void *) != 4 || sizeof(actor_s) == 0x1e90", header)
        self.assertIn("sizeof(void *) != 4 || offsetof(actor_s, sentientInfo) == 0x834", header)
        self.assertIn("sizeof(sentient_info_t) == (sizeof(void *) == 8 ? 0x30 : 0x28)", header)

    def test_generator_refuses_to_overwrite_original_source(self):
        with self.assertRaises(ValueError):
            prepare(ENGINE, ENGINE / SOURCE)

    def test_workflow_compiles_real_actor_routines_for_arm64_without_claiming_runtime(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("prepare_real_engine_actor_pointer_width.py", workflow)
        self.assertIn("IW3_ORIGINAL_ACTOR_POINTER_WIDTH_AARCH64_COMPILE_GREEN", workflow)
        self.assertIn("IW3_ACTOR_RUNTIME_EXECUTED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)


if __name__ == "__main__":
    unittest.main()
