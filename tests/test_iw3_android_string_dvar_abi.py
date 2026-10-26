"""Regression tests for 64-bit string dvar pointers in original KisakCOD FS."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/universal/com_files.cpp"
STRING_DVARS = (
    "fs_homepath",
    "fs_basepath",
    "fs_cdpath",
    "fs_basegame",
    "fs_gameDirVar",
)


class OriginalFilesystemStringDvarABITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_string_values_never_travel_through_32_bit_integer_member(self):
        for name in STRING_DVARS:
            with self.subTest(dvar=name):
                self.assertNotRegex(
                    self.source, rf"\\b{name}->current\\.integer\\b"
                )
                self.assertIn(f"{name}->current.string", self.source)

    def test_startup_uses_native_width_string_pointers(self):
        startup_start = self.source.index("void __cdecl FS_Startup(char *gameName)")
        startup_end = self.source.index("void __cdecl FS_InitFilesystem()", startup_start)
        startup = self.source[startup_start:startup_end]
        self.assertIn("fs_basepath->current.string[0] != '\\0'", startup)
        self.assertIn("fs_homepath->current.string[0] != '\\0'", startup)
        self.assertIn("FS_AddLocalizedGameDirectory((char *)fs_basepath->current.string", startup)
        self.assertNotIn("current.integer", startup)

    def test_open_and_init_paths_keep_string_pointer_width(self):
        open_start = self.source.index(
            "uint32_t __cdecl FS_FOpenFileReadForThread("
        )
        open_end = self.source.index("\\n}\\n", open_start) + 3
        open_body = self.source[open_start:open_end]
        self.assertIn("FS_BuildOSPathForThread((char*)fs_basepath->current.string", open_body)
        self.assertNotIn("fs_basepath->current.integer", open_body)

        init_start = self.source.index("void __cdecl FS_InitFilesystem()")
        init_end = self.source.index("uint32_t __cdecl FS_FOpenFileByMode", init_start)
        init_body = self.source[init_start:init_end]
        self.assertIn("lastValidBase, (char *)fs_basepath->current.string", init_body)
        self.assertIn("lastValidGame, (char *)fs_gameDirVar->current.string", init_body)

    def test_numeric_debug_dvar_stays_numeric(self):
        self.assertIn("fs_debug->current.integer", self.source)


if __name__ == "__main__":
    unittest.main()
