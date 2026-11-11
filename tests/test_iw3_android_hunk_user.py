"""Regression tests for native-width original HunkUser allocation and POSIX VM services."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalHunkUserTests(unittest.TestCase):
    def test_original_hunk_user_bodies_are_transformed_without_32_bit_addresses(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_hunk_user.cpp"
            report_path = Path(temp) / "evidence.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_hunk_user.py"),
                 "--engine", str(ENGINE), "--output", str(output), "--report", str(report_path)],
                cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            staged = output.read_text(encoding="utf-8")
            evidence = json.loads(report_path.read_text(encoding="utf-8"))

        for marker in (
            "Hunk_UserCreate(", "Hunk_UserAlloc(", "Hunk_UserAllocAlignStrict(",
            "Hunk_UserSetPos(", "Hunk_UserReset(", "Hunk_UserDestroy(", "Hunk_CopyString(",
            "user->end = reinterpret_cast<uintptr_t>(user) + static_cast<uintptr_t>(maxSize);",
            "user->pos = reinterpret_cast<uintptr_t>(user->buf);",
            "offsetof(HunkUser, buf)", "uintptr_t pos;", "uintptr_t result;",
            "Z_VirtualCommit(reinterpret_cast<void *>(pos), static_cast<int32_t>(current->pos - pos));",
            "pos = reinterpret_cast<uintptr_t>(user) + 4096u;",
            "memset(user->buf, 0, 4096u - offsetof(HunkUser, buf));",
        ):
            self.assertIn(marker, staged)
        self.assertTrue(evidence["original_HunkUser_bodies_used_with_reviewed_LP64_fixes"])
        self.assertTrue(evidence["HunkUser_header_uses_native_width_address_state"])
        self.assertTrue(evidence["virtual_memory_platform_adapter_required"])
        self.assertFalse(evidence["hunk_user_runtime_invoked"])
        self.assertFalse(evidence["playable_apk"])
        for forbidden in (
            "user->end = (int)user + maxSize;", "user->pos = (int)user->buf;",
            "int32_t pos;", "int32_t result;", "(uint32_t)pos",
            "(int)pos", "user[114].name", "0xFE0u",
        ):
            self.assertNotIn(forbidden, staged)

    def test_vendored_hunk_user_functions_are_already_lp64_safe(self):
        source = (ENGINE / "src/universal/com_memory_hunk_user.cpp").read_text(encoding="utf-8")
        for marker in (
            "user->end = reinterpret_cast<uintptr_t>(user) + static_cast<uintptr_t>(maxSize);",
            "user->pos = reinterpret_cast<uintptr_t>(user->buf);",
            "uintptr_t pos;",
            "uintptr_t result;",
            "Z_VirtualCommit(reinterpret_cast<void *>(pos), static_cast<int32_t>(current->pos - pos));",
            "user->pos = reinterpret_cast<uintptr_t>(pos);",
            "pos = reinterpret_cast<uintptr_t>(user) + 4096u;",
            "Z_VirtualDecommit(reinterpret_cast<void *>(pos), static_cast<int32_t>(user->pos - pos));",
        ):
            self.assertIn(marker, source)
        for forbidden in (
            "user->end = (int)user + maxSize;",
            "user->pos = (int)user->buf;",
            "int32_t pos; // [esp+4h] [ebp-10h]",
            "int32_t result; // [esp+8h] [ebp-Ch]",
            "(uint32_t)pos",
            "(int)pos",
            "user[114].name",
        ):
            self.assertNotIn(forbidden, source)

    def test_hunk_user_header_and_virtual_memory_adapter_are_native_width(self):
        header = (ROOT / "third_party/KisakCOD/src/universal/com_memory.h").read_text(encoding="utf-8")
        adapter = (ROOT / "android/iw3-native/iw3_android_hunk_virtual.cpp").read_text(encoding="utf-8")
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("uintptr_t end;", header)
        self.assertIn("uintptr_t pos;", header)
        self.assertIn("alignas(32) uint8_t buf[1];", header)
        self.assertIn("offsetof(HunkUser, buf) == 0x20", header)
        self.assertIn("mmap(", adapter)
        self.assertIn("mprotect(", adapter)
        self.assertIn("madvise(", adapter)
        self.assertIn("munmap(", adapter)
        self.assertIn("IsRangeReservedLocked", adapter)
        self.assertIn('VirtualMemoryFatal("Z_VirtualFree null pointer", EINVAL)', adapter)
        self.assertNotIn("VirtualAlloc(", adapter)
        self.assertNotIn("VirtualFreeInternal(", adapter)
        self.assertIn("add_library(iw3_sp_hunk_user STATIC", cmake)
        self.assertIn("iw3_hunk_user_native_test", cmake)
        self.assertIn("prepare_real_engine_hunk_user.py", workflow)
        self.assertEqual(workflow.count('-DIW3_EXTRACTED_HUNK_USER="$RUNNER_TEMP/iw3-source/iw3_hunk_user.cpp"'), 2)
        self.assertIn("libiw3_sp_hunk_user.a", workflow)
        self.assertIn("IW3_ORIGINAL_HUNK_USER_LP64_AARCH64_LINK_GREEN", workflow)
        self.assertIn("for symbol in MyAssertHandler I_strnicmp; do", workflow)
        self.assertIn("for symbol in 'Com_Filter(' 'Com_FilterPath('; do", workflow)
        self.assertIn('IW3_ORIGINAL_FILTER_PATH_PROVIDER_AARCH64_LINK_GREEN', workflow)
        self.assertIn('grep -F "$symbol" "$RUNNER_TEMP/iw3-fs-dvar-iwd-defined.txt"', workflow)
        self.assertIn('echo "IW3_FS_STARTUP_RUNTIME_INVOKED=false"', workflow)
        self.assertIn('echo "IW3_PLAYABLE_APK=false"', workflow)


if __name__ == "__main__":
    unittest.main()
