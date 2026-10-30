"""Regression coverage for the original client/dvar writer-gate dependency audit."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/iw3-original-native-android.yml"
LOCK_PROVIDER = ROOT / "android/iw3-native/iw3_android_fs_lock_io.cpp"
LOCK_HOST_TEST = ROOT / "android/iw3-native/fs_readfile_services_native_test.cpp"
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"


class OriginalClientDvarLockServiceTests(unittest.TestCase):
    def test_android_provider_preserves_writer_gate_semantics(self):
        source = LOCK_PROVIDER.read_text(encoding="utf-8")
        self.assertIn('#include "qcommon/fast_critical_section.h"', source)
        self.assertIn("void Sys_LockWrite(FastCriticalSection *critSect)", source)
        self.assertIn("void Sys_UnlockWrite(FastCriticalSection *critSect)", source)
        self.assertIn("__atomic_load_n(&critSect->readCount, __ATOMIC_SEQ_CST)", source)
        self.assertIn("__atomic_add_fetch(&critSect->writeCount, 1U, __ATOMIC_SEQ_CST)", source)
        self.assertIn("__atomic_sub_fetch(&critSect->writeCount, 1U, __ATOMIC_SEQ_CST)", source)
        self.assertIn("sched_yield()", source)
        self.assertIn("assert(critSect != nullptr)", source)
        self.assertNotIn("Windows.h", source)
        self.assertNotIn("InterlockedCompareExchange(", source)

    def test_existing_host_regression_exercises_reader_gate_and_contention(self):
        source = LOCK_HOST_TEST.read_text(encoding="utf-8")
        self.assertIn("test_writer_waits_while_reader_count_is_nonzero()", source)
        self.assertIn("test_writer_exclusion_under_contention()", source)
        self.assertIn("constexpr int kThreadCount = 8", source)
        self.assertIn("constexpr int kIterations = 12000", source)
        cmake = CMAKE.read_text(encoding="utf-8")
        self.assertIn('"${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_fs_lock_io.cpp"', cmake)
        self.assertIn("iw3_original_fs_logfile_state_and_writer_lock", cmake)

    def test_arm64_client_dvar_audit_compiles_and_links_the_real_provider(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('lock_source="$GITHUB_WORKSPACE/android/iw3-native/iw3_android_fs_lock_io.cpp"', workflow)
        self.assertIn('aarch64-linux-android26-clang++', workflow)
        self.assertIn("Machine:                           AArch64", workflow)
        self.assertIn('"$dvar_combined" "$lock_object" -o "$lock_combined"', workflow)
        self.assertIn("iw3-client-dvar-lock-combined-defined.txt", workflow)
        self.assertIn("iw3-client-dvar-lock-combined-undefined.txt", workflow)
        self.assertIn("IW3_ORIGINAL_BGAME_MELEE_DVAR_WRITER_GATE_EDGES_RESOLVED_AARCH64_GREEN", workflow)
        self.assertNotIn('grep -F \'Sys_LockWrite\' "$RUNNER_TEMP/iw3-client-input-with-original-dvar-undefined.txt"', workflow)
        self.assertIn("IW3_CLIENT_RUNTIME_LINKED=false", workflow)
        self.assertIn("IW3_REAL_MAP_LOADED=false", workflow)
        self.assertIn("IW3_GAMEPLAY_PROVEN=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)
        for artifact in (
            "iw3-client-dvar-lock-provider-arm64.o",
            "iw3-client-dvar-lock-provider-elf.txt",
            "iw3-client-dvar-lock-link.json",
        ):
            self.assertIn(artifact, workflow)


if __name__ == "__main__":
    unittest.main()
