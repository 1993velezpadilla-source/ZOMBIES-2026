"""Regression tests for preserving the authentic IW3 file-handle lifecycle."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_iwd_read import (
    SOURCE, FUNCTIONS, REQUIRED, prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalIWDReadLifecycleTests(unittest.TestCase):
    def test_original_open_read_close_and_handle_allocator_are_staged_exactly(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        bodies = [function_source(source, signature) for signature in FUNCTIONS]

        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "iw3_iwd_read_lifecycle.cpp"
            report_path = Path(temp) / "evidence.json"
            report = prepare(ENGINE, output, report_path)
            staged = output.read_text(encoding="utf-8")
            for body in bodies:
                self.assertIn(body, staged)
            self.assertTrue(staged.startswith("// AUDIT ARTIFACT: exact original KisakCOD function bodies."))
            self.assertTrue(report["original_handle_allocation_body_staged_verbatim"])
            self.assertTrue(report["original_FS_FOpenFileReadForThread_body_staged_verbatim"])
            self.assertTrue(report["original_FS_Read_body_staged_verbatim"])
            self.assertTrue(report["original_FS_FCloseFile_body_staged_verbatim"])
            self.assertFalse(report["android_abi_and_service_linkage_proven"])
            self.assertFalse(report["runtime_handle_path_executed"])
            self.assertFalse(report["real_game_assets_loaded"])
            self.assertFalse(report["gameplay_proven"])
            self.assertFalse(report["playable_apk"])
            self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
            for marker in REQUIRED:
                self.assertIn(marker, staged)
        self.assertEqual(source_path.read_bytes(), original)

    def test_original_lifecycle_keeps_zip_clone_and_disk_read_paths(self):
        source = (ENGINE / SOURCE).read_text(encoding="utf-8")
        combined = "\\n".join(function_source(source, signature) for signature in FUNCTIONS)
        for marker in (
            "unzReOpen(iwd->iwdFilename, iwd->handle)",
            "unzOpenCurrentFile(fsh[*file].handleFiles.file.z)",
            "unzReadCurrentFile(fsh[h].handleFiles.file.z, buffer, len)",
            "FS_FileRead(buf, remaining, f)",
            "unzCloseCurrentFile(fsh[h].handleFiles.file.z)",
            "fsh[h].handleFiles.iwdIsClone",
        ):
            self.assertIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
