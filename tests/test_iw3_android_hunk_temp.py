"""Regression tests for the original Hunk temporary allocator's 64-bit ABI."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json, subprocess, sys, unittest
ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"

class OriginalHunkTempAllocatorTests(unittest.TestCase):
    def test_original_hunk_temp_bodies_are_staged_with_native_width_pointers(self):
        with TemporaryDirectory() as temp:
            output, report_path = Path(temp) / "iw3_hunk_temp.cpp", Path(temp) / "evidence.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/iw3_android/prepare_real_engine_hunk_temp.py"),
                 "--engine", str(ENGINE), "--output", str(output), "--report", str(report_path)],
                cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            staged = output.read_text(encoding="utf-8")
            evidence = json.loads(report_path.read_text(encoding="utf-8"))
        for symbol in (
            "Hunk_ClearToMarkLow", "Hunk_AllocAlign", "Hunk_AllocateTempMemoryHigh",
            "Hunk_ClearTempMemoryHigh", "Hunk_AllocLowAlign", "Hunk_ClearTempMemory",
            "Hunk_AllocateTempMemory", "Hunk_FreeTempMemory",
        ):
            self.assertIn(symbol, staged)
        self.assertIn("Hunk_PageBase(&s_hunkData[hunk_low.temp + 4095])", staged)
        self.assertIn("Hunk_PageBase(&s_hunkData[s_hunkTotal - hunk_high.permanent])", staged)
        self.assertIn("Hunk_PageBase(&s_hunkData[hunk_low.permanent + 4095])", staged)
        self.assertIn("reinterpret_cast<uintptr_t>(buf) & 0xFu", staged)
        self.assertIn("uint8_t* __cdecl Hunk_AllocateTempMemoryHigh", staged)
        self.assertIn("reinterpret_cast<uintptr_t>(bufa)", staged)
        for forbidden in (
            "(uint32_t)&s_hunkData", "(uint32_t)beginBuf", "(uint8_t)bufa",
            "(uint32_t)buf", "(uint32_t)pos", "0xFFFFF000", "(_BYTE)s_hunkData",
            "(int)pos", "user[114].name", "0xFE0u",
        ):
            self.assertNotIn(forbidden, staged)
        self.assertTrue(evidence["pointer_page_alignment_uses_uintptr_t"])
        self.assertTrue(evidence["high_temp_allocator_returns_native_pointer"])
        self.assertTrue(evidence["core_allocator_page_math_uses_native_pointer_width"])
        self.assertTrue(evidence["temporary_header_fixed_at_16_bytes_on_32_and_64_bit"])
        self.assertTrue(evidence["single_engine_owned_hunk_state"])
        self.assertFalse(evidence["runtime_hunk_allocator_invoked"])
        self.assertFalse(evidence["playable_apk"])

    def test_vendored_core_hunk_allocators_no_longer_truncate_addresses(self):
        source = (ENGINE / "src/universal/com_memory.cpp").read_text(encoding="utf-8")
        header = (ENGINE / "src/universal/com_memory.h").read_text(encoding="utf-8")
        for marker in (
            "endBuf = Hunk_PageBase(&s_hunkData[s_hunkTotal - hunk_high.permanent]);",
            "buf = &s_hunkData[s_hunkTotal - hunk_high.temp];",
            "if ((reinterpret_cast<uintptr_t>(buf) & 0xFu) != 0)",
            "commitSize = static_cast<uint32_t>(Hunk_PageBase(&s_hunkData[hunk_low.permanent + 4095]) - beginBuf);",
            "user->end = reinterpret_cast<uintptr_t>(user) + static_cast<uintptr_t>(maxSize);",
            "user->pos = reinterpret_cast<uintptr_t>(user->buf);",
            "Z_VirtualCommit(reinterpret_cast<void *>(pos), static_cast<int32_t>(current->pos - pos));",
            "pos = reinterpret_cast<uintptr_t>(user) + 4096u;",
        ):
            self.assertIn(marker, source)
        self.assertIn("uint8_t* __cdecl Hunk_AllocateTempMemoryHigh", source)
        self.assertIn("uint8_t* __cdecl Hunk_AllocateTempMemoryHigh(int size, const char* name);", header)
        for forbidden in (
            "(uint32_t)&s_hunkData", "(uint32_t)beginBuf", "(uint32_t)buf",
            "user->end = (int)user + maxSize;", "user->pos = (int)user->buf;",
            "pos = (void*)(((uint32_t)&user[114].name + 3) & 0xFFFFF000);",
            "Z_VirtualCommit((void*)pos, current->pos - (uint32_t)pos);",
            "Z_VirtualDecommit(pos, user->pos - (uint32_t)pos);",
        ):
            self.assertNotIn(forbidden, source)

    def test_original_hunk_state_has_one_shared_definition(self):
        source = (ENGINE / "src/universal/com_memory.cpp").read_text(encoding="utf-8")
        state = (ENGINE / "src/universal/com_memory_state.cpp").read_text(encoding="utf-8")
        header = (ENGINE / "src/universal/com_memory_state.h").read_text(encoding="utf-8")
        common = (ENGINE / "scripts/common_files.cmake").read_text(encoding="utf-8")
        self.assertNotIn("static hunkUsed_t hunk_high;", source)
        self.assertNotIn("static hunkUsed_t hunk_low;", source)
        self.assertNotIn("unsigned char* s_hunkData;", source)
        self.assertEqual(state.count("hunkUsed_t hunk_high{};"), 1)
        self.assertEqual(state.count("hunkUsed_t hunk_low{};"), 1)
        self.assertEqual(state.count("unsigned char *s_hunkData = nullptr;"), 1)
        self.assertIn('static_assert(sizeof(hunkHeader_t) == 16', header)
        self.assertIn('include "com_memory_state.h"', (ENGINE / "src/universal/com_memory.h").read_text(encoding="utf-8"))
        self.assertIn('"${SRC_DIR}/universal/com_memory_state.cpp"', common)

    def test_aarch64_link_audit_resolves_hunk_allocator_but_keeps_runtime_incomplete(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("add_library(iw3_sp_hunk_temp STATIC", cmake)
        self.assertIn("IW3_EXTRACTED_HUNK_TEMP", workflow)
        self.assertIn("libiw3_sp_hunk_temp.a", workflow)
        self.assertIn("for symbol in Hunk_ClearToMarkLow Hunk_AllocAlign Hunk_AllocateTempMemoryHigh Hunk_ClearTempMemoryHigh Hunk_AllocLowAlign Hunk_ClearTempMemory Hunk_AllocateTempMemory Hunk_FreeTempMemory;", workflow)
        self.assertIn("IW3_ORIGINAL_HUNK_CORE_ALLOCATORS_LP64_AARCH64_LINK_GREEN", workflow)
        self.assertIn("IW3_ORIGINAL_FS_STARTUP_IWD_DIRECTORY_READFILE_HUNK_AARCH64_LINK_GREEN", workflow)
        self.assertIn('echo "IW3_FS_STARTUP_RUNTIME_INVOKED=false"', workflow)
        self.assertIn('echo "IW3_PLAYABLE_APK=false"', workflow)
        self.assertIn("for symbol in SEH_InitLanguage SEH_UpdateCurrentLanguage; do", workflow)
        self.assertIn("IW3_ORIGINAL_FS_STARTUP_LANGUAGE_INIT_AARCH64_LINK_GREEN", workflow)

if __name__ == "__main__":
    unittest.main()
