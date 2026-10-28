"""Regression for native-width string dvar reads in original KisakCOD commands."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/qcommon/cmd.cpp"


class OriginalCommandStringDvarABITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        start = cls.source.index("void Cmd_Dumpraw_f(void)")
        end = cls.source.index("\nvoid Cmd_Init()", start)
        cls.dumpraw = cls.source[start:end]

    def test_raw_dump_paths_use_native_width_string_member(self):
        self.assertIn(
            'std::format("{}\\\\raw\\\\", (char *)fs_basepath->current.string)',
            self.dumpraw,
        )
        self.assertIn(
            'std::format("{}\\\\zone\\\\english\\\\", (char *)fs_basepath->current.string)',
            self.dumpraw,
        )
        self.assertEqual(self.dumpraw.count("fs_basepath->current.string"), 2)
        self.assertNotIn("fs_basepath->current.integer", self.dumpraw)

    def test_no_integer_union_member_is_cast_to_a_path_pointer(self):
        self.assertIsNone(
            re.search(
                r"\(char\s*\*\)\s*fs_basepath->current\.integer",
                self.dumpraw,
            )
        )

    def test_numeric_dvars_are_not_banned_globally(self):
        # The guard is deliberately scoped to string-valued fs_basepath uses;
        # numeric controls elsewhere in cmd.cpp still use current.integer.
        self.assertIn("cl_paused->current.integer", self.source)


if __name__ == "__main__":
    unittest.main()
