"""Verify bounded real usercmd attack injection, never call combat directly."""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import unittest

from tools.zombies_offline.instrument_sp_input import SOURCE, apply

ROOT = Path(__file__).resolve().parents[1]
VENDORED = ROOT / "third_party/KisakCOD"
PROBE = ROOT / "tools/zombies_offline/probe_sp_runtime.ps1"

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
            self.assertTrue(report["aims_at_existing_damageable_actor"])
            self.assertEqual(report["aim_commands_limited_to"], 12)
            self.assertFalse(report["injects_actor_or_damage"])
            self.assertFalse(report["fireweapon_called_directly"])
            self.assertFalse(report["multiplayer_auth_changed"])
            patched = path.read_text(encoding="utf-8")
            self.assertIn("#include <game/g_level.h>", patched)
            self.assertIn("clients[0].snap.ps.weapon > 0", patched)
            self.assertIn("result->buttons |= BUTTON_ATTACK", patched)
            self.assertIn("z2026_test_attack_cmds < 12", patched)
            self.assertIn("#if defined(KISAK_SP)", patched)
            self.assertIn('Z2026_TestInputTrace("TEST_ATTACK_BUTTON_INJECTED")', patched)
            self.assertIn('Z2026_TestInputTrace("TEST_AIMED_AT_EXISTING_ACTOR")', patched)
            self.assertIn("z2026_candidate->actor", patched)
            self.assertIn("z2026_candidate->takedamage", patched)
            self.assertIn("z2026_test_aim_cmds < 12", patched)
            self.assertIn("std::atan2", patched)
            # CL_FinishMove packs client angles and the authoritative server
            # adds snapshot delta_angles; the probe must compensate before pack.
            self.assertIn("z2026_target_pitch - clients[0].snap.ps.delta_angles[0]", patched)
            self.assertIn("z2026_target_yaw - clients[0].snap.ps.delta_angles[1]", patched)
            self.assertIn("clients[0].viewangles[2] = -clients[0].snap.ps.delta_angles[2];", patched)
            self.assertIn("CL_FinishMove(result);", patched)
            self.assertNotIn("FireWeapon(", patched)
            self.assertNotIn("G_Damage(", patched)
            with self.assertRaisesRegex(ValueError, "already applied"):
                apply(copy)
        self.assertEqual((VENDORED / SOURCE).read_bytes(), before)

    def test_runtime_report_does_not_confuse_aim_with_damage(self):
        report = PROBE.read_text(encoding="utf-8")
        self.assertIn("test_aimed_at_existing_actor", report)
        self.assertIn("aimed_weapon_damage_verified", report)
        self.assertIn("$report.actor_damage_callback", report)
        self.assertIn("$report.actor_death_verified=$report.actor_death_callback", report)
        self.assertIn("Attack is injected by instrument_sp_input.py for at most 12 real usercmds.", report)
        self.assertNotIn("+map killhouse +attack", report)

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
