"""Regression tests for native-width allocations in original KisakCOD FS."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD/src/universal"


class OriginalFilesystemNativeAllocationTests(unittest.TestCase):
    def test_location_filter_allocates_searchpath_with_native_size_and_alignment(self):
        source = (ENGINE / "com_files.cpp").read_text(encoding="utf-8")
        start = source.index(
            "const char **__cdecl FS_ListFilteredFilesInLocation("
        )
        end = source.index("\n}\n", start) + 3
        body = source[start:end]

        allocation = (
            "Hunk_UserAlloc(user, sizeof(searchpath_s), "
            "static_cast<int>(alignof(searchpath_s)))"
        )
        self.assertEqual(body.count(allocation), 2)
        self.assertNotIn("Hunk_UserAlloc(user, 0x1Cu, 4)", body)
        self.assertNotIn("Hunk_UserAlloc(user, 0x1C, 4)", body)

    def test_pointer_bearing_iwd_structures_have_explicit_32_and_64_bit_layout_gates(self):
        source = (ENGINE / "com_files_handle_table.cpp").read_text(encoding="utf-8")
        expected_assertions = (
            "sizeof(fileInIwd_s) == (sizeof(void *) == 8 ? 24u : 12u)",
            "offsetof(fileInIwd_s, name) == (sizeof(void *) == 8 ? 8u : 4u)",
            "offsetof(fileInIwd_s, next) == (sizeof(void *) == 8 ? 16u : 8u)",
            "sizeof(iwd_t) == (sizeof(void *) == 8 ? 816u : 804u)",
            "offsetof(iwd_t, hashTable) == (sizeof(void *) == 8 ? 800u : 796u)",
            "offsetof(iwd_t, buildBuffer) == (sizeof(void *) == 8 ? 808u : 800u)",
            "sizeof(searchpath_s) == (sizeof(void *) == 8 ? 40u : 28u)",
            "offsetof(searchpath_s, dir) == (sizeof(void *) == 8 ? 16u : 8u)",
            "offsetof(searchpath_s, language) == (sizeof(void *) == 8 ? 36u : 24u)",
        )
        for assertion in expected_assertions:
            with self.subTest(assertion=assertion):
                self.assertIn(assertion, source)

    def test_original_win32_size_comments_are_not_used_as_allocation_constants(self):
        source = (ENGINE / "com_files.cpp").read_text(encoding="utf-8")
        start = source.index(
            "const char **__cdecl FS_ListFilteredFilesInLocation("
        )
        end = source.index("\n}\n", start) + 3
        body = source[start:end]
        self.assertNotRegex(body, r"Hunk_UserAlloc\([^\n]*0x1C[uU]?\s*,\s*4\s*\)")


if __name__ == "__main__":
    unittest.main()
