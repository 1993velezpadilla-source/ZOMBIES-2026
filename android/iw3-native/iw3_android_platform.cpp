#include "iw3_android_platform.h"

#include <array>
#include <cerrno>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <limits>
#include <mutex>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

// Platform primitives only. NEVER call Win32 / DirectX / Steam / Godot.
// Directory handle is retained, protecting against later cwd changes.
// Per-component O_NOFOLLOW prevents symlink traversal during reads.
namespace {
std::mutex g_data_mutex;
int g_data_root_fd = -1;
std::mutex g_touch_mutex;
struct Touch {
    bool down = false;
    float x = 0;
    float y = 0;
};
std::array<Touch, 10> g_touches{};
bool valid_path(const char *p) {
    if (!p || !*p || *p == '/' || *p == '\\') return false;
    std::size_t len = 0;
    while (p[len] != 0) {
        if (++len >= 1024) return false;
        if (p[len - 1] == '\\') return false;
    }
    return true;
}
int open_beneath_root(int root, const char *path) {
    if (!valid_path(path)) return -1;
    const char *cursor = path;
    int parent = dup(root);
    if (parent < 0) return -1;
    while (*cursor) {
        const char *end = std::strchr(cursor, '/');
        const std::size_t len = end ? static_cast<std::size_t>(end - cursor) : std::strlen(cursor);
        if (len == 0 || len > 255 || (len == 1 && cursor[0] == '.') ||
            (len == 2 && cursor[0] == '.' && cursor[1] == '.')) {
            close(parent);
            return -1;
        }
        char component[256]{};
        std::memcpy(component, cursor, len);
        const bool last = (end == nullptr);
        const int fd = openat(parent, component,
            O_RDONLY | O_CLOEXEC | O_NOFOLLOW | (last ? O_NONBLOCK : O_DIRECTORY));
        close(parent);
        if (fd < 0) return -1;
        parent = fd;
        if (last) {
            struct stat st{};
            if (fstat(parent, &st) != 0 || !S_ISREG(st.st_mode)) {
                close(parent);
                return -1;
            }
            return parent;
        }
        cursor = end + 1;
    }
    close(parent);
    return -1;
}
} // namespace

extern "C" IW3_ANDROID_EXPORT std::uint64_t z2026_platform_monotonic_ns() {
    timespec current{};
    if (clock_gettime(CLOCK_MONOTONIC, &current) != 0) return 0;
    return static_cast<std::uint64_t>(current.tv_sec) * 1000000000ULL +
        static_cast<std::uint64_t>(current.tv_nsec);
}

extern "C" IW3_ANDROID_EXPORT int z2026_platform_set_data_root(const char *dir) {
    if (!dir || dir[0] != '/') return -1;
    const int fd = open(dir, O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) return -1;
    std::lock_guard<std::mutex> lock(g_data_mutex);
    if (g_data_root_fd >= 0) close(g_data_root_fd);
    g_data_root_fd = fd;
    return 0;
}

extern "C" IW3_ANDROID_EXPORT int z2026_platform_read_file(
    const char *relative, void *out, std::size_t capacity) {
    if (!out || !valid_path(relative) ||
        capacity > static_cast<std::size_t>(std::numeric_limits<int>::max())) return -1;
    std::lock_guard<std::mutex> lock(g_data_mutex);
    if (g_data_root_fd < 0) return -1;
    const int fd = open_beneath_root(g_data_root_fd, relative);
    if (fd < 0) return -1;
    // A zero-length buffer is legitimate for empty files.
    std::size_t transferred = 0;
    while (transferred < capacity) {
        const ssize_t n = read(fd, static_cast<unsigned char *>(out) + transferred,
                               capacity - transferred);
        if (n < 0 && errno == EINTR) continue;
        if (n < 0) { close(fd); return -1; }
        if (n == 0) break;
        transferred += static_cast<std::size_t>(n);
    }
    // Fail closed instead of truncating when the caller's buffer is too small.
    if (transferred == capacity) {
        unsigned char unused = 0;
        ssize_t probe;
        do { probe = read(fd, &unused, 1); } while (probe < 0 && errno == EINTR);
        if (probe != 0) { close(fd); return -1; }
    }
    close(fd);
    return static_cast<int>(transferred);
}

extern "C" IW3_ANDROID_EXPORT int z2026_platform_touch_event(
    int id, float x, float y, int down) {
    if (id < 0 || id >= static_cast<int>(g_touches.size()) ||
        !std::isfinite(x) || !std::isfinite(y) ||
        x < 0.0f || x > 1.0f || y < 0.0f || y > 1.0f ||
        (down != 0 && down != 1)) return -1;
    std::lock_guard<std::mutex> lock(g_touch_mutex);
    g_touches[static_cast<std::size_t>(id)] = {down == 1, x, y};
    return 0;
}

extern "C" IW3_ANDROID_EXPORT int z2026_platform_touch_snapshot(
    int id, float *x, float *y) {
    if (id < 0 || id >= static_cast<int>(g_touches.size()) || !x || !y) return -1;
    std::lock_guard<std::mutex> lock(g_touch_mutex);
    const Touch state = g_touches[static_cast<std::size_t>(id)];
    *x = state.x;
    *y = state.y;
    return state.down ? 1 : 0;
}

extern "C" IW3_ANDROID_EXPORT void z2026_platform_touch_reset() {
    std::lock_guard<std::mutex> lock(g_touch_mutex);
    g_touches.fill(Touch{});
}
