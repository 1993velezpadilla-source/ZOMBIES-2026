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

// Rooted native file primitives for the original ZIP/IWD reader. The returned
// descriptor is owned by the caller; it is opened beneath the retained root,
// rejecting absolute paths, dot components and symlink traversal.
IW3_ANDROID_EXPORT int z2026_platform_open_read_fd(const char *relative_path);
 
// Original FS_BuildOSPath callers may supply an absolute path. This variant
// accepts it only when it is beneath the canonical app-data root.
IW3_ANDROID_EXPORT int z2026_platform_open_engine_path_fd(const char *path);

// Enumerate regular *.iwd files directly inside a rooted directory. The
// output is NUL-separated basenames (no partial writes); empty directory means
// the root itself. Returns byte count, or -1 on error/capacity overflow.
IW3_ANDROID_EXPORT int z2026_platform_list_iwd_files(
    const char *directory, char *output, std::size_t output_capacity,
    std::size_t *entry_count);
IW3_ANDROID_EXPORT int z2026_platform_write_file(
    const char *relative_path, const void *source, std::size_t length);
IW3_ANDROID_EXPORT int z2026_platform_unlink_file(const char *relative_path);

// Android touch state plus a native adapter to original usercmd_s layout.
// CL_CreateCmd/game-frame consumption remains pending.
IW3_ANDROID_EXPORT int z2026_platform_touch_event(
    int pointer_id, float normalized_x, float normalized_y, int down);
IW3_ANDROID_EXPORT int z2026_platform_touch_snapshot(
    int pointer_id, float *normalized_x, float *normalized_y);
IW3_ANDROID_EXPORT void z2026_platform_touch_reset();

// fields[10] = serverTime, buttons, packed pitch/yaw/roll angles, then
// forward/right/up/pitch/yaw movement. Uses authentic qcommon/msg.h usercmd_s.
// Diagnostic snapshot only; the original client source also has an Android-only
// apply hook, but cl_input.cpp is not yet part of the Android shared-library target.
IW3_ANDROID_EXPORT int z2026_platform_usercmd_snapshot(
    int server_time, int *fields, std::size_t field_count);

// Merge current Android touch state into a real original usercmd_s before
// CL_FinishMove encodes viewangles. The original CL_CreateCmd source is wired
// to call this only on Android; that client TU still needs Android build integration.
struct usercmd_s;
IW3_ANDROID_EXPORT void z2026_platform_apply_touch_to_usercmd(
    struct usercmd_s *command, float *viewangles);
}
