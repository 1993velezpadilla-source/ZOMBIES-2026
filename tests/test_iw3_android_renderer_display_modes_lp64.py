"""Execute genuine IW3 renderer display-mode enumeration on an LP64 host.

Only D3D enumeration and dvar registration are test doubles. The renderer
functions themselves are extracted unchanged from KisakCOD. NOT a game.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_init.cpp"
SIGNATURES = (
    "int __cdecl R_CompareRefreshRates(_DWORD *e0, _DWORD *e1)",
    "int __cdecl R_AddValidResolution(int width, int height, int resolutionCount, int (*availableResolutions)[2])",
    "int __cdecl R_CompareDisplayModes(_DWORD *e0, _DWORD *e1)",
    "int __cdecl R_AddValidRefreshRate(int refreshRate, int rateCount, int *availableRefreshRates)",
    "void __cdecl R_EnumDisplayModes(uint32_t adapterIndex)",
)

HARNESS = r"""
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>
#define __cdecl
#define iassert(x) assert(x)
using _DWORD = uint32_t;
using HRESULT = int;
enum { D3DFMT_X8R8G8B8 = 21, DVAR_ARCHIVE = 1, DVAR_LATCH = 2, DVAR_AUTOEXEC = 4 };
struct dvar_t {};
struct Mode { uint32_t Width, Height, RefreshRate, Format; };
struct D3D {
    std::vector<Mode> modes;
    uint32_t GetAdapterModeCount(uint32_t, int) { return static_cast<uint32_t>(modes.size()); }
    HRESULT EnumAdapterModes(uint32_t, int, uint32_t index, Mode *out) {
        if (index >= modes.size()) return -1;
        *out = modes[index];
        return 0;
    }
};
struct Dx {
    D3D *d3d9 = nullptr;
    uint32_t displayModeCount = 0;
    Mode displayModes[256]{};
    const char *resolutionNameTable[257]{};
    const char *refreshRateNameTable[257]{};
    char modeText[5120]{};
} dx;
const dvar_t *r_mode = nullptr, *r_displayRefresh = nullptr, *r_noborder = nullptr;
std::vector<std::string> resolutions, refreshes;
const dvar_t *Dvar_RegisterEnum(const char *name, const char **values,
                                int, int, const char *) {
    auto &dst = std::strcmp(name, "r_mode") == 0 ? resolutions : refreshes;
    dst.clear();
    for (size_t i = 0; values[i]; ++i) {
        assert(i < 257);
        dst.emplace_back(values[i]);
    }
    static dvar_t result;
    return &result;
}
const dvar_t *Dvar_RegisterBool(const char *, bool, int, const char *) {
    static dvar_t result;
    return &result;
}
const char *va(const char *, int, int) { return "No valid modes"; }
[[noreturn]] void R_FatalInitError(const char *msg) { throw std::runtime_error(msg); }
/* ORIGINAL_RENDERER_FUNCTIONS */
int main() {
    static_assert(sizeof(void *) == 8, "LP64 test required");
    D3D api;
    dx.d3d9 = &api;
    api.modes = {{1920,1080,144,21}, {800,600,60,21},
                 {1920,1080,60,21}, {1280,720,75,21}, {640,480,60,21}};
    R_EnumDisplayModes(0);
    assert((resolutions == std::vector<std::string>{
        "640x480", "800x600", "1280x720", "1920x1080"}));
    assert((refreshes == std::vector<std::string>{"60 Hz", "75 Hz", "144 Hz"}));
    assert(dx.displayModeCount == 5);
    assert(r_mode && r_displayRefresh && r_noborder);
    api.modes.clear();
    for (uint32_t i = 0; i < 256; ++i)
        api.modes.push_back({640 + i, 480, 60, 21});
    R_EnumDisplayModes(0);
    assert(resolutions.size() == 256);
    assert(resolutions.front() == "640x480");
    assert(resolutions.back() == "895x480");
    assert(refreshes.size() == 1 && refreshes[0] == "60 Hz");
    api.modes.clear();
    bool rejected = false;
    try { R_EnumDisplayModes(0); }
    catch (const std::runtime_error &) { rejected = true; }
    assert(rejected);
    std::puts("IW3_ORIGINAL_RENDERER_DISPLAY_MODES_LP64_PASS");
}
"""

class OriginalRendererDisplayModesLP64(unittest.TestCase):
    def test_native_display_fields_and_full_enumeration_under_sanitizers(self):
        source = SOURCE.read_text(encoding="utf-8")
        functions = "\n".join(function_source(source, s) for s in SIGNATURES)
        self.assertIn("dx.displayModes[modeIndex].Height", functions)
        self.assertIn("dx.displayModes[modeIndex].RefreshRate", functions)
        self.assertNotIn("resolutionNameTable[4 *", functions)
        self.assertNotIn("(int)dx.resolutionNameTable", functions)
        cpp_source = HARNESS.replace("/* ORIGINAL_RENDERER_FUNCTIONS */", functions)
        with tempfile.TemporaryDirectory() as temp:
            cpp = Path(temp) / "renderer_modes.cpp"
            exe = Path(temp) / "renderer_modes"
            cpp.write_text(cpp_source, encoding="utf-8")
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(exe)], capture_output=True, text=True,
                                 timeout=30, env=env)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_RENDERER_DISPLAY_MODES_LP64_PASS", run.stdout)

if __name__ == "__main__":
    unittest.main()
