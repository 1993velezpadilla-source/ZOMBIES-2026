import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "android" / "iw3-native" / "iw3_android_iwd_directory_io.cpp"


class AndroidIwdDirectoryAdapterTests(unittest.TestCase):
    def test_com_sprintf_uses_real_nul_terminators(self):
        source = ADAPTER.read_text(encoding="utf-8")
        self.assertIn(r"dest[size - 1] = '\0';", source)
        self.assertIn(r"if (written < 0) dest[0] = '\0';", source)

    def test_assert_handler_emits_a_newline_not_a_multicharacter_constant(self):
        source = ADAPTER.read_text(encoding="utf-8")
        self.assertIn(r"std::fputc('\n', stderr);", source)

    def test_no_double_backslash_escape_character_literals_remain(self):
        source = ADAPTER.read_text(encoding="utf-8")
        # In C++, '\\0' and '\\n' are multi-character literals here, not
        # NUL/newline escapes. They compile with warnings and become '0'/'n'.
        self.assertEqual(re.findall(r"'\\\\[0n]'", source), [])


if __name__ == "__main__":
    unittest.main()
