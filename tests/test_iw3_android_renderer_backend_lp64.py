"""Real IW3 rb_backend.cpp LP64 tracking and Android D3D9 fence boundary.

Extracts ORIGINAL function bodies into an ASan/UBSan host harness. It does not
claim to render an Android frame or implement GLES synchronization.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/gfx_d3d/rb_backend.cpp"
TRACK_SIGNATURE = "void __cdecl TRACK_rb_backend()"
FENCE_SIGNATURES = (
    "bool __cdecl R_GpuFenceTimeout()",
    "void __cdecl R_FinishGpuFence()",
    "void __cdecl R_InsertGpuFence()",
    "void RB_AbandonGpuFence()",
)


class OriginalBackendLP64Tests(unittest.TestCase):
    def test_android_backend_headers_do_not_require_d3d9_or_bink(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("void __cdecl R_Cinematic_UpdateFrame();", source)
        self.assertIn('#include "r_cinematic.h"', source)
        self.assertIn("#if defined(__ANDROID__)", source)
        for name in ("rb_draw3d.h", "rb_backend.h"):
            header = (SOURCE.parent / name).read_text(encoding="utf-8")
            self.assertIn("#if defined(__ANDROID__)", header)
            self.assertIn('#include "r_d3d9_opaque.h"', header)
            self.assertIn("#else\n#include <d3d9.h>", header)

    def test_native_backend_static_tracking_with_sanitizers(self):
        src = SOURCE.read_text(encoding="utf-8")
        original = function_source(src, TRACK_SIGNATURE)
        for name in ("backEnd", "tess", "gfxCmdBufInput"):
            self.assertIn(f"sizeof({name})", original)
        for legacy in ('&backEnd, 640', '&tess, 2271584', '&gfxCmdBufInput, 1072'):
            self.assertNotIn(legacy, original)
        fixture = r"""
#include <cassert>
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <vector>
#define __cdecl
struct BackEnd { void* resources[17]; unsigned char data[35]; };
struct Tess { void* vertices; void* indices; unsigned char data[121]; };
struct CmdInput { void* shader; void* image[4]; int count; };
BackEnd backEnd{};
Tess tess{};
CmdInput gfxCmdBufInput{};
struct Record { const void* address; size_t bytes; const char* name; int kind; };
std::vector<Record> records;
void track_static_alloc_internal(void* p, int bytes, const char* name, int kind) {
    assert(bytes > 0);
    records.push_back({p, static_cast<size_t>(bytes), name, kind});
}
/* ORIGINAL */
int main() {
    static_assert(sizeof(void*) == 8, "LP64 host required");
    TRACK_rb_backend();
    assert(records.size() == 3);
#define CHECK(i, obj) do { \
    assert(records[i].address == static_cast<const void*>(&obj)); \
    assert(records[i].bytes == sizeof(obj)); \
    assert(records[i].kind == 18); \
    assert(std::strcmp(records[i].name, #obj) == 0); \
} while (0)
    CHECK(0, backEnd);
    CHECK(1, tess);
    CHECK(2, gfxCmdBufInput);
    std::puts("IW3_ORIGINAL_BACKEND_TRACKING_LP64_PASS");
}
"""
        self._build_and_run(fixture.replace("/* ORIGINAL */", original),
                            "IW3_ORIGINAL_BACKEND_TRACKING_LP64_PASS")

    def test_android_gpu_fence_operations_fail_closed_without_gles_sync(self):
        src = SOURCE.read_text(encoding="utf-8")
        originals = []
        for signature in FENCE_SIGNATURES:
            original = function_source(src, signature)
            self.assertIn("#if defined(__ANDROID__)", original, signature)
            self.assertIn("Com_Error(ERR_FATAL", original, signature)
            self.assertIn("#else", original, signature)
            originals.append(original)
        self.assertIn("__rdtsc()", originals[0])  # Windows code preserved
        self.assertIn("dx.flushGpuQuery->Issue(1)", originals[2])
        fixture = r"""
#include <cassert>
#include <cstdio>
#include <stdexcept>
#define __cdecl
#define __ANDROID__ 1
enum { ERR_FATAL = 1 };
void Com_Error(int kind, const char* message, ...) {
    assert(kind == ERR_FATAL);
    if (!message || !*message) std::abort();
    throw std::runtime_error(message);
}
/* ORIGINAL */
template <typename Func>
void must_fail(Func f) {
    try { f(); } catch (const std::runtime_error&) { return; }
    std::abort();
}
int main() {
    must_fail([] { (void)R_GpuFenceTimeout(); });
    must_fail([] { R_FinishGpuFence(); });
    must_fail([] { R_InsertGpuFence(); });
    must_fail([] { RB_AbandonGpuFence(); });
    std::puts("IW3_ORIGINAL_BACKEND_D3D9_FENCE_FAIL_CLOSED_PASS");
}
"""
        fixture = fixture.replace("#include <stdexcept>", "#include <stdexcept>\n#include <cstdlib>")
        self._build_and_run(fixture.replace("/* ORIGINAL */", "\n".join(originals)),
                            "IW3_ORIGINAL_BACKEND_D3D9_FENCE_FAIL_CLOSED_PASS")

    def test_original_d3d9_only_backend_paths_fail_closed_on_android(self):
        # Execute the genuine IW3 functions, not a replacement renderer.
        # Android must not accidentally dereference opaque D3D9 interfaces.
        signatures = (
            "void __cdecl R_Resolve(GfxCmdBufContext context, GfxImage *image)",
            "void __cdecl RB_StretchRaw(int x, int y, int w, int h, int cols, int rows, const uint8_t *data)",
            "void __cdecl RB_SetGammaRamp(const GfxGammaRamp *gammaTable)",
            "void __cdecl RB_BeginFrame(const GfxBackEndData *data)",
            "GfxIndexBufferState *RB_SwapBuffers()",
            "int RB_AdaptiveGpuSyncFinal()",
            "int __cdecl RB_BackendTimeout()",
        )
        src = SOURCE.read_text(encoding="utf-8")
        originals = []
        for signature in signatures:
            original = function_source(src, signature)
            self.assertIn("#if defined(__ANDROID__)", original, signature)
            self.assertIn("Com_Error(ERR_FATAL", original, signature)
            self.assertIn("#else", original, signature)
            originals.append(original)
        self.assertIn("StretchRect(", originals[0])
        self.assertIn("CreateOffscreenPlainSurface(", originals[1])
        self.assertIn("SetGammaRamp(", originals[2])
        self.assertIn("BeginScene()", originals[3])
        self.assertIn("swapChain->Present(", originals[4])
        self.assertIn("__rdtsc()", originals[5])
        self.assertIn("swapFence->GetData(", originals[6])
        fixture = r"""
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#define __cdecl
#define __ANDROID__ 1
enum { ERR_FATAL = 1 };
struct GfxCmdBufContext { void* source; void* state; };
struct GfxImage;
struct GfxGammaRamp;
struct GfxBackEndData;
struct GfxIndexBufferState;
void Com_Error(int kind, const char* message, ...) {
    assert(kind == ERR_FATAL);
    assert(message && *message);
    throw std::runtime_error(message);
}
/* ORIGINAL */
template <typename Func>
void must_fail(Func f) {
    try { f(); } catch (const std::runtime_error&) { return; }
    std::abort();
}
int main() {
    must_fail([] { R_Resolve({}, nullptr); });
    must_fail([] { RB_StretchRaw(0, 0, 1, 1, 1, 1, nullptr); });
    must_fail([] { RB_SetGammaRamp(nullptr); });
    must_fail([] { RB_BeginFrame(nullptr); });
    must_fail([] { (void)RB_SwapBuffers(); });
    must_fail([] { (void)RB_AdaptiveGpuSyncFinal(); });
    must_fail([] { (void)RB_BackendTimeout(); });
    std::puts("IW3_ORIGINAL_BACKEND_D3D9_BOUNDARY_PASS");
}
"""
        self._build_and_run(fixture.replace("/* ORIGINAL */", "\n".join(originals)),
                            "IW3_ORIGINAL_BACKEND_D3D9_BOUNDARY_PASS")

    def test_original_command_consumer_keeps_dispatch_and_guards_d3d9_endscene(self):
        original = function_source(
            SOURCE.read_text(encoding="utf-8"),
            "void __cdecl RB_CallExecuteRenderCommands()")
        dispatch = original.index("RB_ExecuteRenderCommandsLoop(backEndData->cmds)")
        boundary = original.index("#if defined(__ANDROID__)", dispatch)
        fatal = original.index(
            "IW3 Android RB_CallExecuteRenderCommands requires GLES scene end",
            boundary)
        windows = original.index("#else", fatal)
        endscene = original.index("hr = dx.device->EndScene();", windows)
        self.assertLess(dispatch, boundary)
        self.assertLess(boundary, fatal)
        self.assertLess(fatal, windows)
        self.assertLess(windows, endscene)
        self.assertIn("#endif", original[endscene:])

    def _build_and_run(self, source, expected):
        with tempfile.TemporaryDirectory() as tmp:
            cpp = Path(tmp) / "iw3_original_backend.cpp"
            exe = Path(tmp) / "iw3_original_backend"
            cpp.write_text(source, encoding="utf-8")
            built = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++20", "-O1", "-g",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            ran = subprocess.run([str(exe)], capture_output=True, text=True,
                                 env=env, timeout=30)
            self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
            self.assertIn(expected, ran.stdout)


if __name__ == "__main__":
    unittest.main()
