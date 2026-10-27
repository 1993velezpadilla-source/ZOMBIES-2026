"""Regression gates for signed-char safety in authentic IW3 IWD helpers."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.iw3_android.prepare_real_engine_iwd_names import (
    FILES, REQUIRED, FORBIDDEN, prepare,
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

    def test_original_iwd_language_parser_is_unsigned_char_safe(self):
        source = (ENGINE / FILES).read_text(encoding="utf-8")
        body = function_source(
            source,
            "char *__cdecl IwdFileLanguage(const char *pszIwdFileName)",
        )
        safe = "isalpha(static_cast<unsigned char>(pszIwdFileName[iCurrChar]))"
        unsafe = "isalpha(pszIwdFileName[iCurrChar])"
        self.assertIn(safe, body)
        self.assertNotIn(unsafe, body)
        self.assertIn(safe, REQUIRED)
        self.assertIn(unsafe, FORBIDDEN)

        native = (ROOT / "android/iw3-native/iwd_names_native_test.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn("IwdFileLanguage(englishIwdName)", native)
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
            self.assertIn("char szIwdLanguageName[2][64];", staged)
            self.assertIn("int iString = 0;", staged)
            self.assertTrue(report["iwd_filename_hash_high_bit_safe"])
            self.assertTrue(report["iwd_language_sort_key_high_bit_safe"])
            self.assertTrue(report["iwd_language_sort_state_staged_from_original"])
            self.assertFalse(report["fastfile_map_loading_ported"])
            self.assertFalse(report["playable_apk"])


if __name__ == "__main__":
    unittest.main()
