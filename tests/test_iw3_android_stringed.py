"""Regression tests for the authentic StringEd loader slice and its audit boundary."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalStringedLoaderTests(unittest.TestCase):
    def test_loader_bodies_are_staged_from_upstream_without_d3d_database_entrypoints(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_stringed_ingame.cpp"
            report_path = Path(temp) / "evidence.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_stringed.py"),
                 "--engine", str(ENGINE), "--output", str(output), "--report", str(report_path)],
                cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            staged = output.read_text(encoding="utf-8")
            evidence = json.loads(report_path.read_text(encoding="utf-8"))

        for marker in (
            "SE_Load(", "SE_NewLanguage(", "SE_Init(", "SE_ShutDown(",
            "SE_LoadLanguage(", "SE_GetFoundFile(", "SE_LoadFileData(",
            "SE_FreeFileDataAfterLoad(", "SE_BuildFileList(", "SE_R_ListFiles(",
            "TheStringPackage = new CStringEdPackage();",
            'SE_BuildFileList("localizedstrings", &strResults);',
            "FS_ReadFile(psFileName, (void **)&pvLoadedData)",
            'FS_ListFiles(psDir, "/", FS_LIST_PURE_ONLY, &numdirs)',
            "FS_FreeFileList(sysFiles);",
        ):
            self.assertIn(marker, staged)
        self.assertTrue(evidence["original_StringEd_loader_bodies_preserved_verbatim"])
        self.assertTrue(evidence["original_StringEd_globals_preserved"])
        self.assertTrue(evidence["D3D_database_entry_points_excluded"])
        self.assertTrue(evidence["FS_ListFiles_and_FS_ReadFile_are_original_engine_calls"])
        self.assertFalse(evidence["stringed_runtime_invoked"])
        self.assertFalse(evidence["localized_assets_loaded"])
        self.assertFalse(evidence["playable_apk"])
        self.assertIn("#include <qcommon/qcommon.h>", staged)
        self.assertIn("#define ARRAYSIZE(a) (sizeof(a) / sizeof((a)[0]))", staged)
        self.assertNotIn("#include <database/database.h>", staged)
        self.assertNotIn("DB_FindXAssetHeader", staged)
        self.assertNotIn("SE_GetString_FastFile", staged)

    def test_host_and_arm64_audits_use_the_generated_original_loader_slice(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("IW3_EXTRACTED_STRINGED_INGAME", cmake)
        self.assertIn('add_library(iw3_sp_stringed_ingame STATIC', cmake)
        self.assertIn('prepare_real_engine_stringed.py', workflow)
        self.assertEqual(workflow.count('-DIW3_EXTRACTED_STRINGED_INGAME="$RUNNER_TEMP/iw3-source/iw3_stringed_ingame.cpp"'), 2)
        self.assertIn("libiw3_sp_stringed_ingame.a", workflow)
        self.assertIn("IW3_ORIGINAL_STRINGED_INIT_CHAIN_AARCH64_LINK_GREEN", workflow)
        self.assertIn("IW3_ORIGINAL_FS_LISTFILES_FILTERED_CHAIN_AARCH64_LINK_GREEN", workflow)
        self.assertIn('echo "IW3_FS_STARTUP_RUNTIME_INVOKED=false"', workflow)
        self.assertIn('echo "IW3_PLAYABLE_APK=false"', workflow)


if __name__ == "__main__":
    unittest.main()
