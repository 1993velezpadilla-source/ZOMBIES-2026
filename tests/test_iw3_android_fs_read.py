"""Regression tests for compiling the authentic IW3 open/read/close lifecycle."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_fs_read import (
    SOURCE, SHARED_SOURCE, SIGNATURE, FUNCTIONS, REQUIRED, PROLOGUE, prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalFSReadStageTests(unittest.TestCase):
    def test_exact_original_open_read_close_bodies_are_staged(self):
        source_paths = {source_path for _, source_path in FUNCTIONS}
        originals = {source_path: (ENGINE / source_path).read_bytes()
                     for source_path in source_paths}
        texts = {source_path: raw.decode("utf-8")
                 for source_path, raw in originals.items()}
        bodies = [function_source(texts[source_path], signature)
                  for signature, source_path in FUNCTIONS]
        combined = "\n\n".join(bodies) + "\n"
        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "iw3_fs_read.cpp"
            report_path = Path(temp) / "evidence.json"
            report = prepare(ENGINE, output, report_path)
            staged = output.read_text(encoding="utf-8")
            self.assertEqual(staged, PROLOGUE + combined)
            self.assertTrue(report["original_handle_allocation_body_preserved_exactly"])
            self.assertTrue(report["original_FS_FOpenFileReadForThread_body_preserved_exactly"])
            self.assertTrue(report["original_FS_FileForHandle_body_preserved_exactly"])
            self.assertTrue(report["original_FS_Read_body_preserved_exactly"])
            self.assertTrue(report["original_FS_FCloseFile_body_preserved_exactly"])
            self.assertTrue(report["original_extension_and_purity_helpers_preserved_exactly"])
            self.assertTrue(report["full_open_read_close_lifecycle_integrated"])
            self.assertTrue(report["full_original_open_read_close_lifecycle_compiled_into_diagnostic"])
            self.assertFalse(report["runtime_handle_path_executed"])
            self.assertFalse(report["original_upstream_fsh_table_integrated"])
            self.assertTrue(report["android_native_width_fsh_table_adapter_required"])
            self.assertFalse(report["gameplay_proven"])
            self.assertFalse(report["playable_apk"])
            self.assertEqual(report["source_sha256"][str(SOURCE)],
                             hashlib.sha256(originals[SOURCE]).hexdigest())
            self.assertEqual(report["source_sha256"][str(SHARED_SOURCE)],
                             hashlib.sha256(originals[SHARED_SOURCE]).hexdigest())
            for marker in REQUIRED:
                self.assertIn(marker, combined)
        for source_path, original in originals.items():
            self.assertEqual((ENGINE / source_path).read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
