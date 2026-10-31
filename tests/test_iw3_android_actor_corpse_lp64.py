"""Regression tests for pointer-width-safe original IW3 actor-corpse indexing."""
from pathlib import Path
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"
SOURCE = ENGINE / "src/game/actor_corpse.cpp"
HEADER = ENGINE / "src/game/g_scr_main.h"


class OriginalActorCorpseLp64Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def test_corpse_index_uses_the_declared_array_bound_not_truncated_pointers(self):
        body = function_source(
            self.source,
            "int __cdecl G_GetActorCorpseIndex(gentity_s *ent)",
        )
        self.assertIn("ARRAY_COUNT(g_scr_data.actorCorpseInfo)", body)
        self.assertIn("g_scr_data.actorCorpseInfo[result].entnum", body)
        self.assertNotIn("p_entnum", body)
        self.assertNotIn("(int)&g_scr_data.actorBackup", body)

    def test_prune_scan_uses_the_same_fixed_array_bound(self):
        body = function_source(
            self.source,
            "void __cdecl G_PruneLoadedCorpses()",
        )
        self.assertIn("v3 < ARRAY_COUNT(g_scr_data.actorCorpseInfo)", body)
        self.assertIn("g_scr_data.actorCorpseInfo[v3].entnum", body)
        self.assertNotIn("p_entnum", body)
        self.assertNotIn("(int)&g_scr_data.actorBackup", body)

    def test_original_actor_corpse_capacity_is_sixteen(self):
        self.assertIn("corpseInfo_t actorCorpseInfo[16];", self.header)

    def test_original_corpse_count_dvar_and_removal_path_remain_intact(self):
        body = function_source(
            self.source,
            "void __cdecl G_UpdateActorCorpses()",
        )
        self.assertIn("ai_corpseCount->current.integer", body)
        self.assertIn("G_RemoveActorCorpses(integer);", body)
        self.assertNotIn("return;", body)


if __name__ == "__main__":
    unittest.main()
