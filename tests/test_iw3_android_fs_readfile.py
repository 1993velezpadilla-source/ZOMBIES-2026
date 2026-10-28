"""Regression tests for the original FS_ReadFile ABI/source extraction."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"

class OriginalFilesystemReadFileTests(unittest.TestCase):
    def test_original_fs_readfile_and_memory_wrappers_are_staged_verbatim(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_fs_readfile.cpp"
            report = Path(temp) / "evidence.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_fs_readfile.py"),
                 "--engine", str(ENGINE), "--output", str(output), "--report", str(report)],
                cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            staged = output.read_text(encoding="utf-8")
            evidence = json.loads(report.read_text(encoding="utf-8"))
        for marker in ("len = FS_FOpenFileRead(qpath, &h);",
                       "FS_Read(buf, len, h);", "buf[len] = 0;",
                       "Hunk_AllocateTempMemory(bytes, \"FS_AllocMem\")",
                       "Hunk_FreeTempMemory(buffer);"):
            self.assertIn(marker, staged)
        self.assertTrue(evidence["original_fs_readfile_bodies_preserved_verbatim"])
        self.assertTrue(evidence["com_file_accessed_and_load_stack_have_single_shared_state"])
        self.assertFalse(evidence["startup_runtime_invoked"])
        self.assertFalse(evidence["playable_apk"])

    def test_fs_load_state_has_one_engine_owned_definition(self):
        source = (ENGINE / "src/universal/com_files.cpp").read_text(encoding="utf-8")
        state = (ENGINE / "src/universal/com_files_state.cpp").read_text(encoding="utf-8")
        header = (ENGINE / "src/universal/com_files.h").read_text(encoding="utf-8")
        self.assertNotRegex(source, r"(?m)^\\s*int\\s+com_fileAccessed\\s*;\\s*$")
        self.assertNotRegex(source, r"(?m)^\\s*int\\s+fs_loadStack\\s*;\\s*$")
        self.assertIn("int com_fileAccessed = 0;", state)
        self.assertIn("int fs_loadStack = 0;", state)
        self.assertIn("extern int com_fileAccessed;", header)
        self.assertIn("extern int fs_loadStack;", header)

    def test_native_workflow_links_fs_readfile_but_does_not_claim_runtime(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("add_library(iw3_sp_fs_readfile STATIC", cmake)
        self.assertIn("IW3_EXTRACTED_FS_READFILE", cmake)
        self.assertIn("prepare_real_engine_fs_readfile.py", workflow)
        self.assertIn("libiw3_sp_fs_readfile.a", workflow)
        self.assertIn("IW3_ORIGINAL_FS_STARTUP_IWD_DIRECTORY_AND_READFILE_AARCH64_LINK_GREEN", workflow)
        self.assertIn("Hunk_AllocateTempMemory Hunk_FreeTempMemory SEH_InitLanguage", workflow)
        self.assertIn('echo "IW3_FS_STARTUP_RUNTIME_INVOKED=false"', workflow)
        self.assertIn('echo "IW3_PLAYABLE_APK=false"', workflow)

if __name__ == "__main__":
    unittest.main()
