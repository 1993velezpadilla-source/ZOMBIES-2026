// KisakCOD IW3 Android platform EGL/GLES3 surface lifecycle.
// NOT an alternate engine or a renderer: original IW3 material/geometry/draw
// translation, R_Init integration, and real gameplay remain unimplemented.
#if defined(__ANDROID__)
#include "r_android_egl.h"
#include <EGL/eglext.h>

static bool R_AndroidEglIsOwnerThread(const IW3AndroidEglContext *state)
{
    return state && state->ownerThreadValid
        && pthread_equal(state->ownerThread, pthread_self()) != 0;
}

bool R_AndroidEglDestroy(IW3AndroidEglContext *state)
{
    if (!state)
        return false;
    // eglDestroyContext / eglTerminate must never run from an Android UI
    // callback while the engine render thread owns the live EGL context.
    if (state->ownerThreadValid && !R_AndroidEglIsOwnerThread(state))
        return false;
    if (state->display != EGL_NO_DISPLAY)
    {
        // Never unbind another context belonging to the caller or another
        // render thread. EGL current state is thread-local.
        if (state->context != EGL_NO_CONTEXT
            && eglGetCurrentContext() == state->context)
            eglMakeCurrent(state->display, EGL_NO_SURFACE, EGL_NO_SURFACE,
                           EGL_NO_CONTEXT);
        if (state->context != EGL_NO_CONTEXT)
            eglDestroyContext(state->display, state->context);
        if (state->surface != EGL_NO_SURFACE)
            eglDestroySurface(state->display, state->surface);
        eglTerminate(state->display);
    }
    if (state->window)
        ANativeWindow_release(state->window);
    state->display = EGL_NO_DISPLAY;
    state->surface = EGL_NO_SURFACE;
    state->context = EGL_NO_CONTEXT;
    state->window = nullptr;
    state->width = 0;
    state->height = 0;
    state->ownerThreadValid = false;
    state->ownerThread = pthread_t{};
    return true;
}

bool R_AndroidEglRefreshSize(IW3AndroidEglContext *state)
{
    // Android can resize an existing EGL window surface without replacing
    // its EGLSurface. Query EGL (not cached ANativeWindow geometry) on the
    // engine render thread before updating the original IW3 viewport.
    if (!R_AndroidEglIsOwnerThread(state)
        || state->display == EGL_NO_DISPLAY
        || state->surface == EGL_NO_SURFACE
        || state->context == EGL_NO_CONTEXT
        || eglGetCurrentDisplay() != state->display
        || eglGetCurrentContext() != state->context
        || eglGetCurrentSurface(EGL_DRAW) != state->surface)
        return false;

    EGLint width = 0;
    EGLint height = 0;
    if (!eglQuerySurface(state->display, state->surface, EGL_WIDTH, &width)
        || !eglQuerySurface(state->display, state->surface, EGL_HEIGHT, &height)
        || width <= 0 || height <= 0)
        return false;

    // Publish both values together only after all checks pass.
    state->width = width;
    state->height = height;
    return true;
}

bool R_AndroidEglCreate(IW3AndroidEglContext *state, ANativeWindow *window)
{
    if (!state || !window || state->window
        || state->display != EGL_NO_DISPLAY
        || state->context != EGL_NO_CONTEXT
        || state->surface != EGL_NO_SURFACE
        || state->ownerThreadValid)
        return false;

    state->ownerThread = pthread_self();
    state->ownerThreadValid = true;
    ANativeWindow_acquire(window);
    state->window = window;
    state->display = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if (state->display == EGL_NO_DISPLAY)
        goto fail;
    if (!eglInitialize(state->display, nullptr, nullptr))
        goto fail;
    if (!eglBindAPI(EGL_OPENGL_ES_API))
        goto fail;

    {
        // Explicit ES3 is necessary for the planned real IW3 shader backend.
        // Do not silently downgrade to ES2 or claim D3D9 compatibility.
        const EGLint attrs[] = {
            EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
            EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT_KHR,
            EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8,
            EGL_ALPHA_SIZE, 8, EGL_DEPTH_SIZE, 24, EGL_STENCIL_SIZE, 8,
            EGL_NONE
        };
        EGLConfig config = nullptr;
        EGLint count = 0;
        if (!eglChooseConfig(state->display, attrs, &config, 1, &count)
            || count != 1 || !config)
            goto fail;

        EGLint visualId = 0;
        if (!eglGetConfigAttrib(state->display, config, EGL_NATIVE_VISUAL_ID,
                                &visualId)
            || visualId <= 0
            || ANativeWindow_setBuffersGeometry(window, 0, 0, visualId) != 0)
            goto fail;

        state->surface = eglCreateWindowSurface(state->display, config,
                                                window, nullptr);
        if (state->surface == EGL_NO_SURFACE)
            goto fail;

        const EGLint ctxAttrs[] = { EGL_CONTEXT_CLIENT_VERSION, 3, EGL_NONE };
        state->context = eglCreateContext(state->display, config,
                                           EGL_NO_CONTEXT, ctxAttrs);
        if (state->context == EGL_NO_CONTEXT)
            goto fail;
        if (!eglMakeCurrent(state->display, state->surface, state->surface,
                            state->context))
            goto fail;
        if (!R_AndroidEglRefreshSize(state))
            goto fail;
    }
    return true;

fail:
    R_AndroidEglDestroy(state);
    return false;
}

bool R_AndroidEglPresent(const IW3AndroidEglContext *state)
{
    // A successful swap only proves an EGL surface, NOT an IW3 rendered frame.
    if (!R_AndroidEglIsOwnerThread(state)
        || state->display == EGL_NO_DISPLAY
        || state->surface == EGL_NO_SURFACE
        || state->context == EGL_NO_CONTEXT
        || eglGetCurrentDisplay() != state->display
        || eglGetCurrentContext() != state->context
        || eglGetCurrentSurface(EGL_DRAW) != state->surface)
        return false;
    return eglSwapBuffers(state->display, state->surface) == EGL_TRUE;
}
#endif // __ANDROID__
