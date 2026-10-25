// C ABI for exercising REAL KisakCOD AngleVectors from Android arm64.
#include <cmath>
#include <cstddef>

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
