"""Execute the real IW3 Android Surface/Display mode provider under LP64 ASan/UBSan.

JNI and ANativeWindow are mocked; the extracted provider function is unchanged.
This proves argument validation and native mode population, NOT device rendering.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_android_display.cpp"
SIGNATURES = (
    "bool R_AndroidReadSurfaceMode(JNIEnv *env, jobject surface, jobject display,",
    "bool R_AndroidApplySurfaceMode(const IW3AndroidSurfaceMode &mode)",
    "bool R_AndroidPopulateDisplayMode(JNIEnv *env, jobject surface, jobject display)",
)

HARNESS = r"""
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
using jobject = void *;
using jclass = void *;
using jmethodID = void *;
struct ANativeWindow { int width; int height; };
enum _D3DFORMAT { UNKNOWN_ANDROID_FORMAT = 0 };
struct _D3DDISPLAYMODE {
    uint32_t Width = 0, Height = 0, RefreshRate = 0;
    _D3DFORMAT Format = UNKNOWN_ANDROID_FORMAT;
};
struct IW3AndroidSurfaceMode {
    uint32_t width, height, refreshHz;
};
struct {
    _D3DDISPLAYMODE displayModes[256]{};
    uint32_t displayModeCount = 0;
} dx;
int builderCalls = 0;
void R_BuildDisplayModeDvars() {
    ++builderCalls;
    assert(dx.displayModeCount == 1);
    assert(dx.displayModes[0].Width >= 320);
    assert(dx.displayModes[0].Height >= 320);
    assert(dx.displayModes[0].RefreshRate >= 1);
}
struct JNIEnv {
    bool exception = false;
    bool failClass = false;
    bool failMethod = false;
    bool failCall = false;
    float hz = 59.94f;
    int deletedRefs = 0;
    bool ExceptionCheck() { return exception; }
    jclass GetObjectClass(jobject) {
        if (failClass) { exception = true; return nullptr; }
        return reinterpret_cast<jclass>(0x20);
    }
    jmethodID GetMethodID(jclass, const char *name, const char *sig) {
        assert(std::strcmp(name, "getRefreshRate") == 0);
        assert(std::strcmp(sig, "()F") == 0);
        if (failMethod) { exception = true; return nullptr; }
        return reinterpret_cast<jmethodID>(0x30);
    }
    float CallFloatMethod(jobject, jmethodID) {
        if (failCall) exception = true;
        return hz;
    }
    void DeleteLocalRef(jclass) { ++deletedRefs; }
};
ANativeWindow window{1080, 2400};
bool failSurface = false;
int windowReleases = 0;
ANativeWindow *ANativeWindow_fromSurface(JNIEnv *, jobject) {
    return failSurface ? nullptr : &window;
}
int ANativeWindow_getWidth(ANativeWindow *w) { return w->width; }
int ANativeWindow_getHeight(ANativeWindow *w) { return w->height; }
void ANativeWindow_release(ANativeWindow *w) {
    assert(w == &window);
    ++windowReleases;
}
/* ORIGINAL_ANDROID_PROVIDER */
int main() {
    static_assert(sizeof(void *) == 8, "LP64 required");
    JNIEnv env;
    jobject surface = reinterpret_cast<jobject>(0x10);
    jobject display = reinterpret_cast<jobject>(0x11);
    assert(!R_AndroidPopulateDisplayMode(nullptr, surface, display));
    assert(!R_AndroidPopulateDisplayMode(&env, nullptr, display));
    assert(!R_AndroidPopulateDisplayMode(&env, surface, nullptr));
    assert(builderCalls == 0);
    assert(R_AndroidPopulateDisplayMode(&env, surface, display));
    assert(builderCalls == 1 && windowReleases == 1);
    assert(env.deletedRefs == 1);
    assert(dx.displayModes[0].Width == 1080);
    assert(dx.displayModes[0].Height == 2400);
    assert(dx.displayModes[0].RefreshRate == 60);
    assert(dx.displayModes[0].Format == UNKNOWN_ANDROID_FORMAT);
    env.hz = 144.0f;
    assert(R_AndroidPopulateDisplayMode(&env, surface, display));
    assert(dx.displayModes[0].RefreshRate == 144);
    assert(builderCalls == 2);
    // Real portrait and landscape Android windows can be narrower than
    // the original Windows-only 640x480 minimum.
    window.width = 360; window.height = 800;
    assert(R_AndroidPopulateDisplayMode(&env, surface, display));
    assert(dx.displayModes[0].Width == 360 && dx.displayModes[0].Height == 800);
    window.width = 800; window.height = 360;
    assert(R_AndroidPopulateDisplayMode(&env, surface, display));
    assert(dx.displayModes[0].Width == 800 && dx.displayModes[0].Height == 360);
    assert(builderCalls == 4);
    window.width = 319;
    assert(!R_AndroidPopulateDisplayMode(&env, surface, display));
    window.width = 320; window.height = 319;
    assert(!R_AndroidPopulateDisplayMode(&env, surface, display));
    assert(builderCalls == 4);
    window.width = 1080; window.height = 2400;
    env.hz = std::numeric_limits<float>::quiet_NaN();
    assert(!R_AndroidPopulateDisplayMode(&env, surface, display));
    env.hz = std::numeric_limits<float>::infinity();
    assert(!R_AndroidPopulateDisplayMode(&env, surface, display));
    env.hz = 0.0f;
    assert(!R_AndroidPopulateDisplayMode(&env, surface, display));
    env.hz = 1001.0f;
    assert(!R_AndroidPopulateDisplayMode(&env, surface, display));
    assert(builderCalls == 4);
    env.hz = 60.0f;
    env.failClass = true;
    assert(!R_AndroidPopulateDisplayMode(&env, surface, display));
    env.failClass = false; env.exception = false;
    env.failMethod = true;
    assert(!R_AndroidPopulateDisplayMode(&env, surface, display));
    env.failMethod = false; env.exception = false;
    env.failCall = true;
    assert(!R_AndroidPopulateDisplayMode(&env, surface, display));
    env.failCall = false; env.exception = false;
    failSurface = true;
    assert(!R_AndroidPopulateDisplayMode(&env, surface, display));
    failSurface = false;
    assert(builderCalls == 4);
    // JNI read is a value-only snapshot: no renderer state or dvar mutation.
    IW3AndroidSurfaceMode staged{0, 0, 0};
    assert(R_AndroidReadSurfaceMode(&env, surface, display, &staged));
    assert(staged.width == 1080 && staged.height == 2400 && staged.refreshHz == 60);
    assert(builderCalls == 4 && dx.displayModes[0].RefreshRate == 144);
    assert(R_AndroidApplySurfaceMode(staged));
    assert(builderCalls == 5 && dx.displayModes[0].RefreshRate == 60);
    const IW3AndroidSurfaceMode bad{319, 2400, 60};
    assert(!R_AndroidApplySurfaceMode(bad));
    assert(builderCalls == 5 && dx.displayModes[0].Width == 1080);
    const IW3AndroidSurfaceMode sentinel{777, 888, 999};
    staged = sentinel;
    assert(!R_AndroidReadSurfaceMode(&env, surface, display, nullptr));
    env.exception = true;
    assert(!R_AndroidReadSurfaceMode(&env, surface, display, &staged));
    env.exception = false;
    window.height = 319;
    assert(!R_AndroidReadSurfaceMode(&env, surface, display, &staged));
    window.height = 2400;
    assert(staged.width == sentinel.width && staged.height == sentinel.height
           && staged.refreshHz == sentinel.refreshHz);
    assert(builderCalls == 5);
    std::puts("IW3_ORIGINAL_ANDROID_SURFACE_MODE_PROVIDER_LP64_PASS");
}
"""

class AndroidNativeWindowModeProvider(unittest.TestCase):
    def test_real_provider_function_under_sanitizers(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("ANativeWindow_fromSurface(env, surface)", source)
        self.assertIn('GetMethodID(displayClass, "getRefreshRate", "()F")', source)
        self.assertIn("R_BuildDisplayModeDvars();", source)
        self.assertIn("R_AndroidReadSurfaceMode(env, surface, display, &mode)", source)
        self.assertIn("R_AndroidApplySurfaceMode(mode)", source)
        self.assertNotIn("Direct3DCreate9", source)
        cpp = HARNESS.replace("/* ORIGINAL_ANDROID_PROVIDER */",
                              "\n".join(function_source(source, signature) for signature in SIGNATURES))
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp) / "android_display_test.cpp"
            exe = Path(temp) / "android_display_test"
            src.write_text(cpp, encoding="utf-8")
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(src), "-o", str(exe)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(exe)], capture_output=True,
                                 text=True, timeout=30, env=env)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_ANDROID_SURFACE_MODE_PROVIDER_LP64_PASS",
                          run.stdout)

if __name__ == "__main__":
    unittest.main()
