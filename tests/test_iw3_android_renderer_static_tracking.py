"""LP64 regression for the original IW3 renderer static-memory accounting.

Executes the unmodified TRACK_r_init function body from the real renderer source
with instrumented allocation tracking. Host-only: no graphics backend or gameplay.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_init.cpp"
SIGNATURE = "void __cdecl TRACK_r_init()"


class OriginalRendererTrackingLP64Tests(unittest.TestCase):
    def test_native_renderer_globals_are_accounted_by_sizeof(self):
        source = SOURCE.read_text(encoding="utf-8")
        original = function_source(source, SIGNATURE)
        for name in ("rgp", "rg", "vidConfig", "dx"):
            self.assertIn(f"sizeof({name})", original)
        for legacy in ('&rgp, 8576', '&rg, 33552', '&vidConfig, 48'):
            self.assertNotIn(legacy, original)

        fixture = r"""
#include <cassert>
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <vector>
#define __cdecl
struct RendererPermanent { void* materialPointers[12]; unsigned char payload[15]; };
struct RendererGlobal { void* world; void* lights[9]; unsigned char payload[47]; };
struct VideoConfig { void* displayHandle; int width; int height; float aspect; };
struct RendererDevice { void* device; void* swapchains[4]; int windowCount; };
RendererPermanent rgp{};
RendererGlobal rg{};
VideoConfig vidConfig{};
RendererDevice dx{};
struct Record { const void* address; size_t bytes; const char* name; int type; };
std::vector<Record> records;
void track_static_alloc_internal(void* address, int bytes, const char* name, int type) {
    assert(bytes > 0);
    records.push_back({address, static_cast<size_t>(bytes), name, type});
}
/* ORIGINAL_FUNCTION */
int main() {
    static_assert(sizeof(void*) == 8, "LP64 test required");
    TRACK_r_init();
    assert(records.size() == 4);
#define CHECK(i, obj) do { \
    assert(records[i].address == static_cast<const void*>(&(obj))); \
    assert(records[i].bytes == sizeof(obj)); \
    assert(records[i].type == 18); \
    assert(std::strcmp(records[i].name, #obj) == 0); \
} while (0)
    CHECK(0, rgp);
    CHECK(1, rg);
    CHECK(2, vidConfig);
    CHECK(3, dx);
    assert(records[0].bytes != 8576);
    assert(records[1].bytes != 33552);
    assert(records[2].bytes != 48);
    std::puts("IW3_ORIGINAL_RENDERER_STATIC_TRACKING_LP64_PASS");
}
"""
        with tempfile.TemporaryDirectory() as tmp:
            cpp = Path(tmp) / "iw3_original_renderer_tracking.cpp"
            exe = Path(tmp) / "iw3_original_renderer_tracking"
            cpp.write_text(fixture.replace("/* ORIGINAL_FUNCTION */", original), encoding="utf-8")
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(exe)], capture_output=True, text=True,
                                 timeout=30, env=env)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_RENDERER_STATIC_TRACKING_LP64_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
