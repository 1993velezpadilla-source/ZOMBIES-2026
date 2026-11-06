"""Safe Windows MP-stage extractor tests using tiny original synthetic ZIP data."""
from __future__ import annotations
import io
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "iw3_rotu"))
from windows_mp_data_stage import PREFIX, stage_from_zip


class WindowsMpStageTests(unittest.TestCase):
    def make_fixture(self, tmp: Path, relatives: list[str]) -> Path:
        path=tmp / "part-000"
        with zipfile.ZipFile(path,"w") as z:
            for relative in relatives:
                z.writestr(PREFIX+relative,b"TEST - not commercial game content")
        return path

    def test_valid_entries_stage_and_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            zip_file=self.make_fixture(tmp,["localization.txt","main/iw_00.iwd","zone/spanish/mp_crash.ff"])
            report=stage_from_zip([zip_file], tmp/"out",
                required=("localization.txt","main/iw_00.iwd","zone/spanish/mp_crash.ff"))
            self.assertEqual(len(report["selected_files"]),3)
            self.assertFalse(report["gameplay_verified"])
            self.assertTrue((tmp/"out"/"main"/"iw_00.iwd").exists())
            self.assertEqual(report["selected_total_bytes"],3*len(b"TEST - not commercial game content"))

    def test_missing_required_fails_before_any_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            zip_file=self.make_fixture(tmp,["localization.txt"])
            with self.assertRaisesRegex(ValueError,"Missing required original MP files"):
                stage_from_zip([zip_file],tmp/"out",required=("main/iw_00.iwd",))
            self.assertFalse((tmp/"out"/"main").exists())

    def test_executable_or_traversal_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            for relative in ("main/evil.exe", "../outside.ff"):
                zip_file=self.make_fixture(tmp,[relative])
                with self.assertRaisesRegex(ValueError,"Refusing unsafe"):
                    stage_from_zip([zip_file],tmp/"out",required=(relative,))
            self.assertFalse((tmp/"outside.ff").exists())


if __name__=="__main__":
    unittest.main()
