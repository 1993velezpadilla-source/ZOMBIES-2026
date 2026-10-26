"""Regression checks for staging the authentic IW3 FS_Read implementation."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_fs_read import (
    SOURCE, SIGNATURE, REQUIRED, prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalFSReadStageTests(unittest.TestCase):
    def test_exact_original_read_body_is_staged_without_claiming_runtime(self):
        original = (ENGINE / SOURCE).read_bytes()
        body = function_source(original.decode("utf-8"), SIGNATURE)
        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "iw3_fs_read.cpp"
            report_path = Path(temp) / "evidence.json"
            report = prepare(ENGINE, output, report_path)
            staged = output.read_text(encoding="utf-8")
            self.assertEqual(staged, '#include "iw3_android_fs_read_compat.h"\n' + body + "\n")
            self.assertTrue(report["original_FS_Read_body_preserved_exactly"])
            self.assertTrue(report["uses_original_zip_read_and_original_file_read_branches"])
            self.assertFalse(report["android_file_handle_table_integrated"])
            self.assertFalse(report["open_close_lifecycle_integrated"])
            self.assertFalse(report["gameplay_proven"])
            self.assertFalse(report["playable_apk"])
            self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
            for marker in REQUIRED:
                self.assertIn(marker, body)
        self.assertEqual((ENGINE / SOURCE).read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
