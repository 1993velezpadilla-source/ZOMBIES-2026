"""Regression checks for staging the authentic IW3 FS_Read implementation."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_fs_read import (
    SOURCE, SIGNATURE, FUNCTIONS, REQUIRED, PROLOGUE, prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalFSReadStageTests(unittest.TestCase):
    def test_exact_original_read_body_is_staged_without_claiming_runtime(self):
        original = (ENGINE / SOURCE).read_bytes()
        bodies = [function_source(original.decode("utf-8"), signature) for signature in FUNCTIONS]
        body = bodies[-1]
        combined = "\n\n".join(bodies)
        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "iw3_fs_read.cpp"
            report_path = Path(temp) / "evidence.json"
            report = prepare(ENGINE, output, report_path)
            staged = output.read_text(encoding="utf-8")
            self.assertEqual(staged, PROLOGUE + combined + "\n")
            self.assertTrue(report["original_FS_CheckFileSystemStarted_body_preserved_exactly"])
            self.assertTrue(report["original_FS_FileForHandle_body_preserved_exactly"])
            self.assertTrue(report["original_FS_Read_body_preserved_exactly"])
            self.assertTrue(report["uses_original_zip_read_and_original_file_read_branches"])
            self.assertFalse(report["original_upstream_fsh_table_integrated"])
            self.assertTrue(report["android_native_width_fsh_table_adapter_required"])
            self.assertFalse(report["open_close_lifecycle_integrated"])
            self.assertFalse(report["gameplay_proven"])
            self.assertFalse(report["playable_apk"])
            self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
            for marker in REQUIRED:
                self.assertIn(marker, combined)
        self.assertEqual((ENGINE / SOURCE).read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
