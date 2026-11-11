"""Keep the long Android emulator evidence run from being cancelled by duplicate push/PR events."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/iw3-original-android-emulator-jni.yml"


class EmulatorEvidenceConcurrencyTests(unittest.TestCase):
    def test_emulator_run_is_not_cancelled_mid_probe_by_duplicate_events(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        concurrency = workflow.split("concurrency:", 1)[1].split("\njobs:", 1)[0]
        self.assertIn("cancel-in-progress: false", concurrency)

    def test_workflow_still_executes_the_real_android_probe(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("reactivecircus/android-emulator-runner@v2", workflow)
        self.assertIn("script: bash tools/iw3_android/run_emulator_probe.sh", workflow)

    def test_evidence_upload_runs_even_when_the_probe_fails(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if: always()", workflow)
        self.assertIn("IW3-native-original-Cpp-Android-emulator-JNI-log-NOT-GAME", workflow)
        self.assertIn("never claim ARM64 device gameplay", workflow)


if __name__ == "__main__":
    unittest.main()
