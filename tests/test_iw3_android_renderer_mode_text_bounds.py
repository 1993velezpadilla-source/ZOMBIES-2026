"""Executable ASan/UBSan regression for the original renderer display-name writes.

Extracts the exact two snprintf/remaining-capacity blocks from R_EnumDisplayModes.
This is not an Android renderer or a real display-mode enumeration test.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_init.cpp"


class OriginalRendererModeTextBoundsTests(unittest.TestCase):
    def test_original_mode_and_refresh_formatting_under_asan_ubsan(self):
        original = function_source(
            SOURCE.read_text(encoding="utf-8"),
            "void __cdecl R_EnumDisplayModes(uint32_t adapterIndex)",
        )
        mode = re.search(
            r"const size_t modeTextRemaining = .*?modeText \+= v2 \+ 1;",
            original, re.S,
        )
        refresh = re.search(
            r"const size_t refreshTextRemaining = .*?modeText \+= v3 \+ 1;",
            original, re.S,
        )
        self.assertIsNotNone(mode)
        self.assertIsNotNone(refresh)
        self.assertNotIn("ARRAYSIZE(dx.modeText)", original)
        self.assertIn("modeText - dx.modeText", mode.group())
        self.assertIn("modeText - dx.modeText", refresh.group())

        fixture = r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
struct RendererDevice { char modeText[5120]; } dx{};
int availableResolutions[256][2]{};
int availableRefreshRates[257]{};
bool fatal = false;
void R_FatalInitError(const char*) { fatal = true; }
void run_mode_names(bool huge) {
    std::memset(dx.modeText, 0, sizeof(dx.modeText));
    fatal = false;
    for (int i = 0; i < 256; ++i) {
        availableResolutions[i][0] = huge ? 2147483647 : 640;
        availableResolutions[i][1] = huge ? 2147483647 : 480;
        availableRefreshRates[i] = 60;
    }
    char *modeText = dx.modeText;
    int v2 = 0, v3 = 0;
    for (int resolutionIndex = 0; resolutionIndex < 256; ++resolutionIndex) {
        /* ORIGINAL_MODE_BLOCK */
    }
    for (int refreshRateIndex = 0; refreshRateIndex < 256; ++refreshRateIndex) {
        /* ORIGINAL_REFRESH_BLOCK */
    }
}
int main() {
    static_assert(sizeof(void*) == 8, "LP64 required");
    run_mode_names(false);
    assert(!fatal);
    run_mode_names(true);
    assert(fatal);
    std::puts("IW3_ORIGINAL_RENDERER_MODE_TEXT_BOUNDS_LP64_PASS");
}
"""
        fixture = fixture.replace("/* ORIGINAL_MODE_BLOCK */", mode.group())
        fixture = fixture.replace("/* ORIGINAL_REFRESH_BLOCK */", refresh.group())
        with tempfile.TemporaryDirectory() as tmp:
            cpp = Path(tmp) / "iw3_renderer_mode_bounds.cpp"
            exe = Path(tmp) / "iw3_renderer_mode_bounds"
            cpp.write_text(fixture, encoding="utf-8")
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
            self.assertIn("IW3_ORIGINAL_RENDERER_MODE_TEXT_BOUNDS_LP64_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
