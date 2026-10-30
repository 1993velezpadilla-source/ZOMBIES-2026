"""Regression coverage for verbatim staging/linking of the original IW3 command tokenizer."""
from pathlib import Path
import json
import re
import tempfile
import unittest

from tools.iw3_android.prepare_real_engine_cmd_tokenizer import (
    FUNCTIONS,
    STATE_DECLARATION,
    prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD/src/qcommon/cmd.cpp"
GENERATOR = ROOT / "tools/iw3_android/prepare_real_engine_cmd_tokenizer.py"
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"
WORKFLOW = ROOT / ".github/workflows/iw3-original-native-android.yml"


class OriginalCommandTokenizerTests(unittest.TestCase):
    def test_original_tokenizer_bodies_and_private_state_are_staged_verbatim(self):
        source = ENGINE.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_cmd_tokenizer.cpp"
            report = Path(temp) / "iw3_cmd_tokenizer.json"
            evidence = prepare(ROOT / "third_party/KisakCOD", output, report)
            generated = output.read_text(encoding="utf-8")
            parsed = json.loads(report.read_text(encoding="utf-8"))

        self.assertEqual(len(re.findall(r"(?m)^CmdArgsPrivate cmd_argsPrivate;$", source)), 1)
        self.assertEqual(generated.count(STATE_DECLARATION), 1)
        for signature in FUNCTIONS:
            self.assertIn(function_source(source, signature), generated)
        self.assertTrue(evidence["original_tokenizer_and_end_functions_preserved_verbatim"])
        self.assertTrue(parsed["original_cmd_argsPrivate_state_preserved"])
        self.assertTrue(parsed["command_dispatcher_not_extracted"])
        self.assertTrue(parsed["Cmd_Init_not_extracted"])
        self.assertFalse(parsed["filesystem_startup_invoked"])
        self.assertFalse(parsed["playable_apk"])
        self.assertNotIn("Cmd_Init(", generated)
        self.assertNotIn("Cmd_AddCommandInternal(", generated)

    def test_android_archive_is_link_audited_but_not_added_to_jni_diagnostic(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("IW3_EXTRACTED_CMD_TOKENIZER", cmake)
        self.assertIn("add_library(iw3_sp_cmd_tokenizer STATIC", cmake)
        self.assertNotIn(
            "target_link_libraries(iw3_sp_math PRIVATE iw3_sp_cmd_tokenizer",
            cmake,
        )
        self.assertIn("prepare_real_engine_cmd_tokenizer.py", workflow)
        self.assertIn("libiw3_sp_cmd_tokenizer.a", workflow)
        self.assertIn("Cmd_TokenizeString(char*)", workflow)
        self.assertIn("Cmd_EndTokenizedString()", workflow)
        self.assertIn("IW3_ORIGINAL_CMD_TOKENIZER_AARCH64_LINK_GREEN", workflow)
        self.assertIn("IW3_FS_STARTUP_RUNTIME_INVOKED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)
        self.assertEqual(
            workflow.count('-DIW3_EXTRACTED_CMD_TOKENIZER="$RUNNER_TEMP/iw3-source/iw3_cmd_tokenizer.cpp"'),
            2,
        )


if __name__ == "__main__":
    unittest.main()
