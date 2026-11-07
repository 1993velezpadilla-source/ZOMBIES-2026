"""Guard the original IW3 four-slot TLS platform boundary and CI proof.

This checks a genuine AArch64 symbol provider, not an Android gameplay APK.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT / "android/iw3-native"
WORKFLOW = ROOT / ".github/workflows/iw3-command-full-arm64.yml"


class OriginalThreadValueAbiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider = (PLATFORM / "iw3_android_thread_values.cpp").read_text()
        cls.fixture = (PLATFORM / "tests/thread_values_native_test.cpp").read_text()
        cls.workflow = WORKFLOW.read_text()

    def test_original_four_slots_and_thread_local_binding(self):
        self.assertIn("g_threadValues[THREAD_CONTEXT_COUNT][4]", self.provider)
        self.assertIn("thread_local void** s_threadLocals", self.provider)
        self.assertIn("Sys_SetValue(int valueIndex, void* data)", self.provider)
        self.assertIn("Sys_GetValue(int valueIndex)", self.provider)
        self.assertIn("index >= kThreadValueSlots", self.provider)
        self.assertIn("IW3_AndroidBindThreadContext", self.provider)

    def test_real_setjmp_and_two_thread_contexts(self):
        for text in ("setjmp(jump)", "longjmp(*static_cast<jmp_buf*>",
                     "THREAD_CONTEXT_MAIN", "THREAD_CONTEXT_SERVER",
                     "std::thread server", "IW3_AndroidThreadHasErrorJump"):
            self.assertIn(text, self.fixture)

    def test_aarch64_link_gate_keeps_renderer_unresolved(self):
        for text in ("iw3_android_thread_values.cpp",
                     "thread_values_native_test.cpp",
                     "IW3_ANDROID_THREAD_VALUES_HOST_SETJMP_TLS_PASS",
                     "IW3_ORIGINAL_SYS_GETVALUE_AARCH64_PROVIDER_RESOLVED",
                     "IW3_ORIGINAL_RENDERER_RUNTIME_PROVIDER_MISSING",
                     " U CL_InitRenderer()", "IW3_PLAYABLE_APK=false"):
            self.assertIn(text, self.workflow)
        self.assertNotIn("IW3_PLAYABLE_APK=true", self.workflow)


if __name__ == "__main__":
    unittest.main()
