"""Host ASan/UBSan lifecycle test of the UNMODIFIED KisakCOD Android EGL provider.

EGL/ANativeWindow calls are mocked, so this is not device rendering or gameplay.
The Android NDK workflow separately compiles the real provider for ARM64.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_android_egl.cpp"

EGL_HEADER = r"""
#pragma once
#include <android/native_window.h>
using EGLint = int;
using EGLBoolean = int;
using EGLDisplay = void *;
using EGLSurface = void *;
using EGLContext = void *;
using EGLConfig = void *;
using EGLNativeWindowType = ANativeWindow *;
#define EGL_TRUE 1
#define EGL_FALSE 0
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_NO_SURFACE ((EGLSurface)0)
#define EGL_NO_CONTEXT ((EGLContext)0)
#define EGL_DEFAULT_DISPLAY ((void*)0)
#define EGL_OPENGL_ES_API 0x30A0
#define EGL_SURFACE_TYPE 0x3033
#define EGL_WINDOW_BIT 4
#define EGL_RENDERABLE_TYPE 0x3040
#define EGL_RED_SIZE 0x3024
#define EGL_GREEN_SIZE 0x3023
#define EGL_BLUE_SIZE 0x3022
#define EGL_ALPHA_SIZE 0x3021
#define EGL_DEPTH_SIZE 0x3025
#define EGL_STENCIL_SIZE 0x3026
#define EGL_NATIVE_VISUAL_ID 0x302E
#define EGL_CONTEXT_CLIENT_VERSION 0x3098
#define EGL_WIDTH 0x3057
#define EGL_HEIGHT 0x3056
#define EGL_DRAW 0x3059
#define EGL_READ 0x305A
#define EGL_NONE 0x3038
EGLDisplay eglGetDisplay(void *);
EGLBoolean eglInitialize(EGLDisplay, EGLint *, EGLint *);
EGLBoolean eglBindAPI(EGLint);
EGLBoolean eglChooseConfig(EGLDisplay, const EGLint *, EGLConfig *, EGLint, EGLint *);
EGLBoolean eglGetConfigAttrib(EGLDisplay, EGLConfig, EGLint, EGLint *);
EGLSurface eglCreateWindowSurface(EGLDisplay, EGLConfig, EGLNativeWindowType, const EGLint *);
EGLContext eglCreateContext(EGLDisplay, EGLConfig, EGLContext, const EGLint *);
EGLBoolean eglMakeCurrent(EGLDisplay, EGLSurface, EGLSurface, EGLContext);
EGLBoolean eglQuerySurface(EGLDisplay, EGLSurface, EGLint, EGLint *);
EGLDisplay eglGetCurrentDisplay();
EGLContext eglGetCurrentContext();
EGLSurface eglGetCurrentSurface(EGLint);
EGLBoolean eglSwapBuffers(EGLDisplay, EGLSurface);
EGLBoolean eglDestroyContext(EGLDisplay, EGLContext);
EGLBoolean eglDestroySurface(EGLDisplay, EGLSurface);
EGLBoolean eglTerminate(EGLDisplay);
"""

NATIVE_HEADER = r"""
#pragma once
struct ANativeWindow { int marker; };
void ANativeWindow_acquire(ANativeWindow *);
void ANativeWindow_release(ANativeWindow *);
int ANativeWindow_setBuffersGeometry(ANativeWindow *, int, int, int);
"""

HARNESS = r"""
#include <cassert>
#include <cstdio>
#include <initializer_list>
#include <thread>
#include "r_android_egl.cpp"
static int acquired=0, released=0, destroyedContexts=0, destroyedSurfaces=0, terminated=0;
static int failAt=0, swapCalls=0;
static EGLDisplay currentDisplay=EGL_NO_DISPLAY;
static int surfaceWidth=1080, surfaceHeight=2400;
static EGLContext currentContext=EGL_NO_CONTEXT;
static EGLSurface currentSurface=EGL_NO_SURFACE;
static EGLDisplay goodDisplay=reinterpret_cast<void *>(0x10);
static EGLSurface goodSurface=reinterpret_cast<void *>(0x20);
static EGLSurface replacementSurface=reinterpret_cast<void *>(0x21);
static EGLContext goodContext=reinterpret_cast<void *>(0x30);
void ANativeWindow_acquire(ANativeWindow *) { ++acquired; }
void ANativeWindow_release(ANativeWindow *) { ++released; }
int ANativeWindow_setBuffersGeometry(ANativeWindow *w, int, int, int) {
    return failAt==5 || (failAt==14 && w->marker==456) ? -1 : 0;
}
EGLDisplay eglGetDisplay(void *) { return failAt==1 ? EGL_NO_DISPLAY : goodDisplay; }
EGLBoolean eglInitialize(EGLDisplay, EGLint *, EGLint *) { return failAt!=2; }
EGLBoolean eglBindAPI(EGLint api) { assert(api==EGL_OPENGL_ES_API); return failAt!=3; }
EGLBoolean eglChooseConfig(EGLDisplay, const EGLint *attrs, EGLConfig *config, EGLint, EGLint *n) {
    bool es3=false, depth24=false;
    for (int i=0; attrs[i]!=EGL_NONE; i+=2) {
        if (attrs[i]==EGL_RENDERABLE_TYPE) es3=(attrs[i+1]==0x40);
        if (attrs[i]==EGL_DEPTH_SIZE) depth24=(attrs[i+1]==24);
    }
    assert(es3 && depth24);
    *config=reinterpret_cast<void *>(0x40); *n=(failAt==4 ? 0 : 1);
    return EGL_TRUE;
}
EGLBoolean eglGetConfigAttrib(EGLDisplay, EGLConfig, EGLint what, EGLint *out) {
    assert(what==EGL_NATIVE_VISUAL_ID); *out=1; return EGL_TRUE;
}
EGLSurface eglCreateWindowSurface(EGLDisplay, EGLConfig, EGLNativeWindowType w, const EGLint *) {
    if (failAt==6 || (failAt==15 && w->marker==456)) return EGL_NO_SURFACE;
    return w->marker==456 ? replacementSurface : goodSurface;
}
EGLContext eglCreateContext(EGLDisplay, EGLConfig, EGLContext, const EGLint *attrs) {
    assert(attrs[0]==EGL_CONTEXT_CLIENT_VERSION && attrs[1]==3);
    return failAt==7 ? EGL_NO_CONTEXT : goodContext;
}
EGLBoolean eglMakeCurrent(EGLDisplay, EGLSurface draw, EGLSurface, EGLContext ctx) {
    if ((failAt==8 && ctx!=EGL_NO_CONTEXT)
        || (failAt==17 && draw==replacementSurface)
        || (failAt==18 && ctx==EGL_NO_CONTEXT)) return EGL_FALSE;
    currentContext=ctx; currentSurface=draw;
    currentDisplay=(ctx==EGL_NO_CONTEXT ? EGL_NO_DISPLAY : goodDisplay);
    return EGL_TRUE;
}
EGLBoolean eglQuerySurface(EGLDisplay, EGLSurface surf, EGLint what, EGLint *out) {
    if ((failAt==16 && surf==replacementSurface)
        || (failAt==11 && what==EGL_WIDTH) || (failAt==12 && what==EGL_HEIGHT))
        return EGL_FALSE;
    *out=what==EGL_WIDTH ? (failAt==13 ? 0 : surfaceWidth)
                           : (failAt==9 ? 0 : surfaceHeight);
    return EGL_TRUE;
}
EGLDisplay eglGetCurrentDisplay() { return currentDisplay; }
EGLContext eglGetCurrentContext() { return currentContext; }
EGLSurface eglGetCurrentSurface(EGLint which) {
    assert(which==EGL_DRAW || which==EGL_READ); return currentSurface;
}
EGLBoolean eglSwapBuffers(EGLDisplay, EGLSurface) { ++swapCalls; return failAt==10 ? EGL_FALSE : EGL_TRUE; }
EGLBoolean eglDestroyContext(EGLDisplay, EGLContext) { ++destroyedContexts; return EGL_TRUE; }
EGLBoolean eglDestroySurface(EGLDisplay, EGLSurface) { ++destroyedSurfaces; return EGL_TRUE; }
EGLBoolean eglTerminate(EGLDisplay) { ++terminated; return EGL_TRUE; }
int main() {
    static_assert(sizeof(void*)==8, "LP64 required");
    ANativeWindow window{123};
    IW3AndroidEglContext ctx;
    assert(!R_AndroidEglCreate(nullptr, &window));
    assert(!R_AndroidEglCreate(&ctx, nullptr));
    assert(!R_AndroidEglPresent(&ctx));
    assert(!R_AndroidEglRefreshSize(&ctx));
    assert(R_AndroidEglCreate(&ctx, &window));
    assert(ctx.width==1080 && ctx.height==2400);
    assert(acquired==1 && released==0);
    // A live Android Surface may change size without changing EGLSurface.
    surfaceWidth=2400; surfaceHeight=1080;
    assert(R_AndroidEglRefreshSize(&ctx));
    assert(ctx.width==2400 && ctx.height==1080);
    for (int queryFail : {11, 12, 13, 9}) {
        failAt=queryFail;
        assert(!R_AndroidEglRefreshSize(&ctx));
        assert(ctx.width==2400 && ctx.height==1080); // atomic update
    }
    failAt=0;
    currentDisplay=reinterpret_cast<void *>(0x99);
    assert(!R_AndroidEglRefreshSize(&ctx));
    assert(!R_AndroidEglPresent(&ctx));
    currentDisplay=goodDisplay;
    assert(R_AndroidEglRefreshSize(&ctx));
    assert(!R_AndroidEglCreate(&ctx, &window)); // no overwrite/leak
    assert(R_AndroidEglPresent(&ctx));
    assert(swapCalls==1);
    currentContext=EGL_NO_CONTEXT;
    assert(!R_AndroidEglPresent(&ctx)); // wrong thread/current context
    currentContext=goodContext;
    currentSurface=EGL_NO_SURFACE;
    assert(!R_AndroidEglPresent(&ctx)); // wrong draw surface
    currentSurface=goodSurface;
    failAt=10; assert(!R_AndroidEglPresent(&ctx)); failAt=0;
    // A UI-thread teardown must not destroy a live render-thread context.
    std::thread uiThread([&] {
        assert(!R_AndroidEglRefreshSize(&ctx));
        assert(!R_AndroidEglPresent(&ctx));
        assert(!R_AndroidEglDestroy(&ctx));
    });
    uiThread.join();
    assert(acquired==1 && released==0 && destroyedContexts==0
           && destroyedSurfaces==0 && terminated==0);
    assert(ctx.ownerThreadValid && ctx.window==&window);
    assert(R_AndroidEglDestroy(&ctx));
    assert(acquired==released && destroyedContexts==1 && destroyedSurfaces==1 && terminated==1);
    assert(ctx.window==nullptr && ctx.width==0 && ctx.context==EGL_NO_CONTEXT);
    assert(!ctx.ownerThreadValid);
    assert(R_AndroidEglDestroy(&ctx)); // idempotent
    assert(!R_AndroidEglDestroy(nullptr));
    assert(released==1);
    for (int fail=1; fail<=9; ++fail) {
        failAt=fail;
        assert(!R_AndroidEglCreate(&ctx, &window));
        assert(ctx.window==nullptr && ctx.display==EGL_NO_DISPLAY);
        assert(!ctx.ownerThreadValid);
        assert(acquired==released); // no leaked ANativeWindow reference
        failAt=0;
    }
    assert(R_AndroidEglCreate(&ctx, &window));
    ANativeWindow newWindow{456};
    assert(!R_AndroidEglReplaceWindow(&ctx, nullptr));
    assert(!R_AndroidEglReplaceWindow(&ctx, &window));
    std::thread foreign([&] { assert(!R_AndroidEglReplaceWindow(&ctx, &newWindow)); });
    foreign.join();
    const int baselineAcquired=acquired, baselineReleased=released;
    for (int failure : {14, 15, 16, 17}) {
        failAt=failure;
        assert(!R_AndroidEglReplaceWindow(&ctx, &newWindow));
        assert(ctx.window==&window && ctx.surface==goodSurface);
        assert(currentSurface==goodSurface && ctx.width==2400 && ctx.height==1080);
        assert(acquired-released==1); // no leaked references on failed replacement
        failAt=0;
    }
    assert(acquired==baselineAcquired+4 && released==baselineReleased+4);
    surfaceWidth=720; surfaceHeight=1280;
    assert(R_AndroidEglReplaceWindow(&ctx, &newWindow));
    assert(ctx.window==&newWindow && ctx.surface==replacementSurface);
    assert(ctx.width==720 && ctx.height==1280);
    assert(currentSurface==replacementSurface);
    assert(R_AndroidEglPresent(&ctx));
    // Android Surface may disappear before its replacement exists.
    std::thread foreignDetach([&] { assert(!R_AndroidEglDetachWindow(&ctx)); });
    foreignDetach.join();
    failAt=18;
    assert(!R_AndroidEglDetachWindow(&ctx)); // unbind failure is transactional
    assert(ctx.surface==replacementSurface && ctx.window==&newWindow);
    failAt=0;
    assert(R_AndroidEglDetachWindow(&ctx));
    assert(ctx.surface==EGL_NO_SURFACE && ctx.window==nullptr);
    assert(ctx.width==0 && ctx.height==0 && ctx.context==goodContext);
    assert(!R_AndroidEglPresent(&ctx) && !R_AndroidEglRefreshSize(&ctx));
    assert(!R_AndroidEglDetachWindow(&ctx)); // already detached
    failAt=15;
    assert(!R_AndroidEglReplaceWindow(&ctx, &newWindow));
    assert(ctx.surface==EGL_NO_SURFACE && ctx.context==goodContext);
    failAt=0;
    assert(R_AndroidEglReplaceWindow(&ctx, &window)); // resume on new Surface
    assert(ctx.surface==goodSurface && ctx.window==&window);
    assert(ctx.width==720 && ctx.height==1280);
    assert(R_AndroidEglPresent(&ctx));
    assert(R_AndroidEglDestroy(&ctx));
    assert(acquired==released);
    std::puts("IW3_ANDROID_EGL_LIFECYCLE_HOST_SANITIZER_PASS_NOT_RENDERER");
}
"""

class AndroidEglLifecycle(unittest.TestCase):
    def test_unmodified_android_egl_provider_under_sanitizers(self):
        self.assertTrue(SRC.exists())
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "EGL").mkdir()
            (base / "android").mkdir()
            (base / "EGL/egl.h").write_text(EGL_HEADER)
            (base / "EGL/eglext.h").write_text("#define EGL_OPENGL_ES3_BIT_KHR 0x0040\n")
            (base / "android/native_window.h").write_text(NATIVE_HEADER)
            test = base / "egl_lifecycle.cpp"
            test.write_text(HARNESS)
            binary = base / "egl_lifecycle"
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-D__ANDROID__",
                 "-O1", "-g", "-UNDEBUG", "-fsanitize=address,undefined",
                 "-fno-omit-frame-pointer", "-pthread", "-I", str(base), "-I", str(SRC.parent),
                 str(test), "-o", str(binary)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(binary)], capture_output=True, text=True,
                                 env=env, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ANDROID_EGL_LIFECYCLE_HOST_SANITIZER_PASS_NOT_RENDERER", run.stdout)

if __name__ == "__main__":
    unittest.main()
