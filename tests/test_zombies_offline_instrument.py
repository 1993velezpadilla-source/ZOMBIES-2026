"""Minimal mutation and marker sanity checks against the real SP game source."""
import shutil
import tempfile
from pathlib import Path
import unittest

from tools.zombies_offline.instrument_sp_level import GAME_FILE, FRAME_FILE, instrument

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "third_party/KisakCOD" / GAME_FILE


class OfflineSPInstrumentationTests(unittest.TestCase):
    def test_stage_markers_only_in_temp_game_source(self):
        before = UPSTREAM.read_bytes()
        with tempfile.TemporaryDirectory() as root:
            copy = Path(root) / GAME_FILE
            copy.parent.mkdir(parents=True)
            shutil.copyfile(UPSTREAM, copy)
            shutil.copyfile(ROOT / "third_party/KisakCOD" / FRAME_FILE, Path(root) / FRAME_FILE)
            report = instrument(Path(root))
            self.assertEqual(report["stage_markers"], [
                "G_INIT_ENTER", "G_SPAWN_ENTITIES_RETURN", "G_FRAME_ENTER"])
            code = copy.read_text(encoding="utf-8")
            self.assertIn('Z2026_SPTrace("G_INIT_ENTER");', code)
            self.assertIn('Z2026_SPTrace("G_SPAWN_ENTITIES_RETURN");', code)
            self.assertIn('Z2026_SPTrace("G_FRAME_ENTER");', (Path(root) / FRAME_FILE).read_text())
            self.assertIn('std::fopen("z2026-sp-level-trace.txt", "a")', code)
            self.assertIn('#include <cstdio>', code)
            with self.assertRaises(ValueError):
                instrument(Path(root))
        self.assertEqual(before, UPSTREAM.read_bytes())

    def test_fail_closed_on_unrecognized_engine(self):
        with tempfile.TemporaryDirectory() as root:
            file = Path(root) / GAME_FILE
            file.parent.mkdir(parents=True)
            file.write_text("void unrelated() {}\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                instrument(Path(root))


if __name__ == "__main__":
    unittest.main()
