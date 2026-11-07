"""Regression coverage for original logfile state and Android writer-lock port."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_com_logfile_open import (
    SOURCE, SIGNATURE, prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalLogfileOpenProviderTests(unittest.TestCase):
    def test_original_state_and_query_are_extracted_without_replacement(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        body = function_source(source, SIGNATURE)
        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "com_logfile_open.cpp"
            report = Path(temp) / "evidence.json"
            evidence = prepare(ENGINE, output, report)
            staged = output.read_text(encoding="utf-8")
            self.assertTrue(staged.startswith('#include "qcommon/qcommon.h"\n\nint logfile;\n\n'))
            self.assertNotIn("\\nint logfile;\\n", staged)
            self.assertIn("int logfile;", staged)
            self.assertIn(body, staged)
            self.assertIn("return logfile != 0;", staged)
            self.assertEqual(evidence["source_sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual(evidence["function_sha256"], hashlib.sha256(body.encode("utf-8")).hexdigest())
            self.assertTrue(evidence["original_logfile_state_definition_preserved"])
            self.assertTrue(evidence["original_Com_LogFileOpen_body_preserved_verbatim"])
            self.assertFalse(evidence["startup_runtime_invoked"])
            self.assertFalse(evidence["playable_apk"])
        self.assertEqual(source_path.read_bytes(), original)

    def test_android_lock_port_preserves_original_counter_abi_and_real_gate(self):
        lock = (ROOT / "android/iw3-native/iw3_android_fs_lock_io.cpp").read_text(encoding="utf-8")
        header = (ROOT / "third_party/KisakCOD/src/qcommon/fast_critical_section.h").read_text(encoding="utf-8")
        self.assertIn("struct FastCriticalSection", header)
        self.assertIn("sizeof(FastCriticalSection) == 8", header)
        self.assertIn("__atomic_load_n(&critSect->readCount, __ATOMIC_SEQ_CST)", lock)
        self.assertIn("__atomic_add_fetch(&critSect->writeCount, 1U, __ATOMIC_SEQ_CST)", lock)
        self.assertIn("sched_yield()", lock)
        self.assertNotIn("Windows.h", lock)
        self.assertNotIn("return; // stub", lock)

    def test_native_host_test_is_wired_into_filesystem_read_audit(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("iw3_android_fs_lock_io.cpp", cmake)
        self.assertIn("fs_readfile_services_native_test.cpp", cmake)
        self.assertIn("IW3_EXTRACTED_COM_LOGFILE_OPEN", cmake)
        self.assertIn("prepare_real_engine_com_logfile_open.py", workflow)
        self.assertIn("'Com_LogFileOpen()'", workflow)
        self.assertIn("'Sys_LockWrite(FastCriticalSection*)'", workflow)
        self.assertIn("'Sys_UnlockWrite(FastCriticalSection*)'", workflow)
        self.assertIn("IW3_ORIGINAL_FS_READFILE_LOGFILE_AND_WRITE_LOCK_AARCH64_LINK_GREEN", workflow)


if __name__ == "__main__":
    unittest.main()
