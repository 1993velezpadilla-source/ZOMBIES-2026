"""Safety tests for exact original COD4 .weapon stats."""
from pathlib import Path
import tempfile
import unittest

from read_original_weapon_defs import inspect, weapon_fields, read_number


def definition(**fields):
    raw = ["WEAPONFILE"]
    for key, value in fields.items():
        raw.extend([key, str(value)])
    return "\\".join(raw).encode("latin-1")


class OriginalWeaponDefinitionTests(unittest.TestCase):
    def test_reads_real_fields_without_guessing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "common_mp/weapons/m4_mp"
            path.parent.mkdir(parents=True)
            path.write_bytes(definition(
                clipSize=30, fireTime=0.075, reloadTime=2.1,
                reloadEmptyTime=2.8, damage=40, adsTransInTime=0.22))
            catalog = {"weapons": [
                {"id": f"weapon_{n}",
                 "source_weapon_candidates": ["m4_mp"] if n == 0
                 else [f"missing_{n}_mp"]}
                for n in range(28)]}
            report = inspect(root, catalog)
            self.assertEqual(report["weapon_defs_present"], 1)
            self.assertEqual(report["weapon_defs_with_required_timing_and_ammo"], 1)
            self.assertEqual(report["weapons"]["weapon_0"]["numeric"]["clipSize"], 30)
            self.assertEqual(report["weapons"]["weapon_0"]["numeric"]["fireTime"], 0.075)
            self.assertFalse(report["weapons"]["weapon_1"]["source_stats_valid"])

    def test_bad_float_is_absent_not_zero(self):
        self.assertIsNone(read_number({"fireTime": "not_a_number"}, "fireTime"))
        self.assertIsNone(read_number({}, "clipSize"))

    def test_empty_corrupt_source_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"broken"
            p.write_bytes(b"oops")
            with self.assertRaises(ValueError):
                weapon_fields(p)

    def test_no_inventory_guessing_if_source_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog = {"weapons": [{"id": str(n),
                        "source_weapon_candidates": [f"gun{n}_mp"]}
                        for n in range(28)]}
            result=inspect(Path(directory),catalog)
            self.assertEqual(result["weapon_defs_present"],0)
            self.assertEqual(result["weapon_defs_with_required_timing_and_ammo"],0)
            self.assertFalse(result["playable_arsenal_28"])


if __name__=="__main__":
    unittest.main()
