"""Execute genuine IW3 renderer display-mode enumeration on an LP64 host.

Only D3D enumeration and dvar registration are test doubles. The renderer
functions themselves are extracted unchanged from KisakCOD. The genuine
platform-neutral dvar builder is also exercised without D3D. NOT a game.
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
    "int __cdecl R_CompareRefreshRates(const void *lhs, const void *rhs)",
    "int __cdecl R_AddValidResolution(int width, int height, int resolutionCount, int (*availableResolutions)[2])",
    "int __cdecl R_CompareDisplayModes(const void *lhs, const void *rhs)",
    "int __cdecl R_AddValidRefreshRate(int refreshRate, int rateCount, int *availableRefreshRates)",
    "void __cdecl R_BuildDisplayModeDvars()",
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
#include <utility>
#include <type_traits>
#define __cdecl
#define iassert(x) assert(x)
using _DWORD = uint32_t;
using HRESULT = int;
enum { D3DFMT_X8R8G8B8 = 21, DVAR_ARCHIVE = 1, DVAR_LATCH = 2, DVAR_AUTOEXEC = 4 };
struct dvar_t {};
struct Mode { uint32_t Width, Height, RefreshRate, Format; };
using _D3DDISPLAYMODE = Mode; // exact 16-byte ABI of the original renderer mode type
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
int enumRegistrations = 0;
const dvar_t *Dvar_RegisterEnum(const char *name, const char **values,
                                int, int, const char *) {
    ++enumRegistrations;
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
    static_assert(sizeof(Mode) == 4 * sizeof(uint32_t), "D3D display mode ABI");
    static_assert(std::is_same_v<decltype(&R_CompareRefreshRates),
                  int (*)(const void *, const void *)>, "refresh qsort ABI");
    static_assert(std::is_same_v<decltype(&R_CompareDisplayModes),
                  int (*)(const void *, const void *)>, "display qsort ABI");
    // qsort comparators must be antisymmetric even at the uint32_t extremes.
    // Subtracting DWORDs used to wrap and invert the ordering.
    uint32_t low = 1u, high = 0xffffffffu;
    assert(R_CompareRefreshRates(&low, &high) < 0);
    assert(R_CompareRefreshRates(&high, &low) > 0);
    assert(R_CompareRefreshRates(&high, &high) == 0);
    uint32_t lowWidth[3] = {1u, 480u, 60u};
    uint32_t highWidth[3] = {0xffffffffu, 480u, 60u};
    uint32_t lowHeight[3] = {640u, 1u, 60u};
    uint32_t highHeight[3] = {640u, 0xffffffffu, 60u};
    uint32_t lowRefresh[3] = {640u, 480u, 1u};
    uint32_t highRefresh[3] = {640u, 480u, 0xffffffffu};
    for (auto pair : {std::pair<uint32_t*, uint32_t*>{lowWidth, highWidth},
                      {lowHeight, highHeight}, {lowRefresh, highRefresh}}) {
        assert(R_CompareDisplayModes(pair.first, pair.second) < 0);
        assert(R_CompareDisplayModes(pair.second, pair.first) > 0);
        assert(R_CompareDisplayModes(pair.first, pair.first) == 0);
    }
    // Exercise real qsort invocation ABI, not just direct comparator calls.
    uint32_t unsortedRates[] = {0xffffffffu, 60u, 0u, 144u, 1u};
    qsort(unsortedRates, 5, sizeof(unsortedRates[0]), R_CompareRefreshRates);
    assert((std::vector<uint32_t>(unsortedRates, unsortedRates + 5) ==
            std::vector<uint32_t>{0u, 1u, 60u, 144u, 0xffffffffu}));
    Mode unsortedModes[] = {{1920, 1080, 144, 21}, {640, 480, 60, 21},
                            {1920, 1080, 60, 21}, {800, 600, 75, 21}};
    qsort(unsortedModes, 4, sizeof(unsortedModes[0]), R_CompareDisplayModes);
    assert(unsortedModes[0].Width == 640u);
    assert(unsortedModes[1].Width == 800u);
    assert(unsortedModes[2].RefreshRate == 60u);
    assert(unsortedModes[3].RefreshRate == 144u);
    // These are the exact fixed capacities supplied by the original renderer.
    // Previously, a full helper call appended past the end of either table.
    int fullResolutions[256][2]{};
    assert(R_AddValidResolution(1920, 1080, 255, fullResolutions) == 256);
    assert(fullResolutions[255][0] == 1920 && fullResolutions[255][1] == 1080);
    assert(R_AddValidResolution(2560, 1440, 256, fullResolutions) == 256);
    int fullRefreshRates[257]{};
    assert(R_AddValidRefreshRate(120, 256, fullRefreshRates) == 257);
    assert(fullRefreshRates[256] == 120);
    assert(R_AddValidRefreshRate(240, 257, fullRefreshRates) == 257);
    D3D api;
    dx.d3d9 = &api;
    api.modes = {{1920,1080,144,21}, {800,600,60,21},
                 {1920,1080,60,21}, {1280,720,75,21}, {640,480,60,21}};
#if defined(__ANDROID__)
    // Real Android mode provider supplies these modes before enumeration.
    dx.displayModeCount = static_cast<uint32_t>(api.modes.size());
    for (size_t i = 0; i < api.modes.size(); ++i)
        dx.displayModes[i] = api.modes[i];
    // Match the genuine Android provider: apply registers the dvars first.
    R_BuildDisplayModeDvars();
    const int registrationsBeforeEnum = enumRegistrations;
#endif
    R_EnumDisplayModes(0);
#if defined(__ANDROID__)
    assert(enumRegistrations == registrationsBeforeEnum); // no double registration
#endif
    assert((resolutions == std::vector<std::string>{
        "640x480", "800x600", "1280x720", "1920x1080"}));
    assert((refreshes == std::vector<std::string>{"60 Hz", "75 Hz", "144 Hz"}));
    assert(dx.displayModeCount == 5);
    assert(r_mode && r_displayRefresh && r_noborder);
    api.modes.clear();
    for (uint32_t i = 0; i < 256; ++i)
        api.modes.push_back({640 + i, 480, 60, 21});
#if defined(__ANDROID__)
    dx.displayModeCount = static_cast<uint32_t>(api.modes.size());
    for (size_t i = 0; i < api.modes.size(); ++i)
        dx.displayModes[i] = api.modes[i];
    // Match the genuine Android provider: apply registers the dvars first.
    R_BuildDisplayModeDvars();
    const int registrationsBeforeEnumFull = enumRegistrations;
#endif
    R_EnumDisplayModes(0);
#if defined(__ANDROID__)
    assert(enumRegistrations == registrationsBeforeEnumFull); // no double registration
#endif
    assert(resolutions.size() == 256);
    assert(resolutions.front() == "640x480");
    assert(resolutions.back() == "895x480");
    assert(refreshes.size() == 1 && refreshes[0] == "60 Hz");
    // Platform-neutral path: real renderer dvar logic must consume a native
    // provider's populated mode array without dereferencing Direct3D9.
    dx.d3d9 = nullptr;
    dx.displayModeCount = 3;
    dx.displayModes[0] = {1600, 900, 120, 21};
    dx.displayModes[1] = {800, 600, 60, 21};
    dx.displayModes[2] = {1600, 900, 60, 21};
    R_BuildDisplayModeDvars();
    assert((resolutions == std::vector<std::string>{"800x600", "1600x900"}));
    assert((refreshes == std::vector<std::string>{"60 Hz", "120 Hz"}));
    // Same genuine renderer function, compiled for each platform: desktop
    // rejects phone-sized modes; Android accepts physical portrait/landscape.
    dx.displayModeCount = 2;
    dx.displayModes[0] = {360, 800, 60, 0};
    dx.displayModes[1] = {800, 360, 60, 0};
#if defined(__ANDROID__)
    assert(R_AddValidResolution(360, 800, 0, fullResolutions) == 1);
    assert(R_AddValidResolution(319, 800, 0, fullResolutions) == 0);
    R_BuildDisplayModeDvars();
    assert((resolutions == std::vector<std::string>{"360x800", "800x360"}));
    assert((refreshes == std::vector<std::string>{"60 Hz"}));
#else
    assert(R_AddValidResolution(360, 800, 0, fullResolutions) == 0);
    bool narrowRejected = false;
    try { R_BuildDisplayModeDvars(); }
    catch (const std::runtime_error &) { narrowRejected = true; }
    assert(narrowRejected);
#endif
    dx.displayModeCount = 257;
    bool overflowRejected = false;
    try { R_BuildDisplayModeDvars(); }
    catch (const std::runtime_error &) { overflowRejected = true; }
    assert(overflowRejected);
    dx.d3d9 = &api;
    api.modes.clear();
#if defined(__ANDROID__)
    dx.displayModeCount = 0; // No Surface mode applied: must reject.
#endif
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
        self.assertIn("adapter enumeration does not exist on Android.", functions)
        self.assertIn("Android renderer Surface mode must be applied first", functions)
        self.assertIn("!r_mode || !r_displayRefresh", functions)
        self.assertIn("authentic GLES renderer command backend not integrated.", source)
        self.assertIn("dx.displayModes[modeIndex].RefreshRate", functions)
        self.assertNotIn("resolutionNameTable[4 *", functions)
        self.assertNotIn("(int)dx.resolutionNameTable", functions)
        self.assertIn("sizeof(dx.displayModes[0]), R_CompareDisplayModes", source)
        self.assertIn("sizeof(availableRefreshRates[0]), R_CompareRefreshRates", source)
        self.assertNotIn("(int(__cdecl *)(const void *, const void *))R_Compare", source)
        cpp_source = HARNESS.replace("/* ORIGINAL_RENDERER_FUNCTIONS */", functions)
        with tempfile.TemporaryDirectory() as temp:
            cpp = Path(temp) / "renderer_modes.cpp"
            cpp.write_text(cpp_source, encoding="utf-8")
            for platform, flags in (("desktop", []), ("android", ["-D__ANDROID__"])):
                with self.subTest(platform=platform):
                    exe = Path(temp) / ("renderer_modes_" + platform)
                    build = subprocess.run(
                        [os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
                         "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                         *flags, str(cpp), "-o", str(exe)],
                        capture_output=True, text=True, timeout=90)
                    self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
                    env = os.environ.copy()
                    env["ASAN_OPTIONS"] = "detect_leaks=1"
                    run = subprocess.run([str(exe)], capture_output=True, text=True,
                                         timeout=30, env=env)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                    self.assertIn("IW3_ORIGINAL_RENDERER_DISPLAY_MODES_LP64_PASS", run.stdout)


    def test_android_precreate_window_fails_closed_without_gles_draw_backend(self):
        """Compile and execute the ORIGINAL startup function on an LP64 host.

        Native Surface mode support must never accidentally report a working
        IW3 renderer while the genuine GLES draw-command backend is absent.
        """
        source = SOURCE.read_text(encoding="utf-8")
        original = function_source(source, "char __cdecl R_PreCreateWindow()")
        harness = r"""
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#define __cdecl
constexpr int CON_CHANNEL_GFX = 0;
char captured[512]{};
void Com_Printf(int, const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    vsnprintf(captured, sizeof(captured), fmt, args);
    va_end(args);
}
/* ORIGINAL_PRECREATE */
int main() {
    static_assert(sizeof(void *) == 8, "LP64 host required");
    assert(R_PreCreateWindow() == 0);
    assert(strstr(captured, "authentic GLES renderer command backend not integrated"));
}
""".replace("/* ORIGINAL_PRECREATE */", original)
        with tempfile.TemporaryDirectory() as temp:
            cpp = Path(temp) / "iw3_precreate_android.cpp"
            exe = Path(temp) / "iw3_precreate_android"
            cpp.write_text(harness, encoding="utf-8")
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
                 "-D__ANDROID__", "-fsanitize=address,undefined",
                 "-fno-omit-frame-pointer", str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run([str(exe)], capture_output=True, text=True,
                                 timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

if __name__ == "__main__":
    unittest.main()
