"""Guard the original KisakCOD ARM64 workflow against accidental duplicate/corrupt tails.

These checks validate CI evidence integrity; they do not claim a playable APK.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/iw3-original-native-android.yml"


class OriginalIw3WorkflowIntegrityTests(unittest.TestCase):
    def test_single_job_and_unique_step_names(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertEqual(source.count("\njobs:\n"), 1)
        self.assertEqual(source.count("  native-iw3-original-android:\n"), 1)
        steps = re.findall(r"(?m)^      - name: (.+)$", source)
        self.assertGreaterEqual(len(steps), 30)
        self.assertEqual(len(steps), len(set(steps)), "Duplicated CI steps detected")
        self.assertEqual(
            steps.count("Attach evidence and compiled native module (NOT an APK)"),
            1,
        )
        self.assertEqual(
            source.count("name: z2026-iw3-real-math-arm64-phase-a-NOT-APK"),
            1,
        )

    def test_tokenizer_symbol_audit_has_complete_shell_lines(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "grep -E '[[:space:]]cmd_argsPrivate$' "
            '"$RUNNER_TEMP/iw3-fs-startup-combined-defined.txt"',
            source,
        )
        self.assertIn(
            "if grep -E '[[:space:]]cmd_argsPrivate$' "
            '"$RUNNER_TEMP/iw3-fs-startup-undefined.txt"; then',
            source,
        )
        self.assertIn(
            'echo "IW3_ORIGINAL_CMD_TOKENIZER_AARCH64_LINK_GREEN"',
            source,
        )
        self.assertNotIn("grep -E '[[:space:]]cmd_argsPrivate\n", source)
        self.assertNotIn(
            '\n "$RUNNER_TEMP/iw3-fs-startup-combined-defined.txt"\n',
            source,
        )

    def test_workflow_ends_in_single_evidence_upload(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertTrue(source.endswith("          if-no-files-found: error\n"))
        self.assertEqual(
            source.count("      - name: Attach evidence and compiled native module (NOT an APK)"),
            1,
        )
        for evidence in (
            "iw3-original-cmd-tokenizer.json",
            "libiw3_sp_cmd_tokenizer.a",
            "iw3-fs-startup-combined.o",
            "iw3-fs-dvar-iwd-combined.o",
        ):
            self.assertIn(evidence, source)
        self.assertIn("IW3_PLAYABLE_APK=false", source)


if __name__ == "__main__":
    unittest.main()
