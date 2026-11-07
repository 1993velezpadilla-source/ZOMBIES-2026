"""Execute original IW3 GPU-query Android guards with host sanitizers.

A guarded compile is not GLsync integration, a rendered frame, or gameplay.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_setstate_d3d.cpp"
SIGNATURES = (
    "bool __cdecl RB_IsGpuFinished()",
    "bool __cdecl RB_IsGpuFenceFinished()",
)


class OriginalGpuQueryBoundaryTests(unittest.TestCase):
    def test_original_d3d9_gpu_queries_fail_closed_on_android(self):
        src = SOURCE.read_text(encoding="utf-8")
        originals = []
        for signature in SIGNATURES:
            body = function_source(src, signature)
            self.assertIn("#if defined(__ANDROID__)", body)
            self.assertIn("Com_Error(ERR_FATAL", body)
            self.assertIn("#else", body)
            self.assertIn("#endif", body)
            originals.append(body)
        self.assertIn("dx.flushGpuQuery->GetData(0, 0, 1)", originals[0])
        self.assertIn("dx.flushGpuQueryIssued", originals[1])
        fixture = r"""
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#define __cdecl
#define __ANDROID__ 1
enum { ERR_FATAL = 1 };
void Com_Error(int kind, const char* message, ...) {
    assert(kind == ERR_FATAL);
    assert(message && *message);
    throw std::runtime_error(message);
}
enum class IW3AndroidGpuFenceResult { Invalid, Idle, Pending, Complete };
IW3AndroidGpuFenceResult R_AndroidGpuFenceOriginalPoll() { return IW3AndroidGpuFenceResult::Invalid; }
/* ORIGINAL */
int main() {
    bool caught = false;
    try { (void)RB_IsGpuFinished(); }
    catch (const std::runtime_error&) { caught = true; }
    assert(caught);
    caught = false;
    try { (void)RB_IsGpuFenceFinished(); }
    catch (const std::runtime_error&) { caught = true; }
    assert(caught);
    std::puts("IW3_ORIGINAL_GPU_QUERY_ANDROID_FAIL_CLOSED_PASS");
}
"""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "gpu_query.cpp"
            exe = Path(tmp) / "gpu_query"
            source.write_text(fixture.replace("/* ORIGINAL */", "\n".join(originals)), encoding="utf-8")
            built = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++20", "-O1", "-g",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(source), "-o", str(exe)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            ran = subprocess.run([str(exe)], capture_output=True, text=True,
                                 env=env, timeout=30)
            self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
            self.assertIn("IW3_ORIGINAL_GPU_QUERY_ANDROID_FAIL_CLOSED_PASS", ran.stdout)


if __name__ == "__main__":
    unittest.main()
