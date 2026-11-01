// KisakCOD IW3: Android current-surface display-mode provider.
//
// This feeds the ORIGINAL IW3 mode builder with measurements from the real
// Android Surface and Display. It does not create a D3D9 device or render.
// The caller must supply a live Surface and its corresponding Display.
#if defined(__ANDROID__)
#include "r_android_display.h"
#include "r_init.h"
#include <android/native_window_jni.h>
#include <cmath>
#include <cstdint>

bool R_AndroidPopulateDisplayMode(JNIEnv *env, jobject surface, jobject display)
{
    if (!env || !surface || !display)
        return false;

    ANativeWindow *window = ANativeWindow_fromSurface(env, surface);
    if (!window || env->ExceptionCheck())
    {
        if (window)
            ANativeWindow_release(window);
        return false;
    }
    const int width = ANativeWindow_getWidth(window);
    const int height = ANativeWindow_getHeight(window);
    ANativeWindow_release(window);

    // Display.getRefreshRate() reports the current OS refresh rate, not a
    // fabricated default or a list of modes that Android did not report.
    jclass displayClass = env->GetObjectClass(display);
    if (!displayClass || env->ExceptionCheck())
        return false;
    jmethodID getRefreshRate = env->GetMethodID(displayClass, "getRefreshRate", "()F");
    if (!getRefreshRate || env->ExceptionCheck())
    {
        env->DeleteLocalRef(displayClass);
        return false;
    }
    const float refreshHz = env->CallFloatMethod(display, getRefreshRate);
    const bool javaFailed = env->ExceptionCheck();
    env->DeleteLocalRef(displayClass);
    if (javaFailed)
        return false;

    // Original R_AddValidResolution requires at least 640x480. Do not feed
    // it invalid sizes or silently claim a fake 60 Hz mode.
    if (width < 640 || height < 480 || !std::isfinite(refreshHz)
        || refreshHz < 1.0f || refreshHz > 1000.0f)
        return false;

    _D3DDISPLAYMODE nativeMode{};
    nativeMode.Width = static_cast<uint32_t>(width);
    nativeMode.Height = static_cast<uint32_t>(height);
    nativeMode.RefreshRate = static_cast<uint32_t>(refreshHz + 0.5f);
    // Android has no D3D9 display format. The original mode builder uses
    // only Width, Height and RefreshRate; never pretend Format is D3D9.
    nativeMode.Format = static_cast<_D3DFORMAT>(0);
    dx.displayModes[0] = nativeMode;
    dx.displayModeCount = 1;
    R_BuildDisplayModeDvars();
    return true;
}
#endif // __ANDROID__
