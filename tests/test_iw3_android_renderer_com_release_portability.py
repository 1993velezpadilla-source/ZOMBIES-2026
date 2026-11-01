"""Original IW3 D3D9 release helper ABI and Android fail-closed regression.

Host-only compile and sanitizer checks. These do NOT prove Android rendering.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_utils.h"
SOURCE = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_init.cpp"


class RendererComReleasePortabilityTests(unittest.TestCase):
    def test_release_helper_is_type_correct_and_compiles_with_opaque_d3d(self):
        header = HEADER.read_text(encoding="utf-8")
        self.assertEqual(header.count("template <typename T>"), 1)
        original_template = "template <typename T>" + header.split("template <typename T>", 1)[1]
        self.assertIn("T *var,", original_template)
        self.assertNotIn("IDirect3DSurface9 *var,", original_template)

        fixture = r"""
#include <cassert>
#include <cstdint>
#define __cdecl
#define iassert(x) assert(x)
struct IDirect3DSurface9; // Android opaque D3D9 declaration
struct FakeDevice {
    int refs = 1;
    int calls = 0;
    unsigned Release() { ++calls; return --refs; }
};
struct FakeSwapChain {
    int refs = 1;
    int calls = 0;
    unsigned Release() { ++calls; return --refs; }
};
struct FakeQuery {
    int refs = 1;
    int calls = 0;
    unsigned Release() { ++calls; return --refs; }
};
/* ORIGINAL_RELEASE_TEMPLATE */
int main() {
    FakeDevice device;
    FakeSwapChain swap;
    FakeQuery query;
    R_ReleaseAndSetNULL<FakeDevice>(&device, "device", "test", 1);
    R_ReleaseAndSetNULL<FakeSwapChain>(&swap, "swap", "test", 2);
    R_ReleaseAndSetNULL<FakeQuery>(&query, "query", "test", 3);
    assert(device.refs == 0 && device.calls == 1);
    assert(swap.refs == 0 && swap.calls == 1);
    assert(query.refs == 0 && query.calls == 1);
}
"""
        with tempfile.TemporaryDirectory() as tmp:
            cpp = Path(tmp) / "original_renderer_com_release.cpp"
            exe = Path(tmp) / "original_renderer_com_release"
            cpp.write_text(fixture.replace("/* ORIGINAL_RELEASE_TEMPLATE */", original_template), encoding="utf-8")
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-D__ANDROID__",
                 "-O1", "-g", "-fsanitize=address,undefined",
                 "-fno-omit-frame-pointer", str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30, env=env)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_original_renderer_does_not_fake_gpu_fences_or_release_d3d_on_android(self):
        source = SOURCE.read_text(encoding="utf-8")
        sync = function_source(source, "void __cdecl R_SyncGpu(int(__cdecl *WorkCallback)(unsigned __int64))")
        self.assertIn("#if defined(__ANDROID__)", sync)
        self.assertIn("GPU sync requires native GLES fence support", sync)
        self.assertIn("#else\n        dx.gpuSyncStart = __rdtsc();", sync)

        shutdown = function_source(source, "void R_ShutdownDirect3D()")
        self.assertIn("#if defined(__ANDROID__)", shutdown)
        self.assertIn("unexpected Direct3D9 object at shutdown", shutdown)
        self.assertIn("R_ReleaseAndSetNULL<IDirect3D9>(var,", shutdown)
        self.assertIn("R_ReleaseAndSetNULL<IDirect3DDevice9>(varCopy,", shutdown)

        reset = function_source(source, "void R_ReleaseForShutdownOrReset()")
        self.assertIn("#if defined(__ANDROID__)", reset)
        self.assertIn("D3D9 reset cleanup requires a GLES backend", reset)
        self.assertIn("R_ReleaseAndSetNULL<IDirect3DSwapChain9>(", reset)
        self.assertEqual(reset.count("R_ReleaseAndSetNULL<IDirect3DQuery9>("), 3)
        self.assertNotIn("(IDirect3DSurface9 *)", reset)
        self.assertIn("#endif // !__ANDROID__", reset)

        init = function_source(source, "void R_Init()")
        self.assertIn("#if !defined(__ANDROID__)", init)
        self.assertIn("dx.device->TestCooperativeLevel()", init)


if __name__ == "__main__":
    unittest.main()
