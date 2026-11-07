"""Host-execute the original IW3 Com_InitThreadData body with the Android ABI.

Extracts the *verbatim* original function and type definitions; the actual
AArch64 workflow separately compiles the complete original q_shared.cpp.
Neither gate invokes Com_Init or proves a playable APK.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD/src"
PLATFORM = ROOT / "android/iw3-native"


class OriginalMainThreadSharedData(unittest.TestCase):
    def test_verbatim_original_thread_data_initializes_android_context(self):
        source = (ENGINE / "universal/q_shared.cpp").read_text()
        header = (ENGINE / "universal/q_shared.h").read_text()
        adapter = (PLATFORM / "iw3_android_main_thread_shared.cpp").read_text()
        start = source.index("void __cdecl Com_InitThreadData(int threadContext)")
        end = source.index("\nstatic int valueindex;", start)
        original_body = source[start:end]
        self.assertIn("Sys_SetValue(1, &va_info[threadContext]);", original_body)
        self.assertIn("Sys_SetValue(2, &g_com_error[threadContext]);", original_body)
        self.assertIn("Sys_SetValue(3, &g_traceThreadInfo[threadContext]);", original_body)
        type_start = header.index("struct va_info_t\n")
        type_end = header.index("\nenum TraceHitType", type_start)
        original_types = header[type_start:type_end]
        globals_start = source.index("va_info_t va_info[THREAD_CONTEXT_COUNT];")
        globals_end = source.index("\n#ifdef KISAK_MP", globals_start)
        original_globals = source[globals_start:globals_end]
        adapter_start = adapter.index("bool IW3_AndroidBindMainThreadSharedData()")
        original_adapter = adapter[adapter_start:]
        fixture = r"""
#include <qcommon/thread_context.h>
#include "iw3_android_thread_values.h"
#include <cstdint>
#include <csetjmp>
#include <cassert>
#ifndef __cdecl
#define __cdecl
#endif
struct cbrush_t;
struct cmodel_t;
void Sys_SetValue(int, void*);
void* Sys_GetValue(int);
""" + original_types + "\n" + original_globals + "\n" + original_body + "\n" + original_adapter + r"""
int main() {
    assert(!IW3_AndroidThreadHasErrorJump());
    assert(IW3_AndroidBindMainThreadSharedData());
    assert(IW3_AndroidThreadHasErrorJump());
    assert(Sys_GetValue(0) == nullptr); // Profile stack is NOT initialized.
    assert(Sys_GetValue(1) == &va_info[THREAD_CONTEXT_MAIN]);
    assert(Sys_GetValue(2) == &g_com_error[THREAD_CONTEXT_MAIN]);
    assert(Sys_GetValue(3) == &g_traceThreadInfo[THREAD_CONTEXT_MAIN]);
    volatile int result = setjmp(*static_cast<jmp_buf*>(Sys_GetValue(2)));
    if (result == 0) {
        longjmp(*static_cast<jmp_buf*>(Sys_GetValue(2)), 9);
    }
    assert(result == 9);
    IW3_AndroidUnbindThreadContext();
    assert(!IW3_AndroidThreadHasErrorJump());
    return 0;
}
"""
        compiler = shutil.which("c++")
        self.assertIsNotNone(compiler)
        with tempfile.TemporaryDirectory() as directory:
            source_file = Path(directory) / "original_thread_data.cpp"
            executable = Path(directory) / "original_thread_data"
            source_file.write_text(fixture)
            subprocess.run(
                [compiler, "-std=c++20", "-DKISAK_SP=1", "-UNDEBUG",
                 "-Wall", "-Wextra", "-Werror", "-O1",
                 "-fsanitize=undefined", "-fno-omit-frame-pointer", "-pthread",
                 "-I", str(ENGINE), "-I", str(PLATFORM),
                 str(source_file), str(PLATFORM / "iw3_android_thread_values.cpp"),
                 "-o", str(executable)],
                check=True, capture_output=True, text=True, timeout=45)
            subprocess.run([str(executable)], check=True, capture_output=True,
                           text=True, timeout=15)

    def test_original_main_binding_remains_non_game(self):
        workflow = (ROOT / ".github/workflows/iw3-command-full-arm64.yml").read_text()
        self.assertIn("IW3_ANDROID_MAIN_SHARED_DATA_ORIGINAL_OWNER_LINK_PASS", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)
        self.assertNotIn("IW3_PLAYABLE_APK=true", workflow)


if __name__ == "__main__":
    unittest.main()
