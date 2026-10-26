// JNI entry points calling only genuine KisakCOD IW3 C++ modules.
// The Android Activity is a diagnostic entry point, NOT a game engine.
#if !defined(__ANDROID__)
#error "JNI bridge must only compile for Android"
#endif

#include <jni.h>
#include <android/log.h>
#include <cstdio>
#include <atomic>
#include <cstdint>
#include <cstring>
#include "iw3_android_platform.h"

extern "C" int z2026_iw3_math_smoke();
extern "C" int z2026_iw3_surface_smoke();
extern "C" int z2026_iw3_configstrings_smoke();
extern "C" int z2026_iw3_frame_memcpy_smoke();
extern "C" int z2026_iw3_real_pool_smoke();
extern "C" int z2026_iw3_snap_float_smoke();
extern "C" int z2026_iw3_hitloc_copy_smoke();
extern "C" int z2026_iw3_iwd_names_smoke();
extern "C" int z2026_iw3_unzip_smoke(const char *directory, int *iwd_mount_ok, int *iwd_searchpath_ok, int *iwd_directory_scan_ok, int *iwd_lookup_ok, int *iwd_fs_read_ok);
extern "C" int z2026_iw3_configstring_num(const char*);
extern "C" int z2026_iw3_math_source_abi_version();

namespace {
std::atomic<int> g_lifecycle_state{0};
}

#define IW3_JNI_EXPORT extern "C" JNIEXPORT

IW3_JNI_EXPORT jint JNICALL
Java_org_z2026_iw3nativeprobe_EngineBridge_nativeSetDataRoot(
        JNIEnv *env, jclass, jstring absolutePath) {
    if (!absolutePath) return -1;
    const char *path = env->GetStringUTFChars(absolutePath, nullptr);
    if (!path) return -1;
    const int rc = z2026_platform_set_data_root(path);
    env->ReleaseStringUTFChars(absolutePath, path);
    __android_log_print(rc == 0 ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR,
                        "IW3NativeGate", "IW3_JNI_DATA_ROOT_%s",
                        rc == 0 ? "READY" : "FAIL");
    return rc;
}


IW3_JNI_EXPORT jstring JNICALL
Java_org_z2026_iw3nativeprobe_EngineBridge_nativeReport(
        JNIEnv *env, jclass, jstring writableDirectory) {
    int unzip_ok = 0;
    int iwd_mount_ok = 0;
    int iwd_searchpath_ok = 0;
    int iwd_directory_scan_ok = 0;
    int iwd_lookup_ok = 0;
    int iwd_fs_read_ok = 0;
    if (writableDirectory) {
        const char *directory = env->GetStringUTFChars(writableDirectory, nullptr);
        if (directory) {
            unzip_ok = z2026_iw3_unzip_smoke(directory, &iwd_mount_ok, &iwd_searchpath_ok, &iwd_directory_scan_ok, &iwd_lookup_ok, &iwd_fs_read_ok);
            env->ReleaseStringUTFChars(writableDirectory, directory);
        }
    }
    __android_log_print(unzip_ok ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR,
                        "IW3NativeGate", "IW3_JNI_UNZIP_PARSER_%s",
                        unzip_ok ? "PASS" : "FAIL");
    __android_log_print(iwd_mount_ok ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR,
                        "IW3NativeGate", "IW3_JNI_IWD_MOUNT_%s",
                        iwd_mount_ok ? "PASS" : "FAIL");
    __android_log_print(iwd_searchpath_ok ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR,
                        "IW3NativeGate", "IW3_JNI_IWD_SEARCHPATH_%s",
                        iwd_searchpath_ok ? "PASS" : "FAIL");
    __android_log_print(iwd_directory_scan_ok ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR,
                        "IW3NativeGate", "IW3_JNI_IWD_DIRECTORY_SCAN_%s",
                        iwd_directory_scan_ok ? "PASS" : "FAIL");
    __android_log_print(iwd_directory_scan_ok ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR,
                        "IW3NativeGate", "IW3_JNI_IWD_GAME_DIRECTORY_%s",
                        iwd_directory_scan_ok ? "PASS" : "FAIL");
    __android_log_print(iwd_lookup_ok ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR,
                        "IW3NativeGate", "IW3_JNI_IWD_LOOKUP_%s",
                        iwd_lookup_ok ? "PASS" : "FAIL");
    __android_log_print(iwd_fs_read_ok ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR,
                        "IW3NativeGate", "IW3_JNI_IWD_FS_READ_%s",
                        iwd_fs_read_ok ? "PASS" : "FAIL");
    // These calls resolve to the original engine's math, material and
    // configstring implementations via native_math_abi.cpp.
    const int math_ok = z2026_iw3_math_smoke();
    const int surface_ok = z2026_iw3_surface_smoke();
    const int config_ok = z2026_iw3_configstrings_smoke();
    const int frame_copy_ok = z2026_iw3_frame_memcpy_smoke();
    const int pool_ok = z2026_iw3_real_pool_smoke();
    const int snap_ok = z2026_iw3_snap_float_smoke();
    __android_log_print(snap_ok ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR,
                        "IW3NativeGate", "IW3_JNI_SNAP_FLOAT_%s",
                        snap_ok ? "PASS" : "FAIL");
    const int hitloc_ok = z2026_iw3_hitloc_copy_smoke();
    const int iwd_names_ok = z2026_iw3_iwd_names_smoke();
    __android_log_print(iwd_names_ok ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR,
                        "IW3NativeGate", "IW3_JNI_IWD_NAMES_%s",
                        iwd_names_ok ? "PASS" : "FAIL");
    // Real app-private Android filesystem I/O through the native POSIX
    // platform bridge. Sentinel only; this is NOT a game map/fastfile.
    constexpr char kProbe[] = "IW3_NATIVE_IO_2026";
    char fileProbe[64]{};
    const int fileLen = z2026_platform_read_file(
        "iw3-native-io-probe.bin", fileProbe, sizeof(fileProbe));
    const int file_ok =
        fileLen == static_cast<int>(sizeof(kProbe) - 1) &&
        std::memcmp(fileProbe, kProbe, sizeof(kProbe) - 1) == 0 &&
        z2026_platform_read_file("../iw3-native-io-probe.bin",
                                 fileProbe, sizeof(fileProbe)) == -1 &&
        z2026_platform_read_file("iw3-native-io-probe.bin",
                                 fileProbe, 4) == -1;
    __android_log_print(file_ok ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR,
                        "IW3NativeGate", "IW3_JNI_SANDBOX_IO_%s",
                        file_ok ? "PASS" : "FAIL");
    int initial_usercmd[10]{};
    const int usercmd_ok =
        z2026_platform_usercmd_snapshot(1234, initial_usercmd, 10) == 0 &&
        initial_usercmd[0] == 1234 && initial_usercmd[1] == 0 &&
        initial_usercmd[5] == 0 && initial_usercmd[6] == 0;
    __android_log_print(usercmd_ok ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR,
                        "IW3NativeGate", "IW3_JNI_USERCMD_ADAPTER_%s",
                        usercmd_ok ? "READY" : "FAIL");
    const int perk_index = z2026_iw3_configstring_num("specialty_rof");
    const std::uint64_t monotonic_time = z2026_platform_monotonic_ns();
    const int success = unzip_ok && iwd_mount_ok && iwd_searchpath_ok && iwd_directory_scan_ok && iwd_lookup_ok && iwd_fs_read_ok && math_ok && surface_ok && config_ok && frame_copy_ok && pool_ok && snap_ok && hitloc_ok && iwd_names_ok && file_ok && usercmd_ok &&
                        perk_index == 2034 && monotonic_time > 0;
    char report[1536];
    std::snprintf(report, sizeof(report),
                  "ORIGINAL KISAKCOD IW3 C++ CODE TEST\n"
                  "JNI: %s\n"
                  "AngleVectors / original aiming: %s\n"
                  "Surface / material table: %s\n"
                  "Configstring registry: %s\n"
                  "Original G_RunFrame Com_Memcpy: %s\n"
                  "Real IW3 64-bit Pool_Alloc/Free: %s\n"
                  "IW3 ARM64 snap rounding: %s\n"
                  "Real IW3 SP hit-location byte copy: %s\n"
                  "Original IW3 IWD name lookup: %s\n"
                  "Original IW3 ZIP32 stored/deflate parser: %s\n"
                  "Original FS_LoadZipFile IWD index: %s\n"
                  "Original FS_AddSearchPath fixture insertion: %s\n"
                  "Original FS_AddIwdFilesForGameDirectory scan: %s\n"
                  "Original FS_FOpenFileReadForThread lookup-only branch: %s\n"
                  "Original FS_Read IWD ZIP branch: %s\n"
                  "Android app-private data-root I/O: %s\n"
                  "Original IW3 usercmd_s touch adapter: %s\n"
                  "Original specialty_rof ID: %d\n"
                  "Monotonic Android clock: %s\n"
                  "Native ABI version: %d\n\n"
                  "NO IW3 GAME FRAME OR RENDERER YET\n"
                  "THIS IS NOT A PLAYABLE GAME",
                  success ? "PASS" : "FAIL",
                  math_ok ? "PASS" : "FAIL",
                  surface_ok ? "PASS" : "FAIL",
                  config_ok ? "PASS" : "FAIL",
                  frame_copy_ok ? "PASS" : "FAIL",
                  pool_ok ? "PASS" : "FAIL",
                  snap_ok ? "PASS" : "FAIL",
                  hitloc_ok ? "PASS" : "FAIL",
                  iwd_names_ok ? "PASS" : "FAIL",
                  unzip_ok ? "PASS" : "FAIL",
                  iwd_mount_ok ? "PASS" : "FAIL",
                  iwd_searchpath_ok ? "PASS" : "FAIL",
                  iwd_directory_scan_ok ? "PASS" : "FAIL",
                  iwd_lookup_ok ? "PASS" : "FAIL",
                  iwd_fs_read_ok ? "PASS" : "FAIL",
                  file_ok ? "PASS" : "FAIL",
                  usercmd_ok ? "PASS" : "FAIL",
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
Java_org_z2026_iw3nativeprobe_EngineBridge_nativeUsercmdSnapshot(
        JNIEnv *env, jclass, jint serverTime, jintArray out) {
    if (out == nullptr || env->GetArrayLength(out) < 10) return -1;
    int fields[10]{};
    const int rc = z2026_platform_usercmd_snapshot(serverTime, fields, 10);
    if (rc != 0) {
        __android_log_print(ANDROID_LOG_ERROR, "IW3NativeGate",
                            "IW3_JNI_USERCMD_SNAPSHOT_FAILED");
        return rc;
    }
    jint values[10]{};
    for (int i = 0; i < 10; ++i) values[i] = static_cast<jint>(fields[i]);
    env->SetIntArrayRegion(out, 0, 10, values);
    return 0;
}

IW3_JNI_EXPORT jint JNICALL
Java_org_z2026_iw3nativeprobe_EngineBridge_nativeTouchSnapshot(
        JNIEnv *env, jclass, jint id, jfloatArray out) {
    if (out == nullptr || id < 0 || id >= 10 ||
        env->GetArrayLength(out) < 2) return -1;
    float x = 0.0f, y = 0.0f;
    const int pressed = z2026_platform_touch_snapshot(id, &x, &y);
    if (pressed < 0) return -1;
    const jfloat coords[2] = {x, y};
    env->SetFloatArrayRegion(out, 0, 2, coords);
    return pressed;
}

IW3_JNI_EXPORT void JNICALL
Java_org_z2026_iw3nativeprobe_EngineBridge_nativeTouchReset(
        JNIEnv *, jclass) {
    z2026_platform_touch_reset();
}

IW3_JNI_EXPORT void JNICALL
Java_org_z2026_iw3nativeprobe_EngineBridge_nativeLifecycle(
        JNIEnv *, jclass, jint state) {
    if (state < 1 || state > 4) return;
    g_lifecycle_state.store(state, std::memory_order_release);
    __android_log_print(ANDROID_LOG_INFO, "IW3NativeGate",
                        "IW3_JNI_LIFECYCLE_%d", state);
}

IW3_JNI_EXPORT jint JNICALL
Java_org_z2026_iw3nativeprobe_EngineBridge_nativeLifecycleState(
        JNIEnv *, jclass) {
    return g_lifecycle_state.load(std::memory_order_acquire);
}
