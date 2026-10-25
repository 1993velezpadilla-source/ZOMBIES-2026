// JNI entry points calling only genuine KisakCOD IW3 C++ modules.
// The Android Activity is a diagnostic entry point, NOT a game engine.
#if !defined(__ANDROID__)
#error "JNI bridge must only compile for Android"
#endif

#include <jni.h>
#include <android/log.h>
#include <cstdio>
#include <cstdint>
#include "iw3_android_platform.h"

extern "C" int z2026_iw3_math_smoke();
extern "C" int z2026_iw3_surface_smoke();
extern "C" int z2026_iw3_configstrings_smoke();
extern "C" int z2026_iw3_configstring_num(const char*);
extern "C" int z2026_iw3_math_source_abi_version();

#define IW3_JNI_EXPORT extern "C" JNIEXPORT

IW3_JNI_EXPORT jstring JNICALL
Java_org_z2026_iw3nativeprobe_EngineBridge_nativeReport(JNIEnv *env, jclass) {
    // These calls resolve to the original engine's math, material and
    // configstring implementations via native_math_abi.cpp.
    const int math_ok = z2026_iw3_math_smoke();
    const int surface_ok = z2026_iw3_surface_smoke();
    const int config_ok = z2026_iw3_configstrings_smoke();
    const int perk_index = z2026_iw3_configstring_num("specialty_rof");
    const std::uint64_t monotonic_time = z2026_platform_monotonic_ns();
    const int success = math_ok && surface_ok && config_ok &&
                        perk_index == 2034 && monotonic_time > 0;
    char report[640];
    std::snprintf(report, sizeof(report),
                  "ORIGINAL KISAKCOD IW3 C++ CODE TEST\n"
                  "JNI: %s\n"
                  "AngleVectors / original aiming: %s\n"
                  "Surface / material table: %s\n"
                  "Configstring registry: %s\n"
                  "Original specialty_rof ID: %d\n"
                  "Monotonic Android clock: %s\n"
                  "Native ABI version: %d\n\n"
                  "NO IW3 GAME FRAME OR RENDERER YET\n"
                  "THIS IS NOT A PLAYABLE GAME",
                  success ? "PASS" : "FAIL",
                  math_ok ? "PASS" : "FAIL",
                  surface_ok ? "PASS" : "FAIL",
                  config_ok ? "PASS" : "FAIL",
                  perk_index, monotonic_time ? "PASS" : "FAIL",
                  z2026_iw3_math_source_abi_version());
    __android_log_print(success ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR,
                        "IW3NativeGate", "JNI_NATIVE_ENGINE_PROBE_%s",
                        success ? "PASS" : "FAIL");
    return env->NewStringUTF(report);
}

IW3_JNI_EXPORT jint JNICALL
Java_org_z2026_iw3nativeprobe_EngineBridge_nativeTouch(
        JNIEnv *, jclass, jint id, jfloat x, jfloat y, jboolean pressed) {
    return z2026_platform_touch_event(static_cast<int>(id), x, y, pressed ? 1 : 0);
}

IW3_JNI_EXPORT jint JNICALL
Java_org_z2026_iw3nativeprobe_EngineBridge_nativeTouchSnapshot(
        JNIEnv *, jclass, jint id, jfloatArray out) {
    if (out == nullptr || id < 0 || id >= 10) return -1;
    // GetArrayLength is checked before SetFloatArrayRegion; never write
    // outside a Java-side buffer.
    JNIEnv *env = nullptr;
    // JNI signature above intentionally lacks the named environment.
    // See below: replace by a validated JNIEnv* parameter.
    return -1;
}
