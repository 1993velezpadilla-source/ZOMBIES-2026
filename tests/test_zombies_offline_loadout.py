"""Validation of test-only native SP loadout injection in a disposable clone."""
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.zombies_offline.instrument_sp_level import instrument as level_instrument
from tools.zombies_offline.instrument_sp_combat import FILES, prepare as combat_instrument
from tools.zombies_offline.instrument_sp_loadout import apply, MAIN

ROOT = Path(__file__).resolve().parents[1]
VENDORED = ROOT / "third_party/KisakCOD"


class SPTestLoadoutTests(unittest.TestCase):
    def _clone_minimum(self, root):
        for name in set(FILES.values()) | {Path("src/game/g_main.cpp")}:
            dest = root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(VENDORED / name, dest)
        level_instrument(root)
        combat_instrument(root)

    def test_uses_real_registered_bullet_apis_only(self):
        before = (VENDORED / MAIN).read_bytes()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._clone_minimum(root)
            result = apply(root)
            self.assertTrue(result["test_weapon_grant_injected"])
            self.assertFalse(result["forged_fire_or_damage"])
            self.assertFalse(result["altered_mp_auth"])
            data = (root / MAIN).read_text(encoding="utf-8")
            for marker in (
                "TEST_LOADOUT_BOOTSTRAP_BEGIN",
                "TEST_REGISTERED_BULLET_WEAPON_FOUND",
                "TEST_WEAPON_GRANTED", "TEST_AMMO_INITIALIZED",
                "TEST_WEAPON_SWITCH_REQUESTED", "TEST_NO_VALID_REGISTERED_BULLET_WEAPON"
            ):
                self.assertIn(marker, data)
            self.assertIn("BG_GetNumWeapons()", data)
            self.assertIn("BG_GetWeaponDef(z2026_i)", data)
            self.assertIn("BG_CanPlayerHaveWeapon(z2026_i)", data)
            self.assertIn("G_GivePlayerWeapon(", data)
            self.assertIn("InitializeAmmo(", data)
            self.assertIn("G_SelectWeaponIndex(", data)
            self.assertIn("!level.initializing", data)
            self.assertIn("!level.clientIsSpawning", data)
            with self.assertRaisesRegex(ValueError, "already installed"):
                apply(root)
        self.assertEqual(before, (VENDORED / MAIN).read_bytes())

    def test_refuses_uninstrumented_or_vendored_tree(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / MAIN
            path.parent.mkdir(parents=True)
            path.write_text("int main() { return 0; }", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing prior SP"):
                apply(root)
        with self.assertRaisesRegex(ValueError, "Refusing edits"):
            apply(VENDORED)


if __name__ == "__main__":
    unittest.main()
