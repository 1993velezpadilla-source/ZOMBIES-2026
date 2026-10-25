#pragma once
// Android/POSIX platform boundary for a future native KisakCOD SP runtime.
// NOT an alternate game engine. No renderer, artificial gameplay, or assets.
#include <cstddef>
#include <cstdint>

#if defined(__GNUC__)
#define IW3_ANDROID_EXPORT __attribute__((visibility("default")))
#else
#define IW3_ANDROID_EXPORT
#endif

extern "C" {
// Clock: monotonic elapsed nanoseconds, unaffected by wall time changes.
IW3_ANDROID_EXPORT std::uint64_t z2026_platform_monotonic_ns();

// Sandbox reads only: all paths relative to an opened app-owned directory.
// A 0 return is success. The service retains its own root descriptor.
IW3_ANDROID_EXPORT int z2026_platform_set_data_root(const char *absolute_dir);
IW3_ANDROID_EXPORT int z2026_platform_read_file(
    const char *relative_path, void *destination, std::size_t capacity);

// For the future Android input bridge: fingertip IDs [0, 9], coordinates
// normalized [0, 1]. Actual game usercmd wiring is NOT yet implemented.
IW3_ANDROID_EXPORT int z2026_platform_touch_event(
    int pointer_id, float normalized_x, float normalized_y, int down);
IW3_ANDROID_EXPORT int z2026_platform_touch_snapshot(
    int pointer_id, float *normalized_x, float *normalized_y);
IW3_ANDROID_EXPORT void z2026_platform_touch_reset();
}
