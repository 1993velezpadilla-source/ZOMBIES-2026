"""Verify bounded real usercmd attack injection, never call combat directly."""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import unittest

from tools.zombies_offline.instrument_sp_input import SOURCE, apply

ROOT = Path(__file__).resolve().parents[1]
VENDORED = ROOT / "third_party/KisakCOD"

class OfflineSPInputTests(unittest.TestCase):
    def test_only_client_command_hook_in_temp_source(self):
        before = (VENDORED / SOURCE).read_bytes()
        with TemporaryDirectory() as tmp:
            copy = Path(tmp)
            path = copy / SOURCE
            path.parent.mkdir(parents=True)
            shutil.copyfile(VENDORED / SOURCE, path)
            report = apply(copy)
            self.assertTrue(report["test_only_input"])
            self.assertEqual(report["client_commands_limited_to"], 12)
            self.assertTrue(report["requires_player_snapshot_weapon"])
            self.assertFalse(report["fireweapon_called_directly"])
            self.assertFalse(report["multiplayer_auth_changed"])
            patched = path.read_text(encoding="utf-8")
            self.assertIn("clients[0].snap.ps.weapon > 0", patched)
            self.assertIn("result->buttons |= BUTTON_ATTACK", patched)
            self.assertIn("z2026_test_attack_cmds < 12", patched)
            self.assertIn("#if defined(KISAK_SP)", patched)
            self.assertIn('Z2026_TestInputTrace("TEST_ATTACK_BUTTON_INJECTED")', patched)
            self.assertNotIn("FireWeapon(", patched)
            self.assertNotIn("G_Damage(", patched)
            with self.assertRaisesRegex(ValueError, "already applied"):
                apply(copy)
        self.assertEqual((VENDORED / SOURCE).read_bytes(), before)

    def test_missing_original_symbol_fails_closed(self):
        with TemporaryDirectory() as tmp:
            copy = Path(tmp)
            path = copy / SOURCE
            path.parent.mkdir(parents=True)
            path.write_text("irrelevant source", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "input anchors"):
                apply(copy)

if __name__ == "__main__":
    unittest.main()
