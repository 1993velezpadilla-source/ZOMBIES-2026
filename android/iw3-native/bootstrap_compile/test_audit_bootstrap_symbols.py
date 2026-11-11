#!/usr/bin/env python3
"""Regression tests for the authentic IW3 ARM64 object dependency inventory."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name("audit_bootstrap_symbols.py")

class AuditTests(unittest.TestCase):
    def test_defined_symbols_are_removed_and_unresolved_sorted(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d)
            (p / "undefined").write_text("external_b U\nshared U\nexternal_a U\n")
            (p / "defined").write_text("shared T 0 4\nlocal D 0 4\n")
            out = p / "report"
            run = subprocess.run([sys.executable, str(SCRIPT), str(p / "undefined"),
                                  str(p / "defined"), str(out)],
                                 capture_output=True, text=True, check=True)
            self.assertIn("IW3_BOOTSTRAP_UNRESOLVED_UNIQUE=2", run.stdout)
            self.assertIn("IW3_PLAYABLE_APK=false", run.stdout)
            self.assertTrue(out.read_text().endswith("external_a\nexternal_b\n"))
            self.assertIn("NOT A LINKED ENGINE OR APK", out.read_text())

    def test_nm_symbol_classes_do_not_cross_contaminate(self):
        # A provider inventory must not count U records as definitions.
        # A consumer inventory must not count defined records as references.
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d)
            (p / "undefined").write_text("real_missing U\nnot_a_reference T 0 4\n")
            (p / "defined").write_text("real_missing U\ncommon_provider C 4 4\n")
            run = subprocess.run([sys.executable, str(SCRIPT), str(p / "undefined"),
                                  str(p / "defined"), str(p / "report")],
                                 capture_output=True, text=True, check=True)
            self.assertIn("IW3_BOOTSTRAP_UNRESOLVED_UNIQUE=1", run.stdout)
            self.assertTrue((p / "report").read_text().endswith("real_missing\n"))

    def test_empty_unresolved_is_not_playable(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d)
            (p / "undefined").write_text("resolved U\n")
            (p / "defined").write_text("resolved T 0 4\n")
            run = subprocess.run([sys.executable, str(SCRIPT), str(p / "undefined"),
                                  str(p / "defined"), str(p / "report")],
                                 capture_output=True, text=True, check=True)
            self.assertIn("IW3_BOOTSTRAP_UNRESOLVED_UNIQUE=0", run.stdout)
            self.assertIn("IW3_PLAYABLE_APK=false", run.stdout)

if __name__ == "__main__":
    unittest.main()
