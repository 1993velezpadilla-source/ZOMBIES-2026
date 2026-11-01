#pragma once
// Android EGL/GLES3 context lifecycle for the authentic KisakCOD IW3 renderer.
// This is a platform surface provider ONLY: it does not translate IW3 D3D9
// draw commands, load maps, or constitute a playable Android build.
#if defined(__ANDROID__)
#include <android/native_window.h>
#include <EGL/egl.h>

struct IW3AndroidEglContext
{
    EGLDisplay display = EGL_NO_DISPLAY;
    EGLSurface surface = EGL_NO_SURFACE;
    EGLContext context = EGL_NO_CONTEXT;
    ANativeWindow *window = nullptr; // acquired reference owned by this object
    EGLint width = 0;
    EGLint height = 0;

    IW3AndroidEglContext() = default;
    IW3AndroidEglContext(const IW3AndroidEglContext &) = delete;
    IW3AndroidEglContext &operator=(const IW3AndroidEglContext &) = delete;
};

// Call all three functions on the SAME engine render thread. The caller must
// serialize Surface destruction/recreation and keep the Java Surface alive.
// No JNI references are retained; window is acquired/released explicitly.
bool R_AndroidEglCreate(IW3AndroidEglContext *state, ANativeWindow *window);
bool R_AndroidEglPresent(const IW3AndroidEglContext *state);
void R_AndroidEglDestroy(IW3AndroidEglContext *state);
#endif
