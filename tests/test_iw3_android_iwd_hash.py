"""Regression gate for signed-char safety in the authentic IW3 IWD hash."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.iw3_android.prepare_real_engine_iwd_names import (
    FILES, FUNCTIONS, REQUIRED, FORBIDDEN, prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalIwdHashPortabilityTests(unittest.TestCase):
    def test_original_hash_uses_unsigned_char_for_ctype(self):
        source_path = ENGINE / FILES
        source = source_path.read_text(encoding="utf-8")
        signature = "int __cdecl FS_HashFileName(const char *fname, int hashSize)"
        body = function_source(source, signature)
        self.assertIn("tolower(static_cast<unsigned char>(fname[i]))", body)
        self.assertNotIn("tolower(fname[i])", body)
        self.assertIn("letter = tolower(static_cast<unsigned char>(fname[i]));", REQUIRED)
        self.assertIn("letter = tolower(fname[i]);", FORBIDDEN)

        native = (ROOT / "android/iw3-native/iwd_names_native_test.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn("static_cast<char>(0xFE)", native)
        self.assertIn("FS_HashFileName(highBitName, 1024) == 930", native)

    def test_original_iwd_language_parser_uses_unsigned_char_for_ctype(self):
        source = (ENGINE / FILES).read_text(encoding="utf-8")
        body = function_source(
            source,
            "char *__cdecl IwdFileLanguage(const char *pszIwdFileName)",
        )
        self.assertIn(
            "isalpha(static_cast<unsigned char>(pszIwdFileName[iCurrChar]))",
            body,
        )
        self.assertNotIn("isalpha(pszIwdFileName[iCurrChar])", body)
        native = (ROOT / "android/iw3-native/iwd_names_native_test.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn("IwdFileLanguage(englishIwdName)", native)
        self.assertIn("static_cast<char>(0xFE)", native)
        self.assertIn("IwdFileLanguage(highBitLanguageName)", native)

    def test_generated_original_hash_and_language_helpers_keep_high_bit_guards(self):
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "iw3_iwd_names.cpp"
            report = prepare(ENGINE, output)
            staged = output.read_text(encoding="utf-8")
            self.assertIn("tolower(static_cast<unsigned char>(fname[i]))", staged)
            self.assertNotIn("tolower(fname[i])", staged)
            self.assertIn(
                "isalpha(static_cast<unsigned char>(pszIwdFileName[iCurrChar]))",
                staged,
            )
            self.assertNotIn("isalpha(pszIwdFileName[iCurrChar])", staged)
            self.assertTrue(report["iwd_filename_hash_high_bit_safe"])
            self.assertTrue(report["iwd_language_sort_key_high_bit_safe"])
            self.assertFalse(report["fastfile_map_loading_ported"])
            self.assertFalse(report["playable_apk"])


if __name__ == "__main__":
    unittest.main()
