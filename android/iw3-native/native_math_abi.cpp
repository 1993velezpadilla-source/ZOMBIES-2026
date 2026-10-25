// C ABI for exercising REAL KisakCOD AngleVectors from Android arm64.
#include <cmath>
#include <cstddef>
#include <cstring>
#include "iw3_android_surface_compat.h"
#include "surfaceflags.h"
#include "com_constantconfigstrings.h"
#include "pool_allocator.h"

#if defined(_WIN32)
#error "This project is for Android NDK and portable host math tests only"
#endif

void AngleVectors(const float *angles, float *forward, float *right, float *up);

#if defined(_WIN32)
#define Z2026_NATIVE_EXPORT __declspec(dllexport)
#else
#define Z2026_NATIVE_EXPORT __attribute__((visibility("default")))
#endif

extern "C" Z2026_NATIVE_EXPORT int z2026_iw3_math_source_abi_version() {
    return 1; // ABI version only; NOT an IW3 engine/runtime version.
}

extern "C" Z2026_NATIVE_EXPORT void z2026_iw3_angle_vectors(
    const float *angles, float *forward, float *right, float *up) {
    if (angles == nullptr) return;
    // Calls compiled source from actual third_party/KisakCOD, not reimplemented.
    AngleVectors(angles, forward, right, up);
}

extern "C" Z2026_NATIVE_EXPORT int z2026_iw3_math_smoke() {
    const float angles[3] = {0.0f, 90.0f, 0.0f};
    float fwd[3]{}, right[3]{}, up[3]{};
    z2026_iw3_angle_vectors(angles, fwd, right, up);
    const auto close = [](float a, float b) { return std::fabs(a - b) < 0.0002f; };
    return close(fwd[0], 0.0f) && close(fwd[1], 1.0f) &&
           close(fwd[2], 0.0f) && close(right[0], 1.0f) &&
           close(up[2], 1.0f);
}

extern "C" Z2026_NATIVE_EXPORT int z2026_iw3_surface_type_from_name(const char* name) {
    if (!name) return -1;
    // The 60-entry table and lookup routine come directly from the
    // original IW3 src/universal/surfaceflags.cpp C++ translation unit.
    return Com_SurfaceTypeFromName(name);
}

extern "C" Z2026_NATIVE_EXPORT const char* z2026_iw3_surface_type_name(int index) {
    return Com_SurfaceTypeToName(index);
}

extern "C" Z2026_NATIVE_EXPORT int z2026_iw3_surface_smoke() {
    return z2026_iw3_surface_type_from_name("brick") == 2 &&
           z2026_iw3_surface_type_from_name("BRICK") == 2 &&
           z2026_iw3_surface_type_from_name("foliage") == 8 &&
           z2026_iw3_surface_type_from_name("invalid-type") == -1 &&
           z2026_iw3_surface_type_from_name("default") == 0;
}

extern "C" Z2026_NATIVE_EXPORT void z2026_iw3_configstrings_initialize() {
    // Calls KisakCOD's authentic registry init, not an emulator.
    CCS_InitConstantConfigStrings();
}

extern "C" Z2026_NATIVE_EXPORT int z2026_iw3_configstring_num(const char* name) {
    if (name == nullptr) return -1;
    const int index = CCS_GetConstConfigStringIndex(name);
    if (index < 0) return -1;
    return CCS_GetConfigStringNumForConstIndex(static_cast<std::uint32_t>(index));
}

extern "C" Z2026_NATIVE_EXPORT int z2026_iw3_configstrings_smoke() {
    z2026_iw3_configstrings_initialize();
    return z2026_iw3_configstring_num("bg_aimSpreadMoveSpeedThreshold") == 20 &&
           z2026_iw3_configstring_num("specialty_rof") == 2034 &&
           z2026_iw3_configstring_num("SPECIALTY_ROF") == 2034 &&
           z2026_iw3_configstring_num("__not_a_valid_IW3_config__") == -1;
}

// Authentic IW3 Single-Player G_RunFrame prerequisite:
// Source is extracted without modification from com_shared.cpp's Com_Memcpy.
void Com_Memcpy(void *dest_p, const void *src_p, const std::size_t count);

extern "C" Z2026_NATIVE_EXPORT int z2026_iw3_frame_memcpy_smoke() {
    // The actual G_RunFrame copies 12 * pendingTriggerListSize bytes.
    // Verify that boundary calculation against real original Com_Memcpy.
    constexpr std::size_t trigger_stride = 12;
    constexpr std::size_t trigger_count = 4;
    unsigned char src[trigger_stride * trigger_count] {};
    unsigned char dst[trigger_stride * trigger_count + 2] {};
    for (std::size_t i = 0; i < sizeof(src); ++i) {
        src[i] = static_cast<unsigned char>(i ^ 0xA5);
    }
    dst[0] = 0xCD;
    dst[sizeof(dst) - 1] = 0xEF;
    Com_Memcpy(dst + 1, src, trigger_stride * trigger_count);
    if (dst[0] != 0xCD || dst[sizeof(dst) - 1] != 0xEF)
        return 0;
    if (std::memcmp(dst + 1, src, sizeof(src)) != 0)
        return 0;
    const unsigned char sentinel = 0x42;
    unsigned char dest = sentinel;
    Com_Memcpy(&dest, src, 0);
    return dest == sentinel;
}

extern "C" Z2026_NATIVE_EXPORT int z2026_iw3_real_pool_smoke() {
    // Runs actual KisakCOD Pool_Init/Alloc/Free/FreeCount linked from its
    // original translation unit. No simulated allocator implementation.
    struct alignas(void*) EnginePoolSlot {
        freenode link;
        std::uint64_t state_id;
        unsigned char payload[24];
    };
    EnginePoolSlot slots[5]{};
    pooldata_t pool{};
    Pool_Init(reinterpret_cast<char*>(slots), &pool, sizeof(slots[0]), 5);
    if (Pool_FreeCount(&pool) != 5 || pool.activeCount != 0) return 0;
    freenode *first = Pool_Alloc(&pool);
    freenode *second = Pool_Alloc(&pool);
    if (first != &slots[0].link || second != &slots[1].link ||
        Pool_FreeCount(&pool) != 3 || pool.activeCount != 2) return 0;
    Pool_Free(second, &pool);
    Pool_Free(first, &pool);
    if (Pool_FreeCount(&pool) != 5 || pool.activeCount != 0) return 0;
    return Pool_Alloc(&pool) == first && Pool_Alloc(&pool) == second;
}

void G_HitLocStrcpy(unsigned char *destination, const char *source);
extern "C" Z2026_NATIVE_EXPORT int z2026_iw3_hitloc_copy_smoke() {
    // Invoke the authentic KisakCOD SP g_combat.cpp function compiled
    // unchanged from its ARM64-corrected source, not a substitute copy.
    unsigned char dst[24];
    std::memset(dst, 0xC7, sizeof(dst));
    G_HitLocStrcpy(dst + 3, "head");
    return dst[2] == 0xC7 && dst[3] == 'h' && dst[4] == 'e' &&
           dst[5] == 'a' && dst[6] == 'd' && dst[7] == 0 &&
           dst[8] == 0xC7;
}
