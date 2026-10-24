"""Weapon definition metadata contract. No game assets are read."""
from pathlib import Path
import unittest
from tools.zombies_offline.weapon_schema_export import parse_weapon_schema

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/bgame/bg_weapons_load_obj.cpp"

class WeaponSchemaTests(unittest.TestCase):
    def test_exact_unmodified_engine_schema(self):
        report = parse_weapon_schema(SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(report["field_count"], 502)
        self.assertEqual(report["unique_names"], 501)
        self.assertEqual(report["duplicate_names_in_upstream_source"], ["guidedMissileType"])
        names = {r["name"] for r in report["fields"]}
        for required in ("fireTime", "damage", "clipSize", "adsTransInTime",
                         "adsTransOutTime", "reloadTime", "reloadEmptyTime",
                         "fireAnim", "adsFireAnim", "handModel"):
            self.assertIn(required, names)
        self.assertEqual(report["weapon_stats_or_models"], "NOT_INCLUDED")
        self.assertFalse(report["runtime_weapon_files_loaded"])

    def test_rejects_partial_or_unrelated_source(self):
        with self.assertRaises(ValueError):
            parse_weapon_schema("void main() {}")
        text = SOURCE.read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Incomplete weapon schema"):
            parse_weapon_schema(text.replace('"displayName", 4, CSPFT_STRING',
                                             '"noDisplay", invalid, CSPFT_STRING', 1))


if __name__ == "__main__":
    unittest.main()
