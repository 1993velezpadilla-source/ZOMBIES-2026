"""Standalone SP source tests: no COD4 game data, no Steam service, no MP join."""
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.zombies_offline.sp_source_gate import (
    COMMON, SP, SP_CMAKE, WEAPON_SOURCE, WINMAIN, prepare, inspect,
)

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "third_party/KisakCOD"


class OfflineSinglePlayerSourceTests(unittest.TestCase):
    def make_copy(self, root: Path):
        for path in (COMMON, SP, SP_CMAKE, WEAPON_SOURCE, WINMAIN):
            dest = root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(UPSTREAM / path, dest)
        (root / "CMakeLists.txt").write_text("project(KisakCOD)\n", encoding="utf-8")

    def test_only_disposable_sp_source_uses_steam_guard(self):
        orig = (UPSTREAM / WINMAIN).read_bytes()
        with TemporaryDirectory() as tmp:
            local = Path(tmp)
            self.make_copy(local)
            self.assertFalse(inspect(local)["single_player_source_gate"])
            report = prepare(local)
            self.assertTrue(report["single_player_source_gate"])
            self.assertTrue(all(report["checks"].values()))
            self.assertIn("adsTransInTime", report["weapon_fields_detected"])
            self.assertIn("reloadTime", report["weapon_fields_detected"])
            self.assertFalse(report["sp_executable_compiled"])
            self.assertFalse(report["zombie_gameplay_verified"])
            patched = (local / WINMAIN).read_text(encoding="utf-8")
            self.assertIn("#ifndef KISAK_SP\n\t\t\tSteam_Init();\n#endif", patched)
            self.assertIn("Steam_Init();", patched)
            with self.assertRaises(ValueError):
                prepare(local)
        self.assertEqual(orig, (UPSTREAM / WINMAIN).read_bytes())

    def test_missing_actor_source_fails_closed(self):
        with TemporaryDirectory() as tmp:
            local = Path(tmp)
            self.make_copy(local)
            file = local / SP
            file.write_text(file.read_text(encoding="utf-8").replace(
                '"${SRC_DIR}/game/actor_spawner.cpp"', '"${SRC_DIR}/game/missing_actor.cpp"'),
                encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source checks failed"):
                prepare(local)

    def test_no_game_data_is_read_by_gate(self):
        import inspect as pyinspect
        import tools.zombies_offline.sp_source_gate as module
        source = pyinspect.getsource(module)
        self.assertNotIn("Steam_UpdateClientAuthTicket(", source)
        self.assertNotIn("bypass auth", source.lower())
        self.assertFalse((ROOT / "tools/zombies_offline").joinpath("assets").exists())


if __name__ == "__main__":
    unittest.main()
