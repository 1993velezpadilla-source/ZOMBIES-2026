"""Tests for the disposable SP archive staging filter with tiny fake ZIP files."""
import io
import json
import tempfile
from pathlib import Path
import unittest
import zipfile

from tools.zombies_offline.stage_sp_data import PREFIX, REQUIRED_SP, stage_from_reader


def make_archive(items):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, body in items.items():
            z.writestr(PREFIX + name, body)
    out.seek(0)
    return out


class OfflineSPStageTests(unittest.TestCase):
    def test_stages_only_known_sp_files_and_never_executables(self):
        items = {p: b"TEST_DATA:" + p.encode() for p in REQUIRED_SP}
        items["iw3sp.exe"] = b"not allowed"
        items["private/config.ini"] = b"not allowed"
        items["zone/spanish/mp_crash.ff"] = b"MP map not requested"
        archive = make_archive(items)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = stage_from_reader(archive, root)
            self.assertEqual(report["file_count"], len(REQUIRED_SP))
            self.assertEqual(report["test_level"], "killhouse")
            self.assertFalse((root / "iw3sp.exe").exists())
            self.assertFalse((root / "zone/spanish/mp_crash.ff").exists())
            self.assertTrue((root / "zone/spanish/killhouse.ff").is_file())
            self.assertFalse(report["gameplay_verified"])
            self.assertFalse(report["first_zombie_verified"])
            self.assertFalse(report["game_data_in_artifacts"])
            self.assertEqual({p["path"] for p in report["files"]}, set(REQUIRED_SP))

    def test_missing_level_fails_closed(self):
        items = {p: b"x" for p in REQUIRED_SP if not p.endswith("killhouse.ff")}
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Missing required SP data"):
                stage_from_reader(make_archive(items), Path(tmp))

    def test_path_traversal_and_extensions_rejected(self):
        items = {p: b"x" for p in REQUIRED_SP}
        items["../evil.exe"] = b"bad"
        items["iw3sp.exe"] = b"do not stage"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Unsafe/duplicate"):
                stage_from_reader(make_archive(items), Path(tmp),
                                  required=("../evil.exe",))
            with self.assertRaisesRegex(ValueError, "Unsafe/duplicate"):
                stage_from_reader(make_archive(items), Path(tmp),
                                  required=("iw3sp.exe",))  # present, but forbidden


if __name__ == '__main__':
    unittest.main()
