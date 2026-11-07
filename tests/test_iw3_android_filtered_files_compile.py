"""Regression tests for compiling original IW3 filtered-file search bodies."""
from pathlib import Path
import json
import tempfile
import unittest

from tools.iw3_android.prepare_real_engine_filtered_files import (
    ALLOCATION,
    LIST_ALLOCATION,
    LIST_SIGNATURE,
    SIGNATURE,
    definition_source,
    prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalFilteredFilesCompileTests(unittest.TestCase):
    def test_generator_preserves_both_original_bodies_and_native_allocations(self):
        source = (ENGINE / "src/universal/com_files.cpp").read_text(encoding="utf-8")
        expected_location = function_source(source, SIGNATURE)
        expected_list = definition_source(source, LIST_SIGNATURE)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "filtered.cpp"
            report = Path(temp) / "report.json"
            evidence = prepare(ENGINE, output, report)
            rendered = output.read_text(encoding="utf-8")
            self.assertIn(expected_location, rendered)
            self.assertIn(expected_list, rendered)
            self.assertEqual(rendered.count(ALLOCATION), 2)
            self.assertEqual(rendered.count(LIST_ALLOCATION), 1)
            self.assertNotIn("Hunk_UserAlloc(user, 0x1Cu, 4)", rendered)
            self.assertNotIn("Hunk_UserAlloc(user, 0x1C, 4)", rendered)
            self.assertNotIn("Hunk_UserAlloc(user, 0x8004u, 4)", rendered)
            self.assertTrue(evidence["original_function_body_preserved_verbatim"])
            self.assertTrue(evidence["original_list_function_body_preserved_verbatim"])
            self.assertEqual(evidence["native_pointer_array_slots"], 8193)
            self.assertTrue(evidence["original_list_capacity_guard_preserved"])
            self.assertEqual(evidence["original_list_capacity_limit"], 0x1FFF)
            self.assertFalse(evidence["runtime_execution_proven"])
            self.assertFalse(evidence["playable_apk"])
            self.assertEqual(json.loads(report.read_text())["win32_fixed_size_allocations"], 0)

    def test_native_workflow_compiles_and_archives_both_original_functions(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("add_library(iw3_sp_filtered_files STATIC", cmake)
        self.assertIn("IW3_EXTRACTED_FILTERED_FILES", cmake)
        self.assertIn("prepare_real_engine_filtered_files.py", workflow)
        self.assertIn("libiw3_sp_filtered_files.a", workflow)
        self.assertIn("IW3_EXTRACTED_FILTERED_FILES", workflow)
        self.assertIn('grep -F "FS_ListFilteredFiles("', workflow)
        self.assertIn("FS_AddFileToList", workflow)
        self.assertIn("Sys_ListFiles", workflow)


if __name__ == "__main__":
    unittest.main()
