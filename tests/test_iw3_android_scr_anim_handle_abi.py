"""Regression tests for the original IW3 scr_anim_s 32-bit payload on LP64."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "third_party/KisakCOD/src/bgame/bg_local.h"
FIXTURE = ROOT / "android/iw3-native/scr_anim_abi_native_test.cpp"
WORKFLOW = ROOT / ".github/workflows/iw3-original-native-android.yml"


class OriginalScrAnimHandleAbiTests(unittest.TestCase):
    def test_original_constructor_zero_extends_the_32_bit_payload(self):
        source = HEADER.read_text(encoding="utf-8")
        self.assertIn("static_cast<std::uintptr_t>(static_cast<std::uint32_t>(i))", source)
        self.assertIn("reinterpret_cast<const char *>", source)
        self.assertNotIn("linkPointer = (const char *)i", source)

    def test_native_fixture_executes_the_real_header_constructor_without_dereference(self):
        source = FIXTURE.read_text(encoding="utf-8")
        self.assertIn("#include <bgame/bg_local.h>", source)
        self.assertIn("std::bit_cast<int>(bits)", source)
        self.assertIn("reinterpret_cast<std::uintptr_t>(value.linkPointer)", source)
        self.assertIn("IW3_SCR_ANIM_HANDLE_ZERO_EXTEND_RUNTIME_PASS", source)
        self.assertNotIn("*value.linkPointer", source)

    def test_arm64_workflow_executes_host_fixture_and_compiles_same_source(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("scr_anim_abi_native_test.cpp", workflow)
        self.assertIn("IW3_ORIGINAL_SCR_ANIM_HANDLE_AARCH64_COMPILE_PASS", workflow)
        self.assertIn("IW3_SCR_ANIM_HANDLE_RUNTIME_LINKED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)


if __name__ == "__main__":
    unittest.main()
