"""Regression tests for authentic KisakCOD language-init staging and ARM64 linkage."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalLanguageRegistryTests(unittest.TestCase):
    def test_original_language_table_and_functions_are_staged_verbatim(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_language.cpp"
            report_path = Path(temp) / "evidence.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_language.py"),
                 "--engine", str(ENGINE), "--output", str(output), "--report", str(report_path)],
                cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            staged = output.read_text(encoding="utf-8")
            evidence = json.loads(report_path.read_text(encoding="utf-8"))

        expected = [
            "english", "french", "german", "italian", "spanish",
            "british", "russian", "polish", "korean", "taiwanese",
            "japanese", "chinese", "thai", "leet", "czech",
        ]
        self.assertEqual(evidence["language_names"], expected)
        self.assertTrue(evidence["original_language_table_preserved_verbatim"])
        self.assertTrue(evidence["original_SEH_GetCurrentLanguage_body_preserved_verbatim"])
        self.assertTrue(evidence["original_SEH_InitLanguage_body_preserved_verbatim"])
        self.assertTrue(evidence["original_SEH_UpdateCurrentLanguage_body_preserved_verbatim"])
        self.assertTrue(evidence["original_language_name_and_index_helpers_preserved_verbatim"])
        self.assertTrue(evidence["languageInfo_t_native_pointer_layout_guarded"])
        self.assertTrue(evidence["original_FS_LanguageHasAssets_body_preserved_verbatim"])
        self.assertTrue(evidence["original_SEH_StringEd_SetLanguageStrings_body_preserved_verbatim"])
        self.assertTrue(evidence["original_SEH_UpdateLanguageInfo_body_preserved_verbatim"])
        self.assertTrue(evidence["original_SEH_Init_StringEd_and_shutdown_bodies_preserved_verbatim"])
        self.assertFalse(evidence["full_stringed_database_and_translation_loading_ported"])
        self.assertFalse(evidence["stringed_runtime_invoked"])
        self.assertFalse(evidence["playable_apk"])
        for marker in ("SEH_GetCurrentLanguage", "SEH_InitLanguage", "SEH_UpdateCurrentLanguage",
                       "SEH_GetLanguageName", "SEH_GetLanguageIndexForName",
                       "FS_LanguageHasAssets", "SEH_StringEd_SetLanguageStrings",
                       "SEH_UpdateLanguageInfo", "SEH_Init_StringEd",
                       "SEH_Shutdown_StringEd", "SE_Init();", "SE_ShutDown();"):
            self.assertIn(marker, staged)
        self.assertNotIn('return language == 0 ? "english" : "";', staged)

    def test_language_audit_uses_original_provider_not_english_only_adapter(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        adapter = (ROOT / "android/iw3-native/iw3_android_iwd_directory_io.cpp").read_text(encoding="utf-8")
        compat = (ROOT / "android/iw3-native/iw3_android_language_compat.h").read_text(encoding="utf-8")

        self.assertIn("add_library(iw3_sp_language STATIC", cmake)
        self.assertIn("add_library(iw3_sp_stringed_ingame STATIC", cmake)
        self.assertIn('stringed/stringed_ingame.cpp', cmake)
        self.assertIn("iw3_language_native_test", cmake)
        self.assertIn("prepare_real_engine_language.py", workflow)
        self.assertIn("IW3_EXTRACTED_LANGUAGE", workflow)
        self.assertIn("libiw3_sp_language.a", workflow)
        self.assertIn("IW3_ORIGINAL_FS_STARTUP_LANGUAGE_INIT_AARCH64_LINK_GREEN", workflow)
        self.assertIn("libiw3_sp_stringed_ingame.a", workflow)
        self.assertIn("IW3_ORIGINAL_STRINGED_INIT_CHAIN_AARCH64_LINK_GREEN", workflow)
        self.assertIn("FS_ListFiles FS_CheckLocation FS_ListFilteredFiles FS_ListFilteredFilesInLocation", workflow)
        self.assertIn("IW3_ORIGINAL_FS_LISTFILES_FILTERED_CHAIN_AARCH64_LINK_GREEN", workflow)
        self.assertNotIn('if ! grep -F "FS_ListFiles"', workflow)
        self.assertIn("#if !defined(IW3_IWD_DIRECTORY_LINK_AUDIT)", adapter)
        self.assertIn("static_assert(sizeof(languageInfo_t)", compat)
        self.assertIn("SEH_UpdateCurrentLanguage();", (ROOT / "tools/iw3_android/prepare_real_engine_language.py").read_text(encoding="utf-8"))
        self.assertIn("const dvar_s *__cdecl SEH_UpdateCurrentLanguage();", compat)
        self.assertIn('echo "IW3_FS_STARTUP_RUNTIME_INVOKED=false"', workflow)
        self.assertIn('echo "IW3_PLAYABLE_APK=false"', workflow)
        self.assertNotIn('for symbol in SEH_InitLanguage; do\n            grep -F "$symbol" "$RUNNER_TEMP/iw3-fs-dvar-iwd-undefined.txt"\n          done', workflow)


if __name__ == "__main__":
    unittest.main()
