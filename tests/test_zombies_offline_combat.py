"""Tests use real SP sources in disposable temp, no assets or login."""
import shutil
import tempfile
from pathlib import Path
import unittest

from tools.zombies_offline.instrument_sp_level import instrument
from tools.zombies_offline.instrument_sp_combat import FILES, prepare

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD"


class SPCombatInstrumentationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.copy = Path(self.temp.name)
        for file in FILES.values():
            output = self.copy / file
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / file, output)

    def test_callbacks_are_passive_and_marker_once(self):
        before = {key: (SOURCE / file).read_bytes()
                  for key, file in FILES.items()}
        instrument(self.copy)
        result = prepare(self.copy)
        self.assertFalse(result["injected_shots"])
        self.assertFalse(result["injected_enemies"])
        self.assertFalse(result["multiplayer_auth_changed"])
        self.assertEqual(result["files_instrumented"],
                         ["weapon", "actor", "combat", "main"])
        for key, file in FILES.items():
            modified = (self.copy / file).read_text(encoding="utf-8")
            self.assertIn("Z2026_", modified)
            self.assertEqual((SOURCE / file).read_bytes(), before[key])
        self.assertIn("BULLET_FIRE_DISPATCH",
                      (self.copy / FILES["weapon"]).read_text(encoding="utf-8"))
        self.assertIn('g_entities[0].client->ps.weapon > 0',
                      (self.copy / FILES["main"]).read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "Already instrumented"):
            prepare(self.copy)

    def test_does_not_allow_combat_hooks_without_level_instrumentation(self):
        with self.assertRaisesRegex(ValueError, "Run instrument_sp_level"):
            prepare(self.copy)

    def test_malformed_weapon_callback_fails_before_writing_anything(self):
        instrument(self.copy)
        path = self.copy / FILES["weapon"]
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("void __cdecl FireWeapon(",
                                     "void __cdecl WeaponDoesNotExist("),
                        encoding="utf-8")
        prior = {key: (self.copy / file).read_bytes()
                 for key, file in FILES.items()}
        with self.assertRaisesRegex(ValueError, "anchor"):
            prepare(self.copy)
        for key, file in FILES.items():
            self.assertEqual((self.copy / file).read_bytes(), prior[key])


if __name__ == "__main__":
    unittest.main()
