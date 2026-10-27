#include "iw3_android_platform.h"
#include "iw3_android_usercmd_compat.h"

#include <algorithm>
#include <array>
#include <cerrno>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <cctype>
#include <cstdlib>
#include <dirent.h>
#include <fcntl.h>
#include <limits.h>
#include <limits>
#include <mutex>
#include <string>
#include <vector>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

// Platform primitives only. NEVER call Win32 / DirectX / Steam / Godot.
// Directory handle is retained, protecting against later cwd changes.
// Per-component O_NOFOLLOW prevents symlink traversal during reads.
namespace {
std::mutex g_data_mutex;
int g_data_root_fd = -1;
std::string g_data_root_path;
std::mutex g_touch_mutex;
enum class TouchRole : std::uint8_t {
    None, Move, Look, Attack, Ads, Jump, Reload, Use, Melee, Crouch, Prone, Sprint, Slide
};
struct Touch {
    bool down = false;
    float x = 0;
    float y = 0;
    float origin_x = 0;
    float origin_y = 0;
    float previous_x = 0;
    float previous_y = 0;
    TouchRole role = TouchRole::None;
};
std::array<Touch, 10> g_touches{};
float g_view_yaw_degrees = 0.0f;
float g_view_pitch_degrees = 0.0f;
float g_pending_yaw_degrees = 0.0f;
float g_pending_pitch_degrees = 0.0f;

TouchRole classify_touch(float x, float y) {
    // Dedicated lower-left buttons keep sprint and slide distinct from the
    // left-thumb movement zone. Slide is the engine's sprint+crouch chord.
    if (x < 0.18f && y >= 0.76f) return TouchRole::Sprint;
    if (x >= 0.18f && x < 0.38f && y >= 0.76f) return TouchRole::Slide;
    if (x >= 0.82f && y >= 0.76f) return TouchRole::Attack;
    if (x >= 0.60f && x < 0.82f && y >= 0.76f) return TouchRole::Ads;
    if (x >= 0.60f && x < 0.82f && y >= 0.58f && y < 0.76f) return TouchRole::Jump;
    if (x >= 0.82f && y >= 0.58f && y < 0.76f) return TouchRole::Reload;
    if (x >= 0.82f && y >= 0.40f && y < 0.58f) return TouchRole::Use;
    if (x >= 0.60f && x < 0.82f && y >= 0.40f && y < 0.58f) return TouchRole::Melee;
    if (x >= 0.60f && x < 0.82f && y >= 0.22f && y < 0.40f) return TouchRole::Crouch;
    if (x >= 0.82f && y >= 0.22f && y < 0.40f) return TouchRole::Prone;
    return x < 0.48f ? TouchRole::Move : TouchRole::Look;
}

void update_touch_position(Touch &touch, float x, float y) {
    if (touch.role == TouchRole::Look) {
        const float yaw_delta = (x - touch.previous_x) * 240.0f;
        const float pitch_delta = (y - touch.previous_y) * 180.0f;
        g_view_yaw_degrees = std::remainder(
            g_view_yaw_degrees + yaw_delta, 360.0f);
        g_view_pitch_degrees = std::clamp(
            g_view_pitch_degrees + pitch_delta, -89.0f, 89.0f);
        // Keep frame deltas separate from diagnostic absolute angles. The
        // original CL_CreateCmd consumes each delta exactly once per command.
        g_pending_yaw_degrees += yaw_delta;
        g_pending_pitch_degrees += pitch_delta;
    }
    touch.previous_x = x;
    touch.previous_y = y;
    touch.x = x;
    touch.y = y;
}

int move_axis(float delta) {
    constexpr float dead_zone = 0.04f;
    constexpr float full_scale = 0.22f;
    const float magnitude = std::fabs(delta);
    if (magnitude <= dead_zone) return 0;
    const float normalized = std::clamp((magnitude - dead_zone) /
                                        (full_scale - dead_zone), 0.0f, 1.0f);
    const int value = static_cast<int>(std::lround(normalized * 127.0f));
    return delta < 0.0f ? -value : value;
}

int angle_to_short(float degrees) {
    const auto packed = static_cast<long long>(
        std::llround(static_cast<double>(degrees) * (65536.0 / 360.0)));
    return static_cast<int>(static_cast<std::uint16_t>(packed & 0xffffLL));
}
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


bool normalize_engine_path(const char *path, char output[1024], bool allow_root) {
    if (!path || !output || g_data_root_path.empty()) return false;

    // The original FS_BuildOSPathForThread/FS_ReplaceSeparators pair turns
    // even the leading slash of a POSIX absolute base into a backslash. Normalize
    // separators before checking absoluteness so that such paths are still
    // constrained to the retained Android data root, not misread as root-relative.
    std::string normalized_path_storage(path);
    for (char &character : normalized_path_storage) {
        if (character == '\\') character = '/';
    }
    const char *normalized_path = normalized_path_storage.c_str();
    const char *relative = normalized_path;
    if (normalized_path[0] == '/') {
        const std::string &root = g_data_root_path;
        if (root == normalized_path) {
            if (!allow_root) return false;
            output[0] = '\0';
            return true;
        }
        if (root == "/") {
            relative = normalized_path + 1;
        } else {
            const std::size_t root_length = root.size();
            if (std::strncmp(normalized_path, root.c_str(), root_length) != 0) return false;
            if (normalized_path[root_length] == '/') {
                relative = normalized_path + root_length + 1;
            } else {
                // Reject sibling-prefix attacks such as /data/app-evil.
                return false;
            }
        }
    }
    if (!*relative) {
        if (!allow_root) return false;
        output[0] = '\0';
        return true;
    }
    // valid_path rejects dot components after separator normalization, including
    // Windows-style ".." paths, before any openat traversal occurs.
    if (!valid_path(relative)) return false;
    const std::size_t length = std::strlen(relative);
    if (length >= 1024) return false;
    std::memcpy(output, relative, length + 1);
    return true;
}

int open_directory_beneath_root(int root, const char *path) {
    if (!path) return -1;
    if (!*path) {
        // Do not dup(root) here: dup shares the directory stream offset with
        // the retained root descriptor, so the first readdir would leave later
        // IWD scans at EOF. openat(".") gives each scan an independent open
        // file description while staying anchored to the trusted root fd.
        const int copy = openat(root, ".",
            O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
        if (copy < 0) return -1;
        struct stat st{};
        if (fstat(copy, &st) != 0 || !S_ISDIR(st.st_mode)) {
            close(copy);
            return -1;
        }
        return copy;
    }
    if (!valid_path(path)) return -1;
    int current = dup(root);
    if (current < 0) return -1;
    const char *cursor = path;
    while (*cursor) {
        const char *end = std::strchr(cursor, '/');
        const std::size_t length = end
            ? static_cast<std::size_t>(end - cursor) : std::strlen(cursor);
        if (length == 0 || length > 255 ||
            (length == 1 && cursor[0] == '.') ||
            (length == 2 && cursor[0] == '.' && cursor[1] == '.')) {
            close(current);
            return -1;
        }
        char component[256]{};
        std::memcpy(component, cursor, length);
        const int next = openat(current, component,
            O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
        close(current);
        if (next < 0) return -1;
        current = next;
        if (!end) break;
        cursor = end + 1;
    }
    struct stat st{};
    if (fstat(current, &st) != 0 || !S_ISDIR(st.st_mode)) {
        close(current);
        return -1;
    }
    return current;
}

bool has_iwd_extension(const char *name) {
    const std::size_t length = std::strlen(name);
    if (length < 4) return false;
    const char *extension = name + length - 4;
    return extension[0] == '.' &&
        std::tolower(static_cast<unsigned char>(extension[1])) == 'i' &&
        std::tolower(static_cast<unsigned char>(extension[2])) == 'w' &&
        std::tolower(static_cast<unsigned char>(extension[3])) == 'd';
}

int open_parent_beneath_root(int root, const char *path, char leaf[256]) {
    if (!valid_path(path) || !leaf) return -1;
    const char *cursor = path;
    int parent = dup(root);
    if (parent < 0) return -1;
    for (;;) {
        const char *end = std::strchr(cursor, '/');
        const std::size_t len = end
            ? static_cast<std::size_t>(end - cursor) : std::strlen(cursor);
        if (len == 0 || len > 255 ||
            (len == 1 && cursor[0] == '.') ||
            (len == 2 && cursor[0] == '.' && cursor[1] == '.')) {
            close(parent);
            return -1;
        }
        char component[256]{};
        std::memcpy(component, cursor, len);
        if (!end) {
            std::memcpy(leaf, component, len + 1);
            return parent;
        }
        const int next = openat(parent, component,
            O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
        close(parent);
        if (next < 0) return -1;
        parent = next;
        cursor = end + 1;
    }
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
    // POSIX requires a PATH_MAX-sized destination for realpath when the
    // caller supplies its own buffer. A 1 KiB buffer trips fortify on glibc
    // even for a short app path; validate our tighter stored-path limit after
    // canonicalization instead.
    char resolved[PATH_MAX]{};
    if (!realpath(dir, resolved) || std::strlen(resolved) >= 1024) return -1;
    std::string configured_root(dir);
    while (configured_root.size() > 1 && configured_root.back() == '/')
        configured_root.pop_back();
    if (configured_root.size() >= 1024 ||
        configured_root.find('\\') != std::string::npos) return -1;
    // Do not retain dot components in the prefix used to recognize the
    // engine's absolute FS_BuildOSPath strings. The descriptor itself still
    // points at the canonical realpath target, so accepted suffixes remain
    // opened beneath that descriptor even when Android exposes an alias path.
    std::size_t component_start = 1;
    while (component_start < configured_root.size()) {
        const std::size_t slash = configured_root.find('/', component_start);
        const std::size_t component_end = slash == std::string::npos
            ? configured_root.size() : slash;
        const std::string component = configured_root.substr(
            component_start, component_end - component_start);
        if (component.empty() || component == "." || component == "..") return -1;
        if (slash == std::string::npos) break;
        component_start = slash + 1;
    }
    const int fd = open(resolved, O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) return -1;
    std::lock_guard<std::mutex> lock(g_data_mutex);
    if (g_data_root_fd >= 0) close(g_data_root_fd);
    g_data_root_fd = fd;
    g_data_root_path = configured_root;
    return 0;
}

extern "C" IW3_ANDROID_EXPORT int z2026_platform_copy_data_root(
    char *destination, std::size_t capacity) {
    if (!destination || capacity == 0) return -1;
    destination[0] = '\0';
    std::lock_guard<std::mutex> lock(g_data_mutex);
    if (g_data_root_fd < 0 || g_data_root_path.empty() ||
        g_data_root_path.size() >= capacity) return -1;
    std::memcpy(destination, g_data_root_path.c_str(), g_data_root_path.size() + 1);
    return static_cast<int>(g_data_root_path.size());
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


extern "C" IW3_ANDROID_EXPORT int z2026_platform_open_read_fd(
    const char *relative) {
    if (!valid_path(relative)) return -1;
    std::lock_guard<std::mutex> lock(g_data_mutex);
    if (g_data_root_fd < 0) return -1;
    return open_beneath_root(g_data_root_fd, relative);
}


extern "C" IW3_ANDROID_EXPORT int z2026_platform_open_engine_path_fd(
    const char *path) {
    char relative[1024]{};
    std::lock_guard<std::mutex> lock(g_data_mutex);
    if (g_data_root_fd < 0 ||
        !normalize_engine_path(path, relative, false)) return -1;
    return open_beneath_root(g_data_root_fd, relative);
}

extern "C" IW3_ANDROID_EXPORT int z2026_platform_list_iwd_files(
    const char *directory, char *output, std::size_t output_capacity,
    std::size_t *entry_count) {
    if (!entry_count || (!output && output_capacity)) return -1;
    *entry_count = 0;
    char relative[1024]{};
    std::lock_guard<std::mutex> lock(g_data_mutex);
    if (g_data_root_fd < 0 ||
        !normalize_engine_path(directory, relative, true)) return -1;
    const int fd = open_directory_beneath_root(g_data_root_fd, relative);
    if (fd < 0) return -1;
    DIR *stream = fdopendir(fd);
    if (!stream) {
        close(fd);
        return -1;
    }

    // The authentic FS_AddIwdFilesForGameDirectory caps the Sys_ListFiles
    // result at 1024 entries BEFORE sorting those retained entries. Preserve
    // that contract: retain the first 1024 valid names in native directory
    // enumeration order, count all valid IWDs, and let the original engine
    // sort the retained prefix. Do not silently substitute the lexicographically
    // smallest 1024 archives; that changes which archives the engine mounts.
    constexpr std::size_t kMaxReturnedIwdFiles = 1024;
    std::vector<std::string> names;
    names.reserve(kMaxReturnedIwdFiles);
    std::size_t total_count = 0;
    bool read_error = false;
    for (;;) {
        errno = 0;
        dirent *entry = readdir(stream);
        if (!entry) {
            read_error = errno != 0;
            break;
        }
        if (entry->d_name[0] == '.' ||
            !has_iwd_extension(entry->d_name)) continue;
        struct stat st{};
        if (fstatat(dirfd(stream), entry->d_name, &st,
                    AT_SYMLINK_NOFOLLOW) != 0 || !S_ISREG(st.st_mode)) {
            continue;
        }
        if (total_count == std::numeric_limits<std::size_t>::max()) {
            read_error = true;
            break;
        }
        ++total_count;
        if (names.size() < kMaxReturnedIwdFiles) {
            names.emplace_back(entry->d_name);
        }
    }
    if (closedir(stream) != 0) read_error = true;
    if (read_error) return -1;

    std::size_t needed = 0;
    for (const std::string &name : names) {
        if (name.size() + 1 > std::numeric_limits<std::size_t>::max() - needed)
            return -1;
        needed += name.size() + 1;
    }
    if (needed > output_capacity || (needed && !output) ||
        needed > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
        return -1;
    }
    std::size_t offset = 0;
    for (const std::string &name : names) {
        std::memcpy(output + offset, name.c_str(), name.size() + 1);
        offset += name.size() + 1;
    }
    *entry_count = total_count;
    return static_cast<int>(needed);
}

extern "C" IW3_ANDROID_EXPORT int z2026_platform_directory_has_contents(
    const char *directory) {
    char relative[1024]{};
    std::lock_guard<std::mutex> lock(g_data_mutex);
    if (g_data_root_fd < 0 ||
        !normalize_engine_path(directory, relative, true)) return -1;
    const int fd = open_directory_beneath_root(g_data_root_fd, relative);
    if (fd < 0) return -1;
    DIR *stream = fdopendir(fd);
    if (!stream) {
        close(fd);
        return -1;
    }

    int result = 0;
    bool read_error = false;
    for (;;) {
        errno = 0;
        dirent *entry = readdir(stream);
        if (!entry) {
            read_error = errno != 0;
            break;
        }
        if (!std::strcmp(entry->d_name, ".") ||
            !std::strcmp(entry->d_name, "..")) continue;

        struct stat st{};
        if (fstatat(dirfd(stream), entry->d_name, &st,
                    AT_SYMLINK_NOFOLLOW) != 0) {
            if (errno == ENOENT) continue;
            read_error = true;
            break;
        }
        // Fail closed on symlinks; directory scanning must remain beneath the
        // retained app-data root even when a file changes during enumeration.
        if (S_ISLNK(st.st_mode)) continue;
        if (!S_ISDIR(st.st_mode) || std::strcmp(entry->d_name, "CVS") != 0) {
            result = 1;
            break;
        }
    }
    if (closedir(stream) != 0) read_error = true;
    return read_error ? -1 : result;
}

extern "C" IW3_ANDROID_EXPORT int z2026_platform_mkdir(const char *relative) {
    if (!valid_path(relative)) return -1;
    std::lock_guard<std::mutex> lock(g_data_mutex);
    if (g_data_root_fd < 0) return -1;
    char leaf[256]{};
    const int parent = open_parent_beneath_root(g_data_root_fd, relative, leaf);
    if (parent < 0) return -1;
    int rc = mkdirat(parent, leaf, 0700);
    if (rc != 0 && errno == EEXIST) {
        struct stat st{};
        if (fstatat(parent, leaf, &st, AT_SYMLINK_NOFOLLOW) == 0 &&
            S_ISDIR(st.st_mode)) rc = 0;
    }
    close(parent);
    return rc;
}

extern "C" IW3_ANDROID_EXPORT int z2026_platform_rmdir(const char *relative) {
    if (!valid_path(relative)) return -1;
    std::lock_guard<std::mutex> lock(g_data_mutex);
    if (g_data_root_fd < 0) return -1;
    char leaf[256]{};
    const int parent = open_parent_beneath_root(g_data_root_fd, relative, leaf);
    if (parent < 0) return -1;
    const int rc = unlinkat(parent, leaf, AT_REMOVEDIR);
    close(parent);
    return rc;
}

extern "C" IW3_ANDROID_EXPORT int z2026_platform_write_file(
    const char *relative, const void *source, std::size_t length) {
    if (!valid_path(relative) || (!source && length) ||
        length > static_cast<std::size_t>(std::numeric_limits<int>::max())) return -1;
    std::lock_guard<std::mutex> lock(g_data_mutex);
    if (g_data_root_fd < 0) return -1;
    char leaf[256]{};
    const int parent = open_parent_beneath_root(g_data_root_fd, relative, leaf);
    if (parent < 0) return -1;
    const int fd = openat(parent, leaf,
        O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC | O_NOFOLLOW, 0600);
    if (fd < 0) { close(parent); return -1; }
    struct stat st{};
    if (fstat(fd, &st) != 0 || !S_ISREG(st.st_mode)) {
        close(fd); close(parent); return -1;
    }
    std::size_t written = 0;
    while (written < length) {
        const ssize_t n = ::write(fd,
            static_cast<const unsigned char *>(source) + written, length - written);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) {
            close(fd);
            unlinkat(parent, leaf, 0);
            close(parent);
            return -1;
        }
        written += static_cast<std::size_t>(n);
    }
    const int close_result = close(fd);
    close(parent);
    return close_result == 0 ? static_cast<int>(written) : -1;
}

extern "C" IW3_ANDROID_EXPORT int z2026_platform_unlink_file(
    const char *relative) {
    if (!valid_path(relative)) return -1;
    std::lock_guard<std::mutex> lock(g_data_mutex);
    if (g_data_root_fd < 0) return -1;
    char leaf[256]{};
    const int parent = open_parent_beneath_root(g_data_root_fd, relative, leaf);
    if (parent < 0) return -1;
    const int rc = unlinkat(parent, leaf, 0);
    close(parent);
    return rc;
}

extern "C" IW3_ANDROID_EXPORT int z2026_platform_touch_event(
    int id, float x, float y, int down) {
    if (id < 0 || id >= static_cast<int>(g_touches.size()) ||
        !std::isfinite(x) || !std::isfinite(y) ||
        x < 0.0f || x > 1.0f || y < 0.0f || y > 1.0f ||
        (down != 0 && down != 1)) return -1;
    std::lock_guard<std::mutex> lock(g_touch_mutex);
    Touch &touch = g_touches[static_cast<std::size_t>(id)];
    if (down == 1) {
        if (!touch.down) {
            touch.down = true;
            touch.x = touch.origin_x = touch.previous_x = x;
            touch.y = touch.origin_y = touch.previous_y = y;
            touch.role = classify_touch(x, y);
        } else {
            update_touch_position(touch, x, y);
        }
    } else {
        if (touch.down) update_touch_position(touch, x, y);
        else { touch.x = x; touch.y = y; }
        touch.down = false;
        touch.role = TouchRole::None;
    }
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
    g_view_yaw_degrees = 0.0f;
    g_view_pitch_degrees = 0.0f;
    g_pending_yaw_degrees = 0.0f;
    g_pending_pitch_degrees = 0.0f;
}

extern "C" IW3_ANDROID_EXPORT int z2026_platform_usercmd_snapshot(
    int server_time, int *fields, std::size_t field_count) {
    if (!fields || field_count < 10 || server_time < 0) return -1;
    std::lock_guard<std::mutex> lock(g_touch_mutex);
    usercmd_s command{};
    command.serverTime = server_time;
    command.angles[0] = angle_to_short(g_view_pitch_degrees);
    command.angles[1] = angle_to_short(g_view_yaw_degrees);
    bool movement_claimed = false;
    for (const Touch &touch : g_touches) {
        if (!touch.down) continue;
        switch (touch.role) {
        case TouchRole::Move:
            if (!movement_claimed) {
                command.forwardmove = static_cast<char>(move_axis(touch.origin_y - touch.y));
                command.rightmove = static_cast<char>(move_axis(touch.x - touch.origin_x));
                movement_claimed = true;
            }
            break;
        case TouchRole::Sprint: command.buttons |= BUTTON_SPRINT; break;
        case TouchRole::Slide: command.buttons |= BUTTON_SPRINT | BUTTON_CROUCH; break;
        case TouchRole::Attack: command.buttons |= BUTTON_ATTACK; break;
        case TouchRole::Ads: command.buttons |= BUTTON_ADS; break;
        case TouchRole::Jump: command.buttons |= BUTTON_JUMP; break;
        case TouchRole::Reload: command.buttons |= BUTTON_RELOAD; break;
        case TouchRole::Use: command.buttons |= BUTTON_USE; break;
        case TouchRole::Melee: command.buttons |= BUTTON_MELEE; break;
        case TouchRole::Crouch: command.buttons |= BUTTON_CROUCH; break;
        case TouchRole::Prone: command.buttons |= BUTTON_PRONE; break;
        case TouchRole::None:
        case TouchRole::Look: break;
        }
    }
    fields[0] = command.serverTime;
    fields[1] = command.buttons;
    fields[2] = command.angles[0];
    fields[3] = command.angles[1];
    fields[4] = command.angles[2];
    fields[5] = static_cast<int>(static_cast<signed char>(command.forwardmove));
    fields[6] = static_cast<int>(static_cast<signed char>(command.rightmove));
    fields[7] = static_cast<int>(static_cast<signed char>(command.upmove));
    fields[8] = static_cast<int>(static_cast<signed char>(command.pitchmove));
    fields[9] = static_cast<int>(static_cast<signed char>(command.yawmove));
    return 0;
}

extern "C" IW3_ANDROID_EXPORT void z2026_platform_apply_touch_to_usercmd(
    usercmd_s *command, float *viewangles) {
    if (!command || !viewangles) return;
    std::lock_guard<std::mutex> lock(g_touch_mutex);

    // A touch-look delta is applied once to the original client viewangles;
    // CL_FinishMove then encodes these into the real IW3 usercmd_s.
    const float pitch_delta = std::clamp(g_pending_pitch_degrees, -90.0f, 90.0f);
    const float yaw_delta = std::remainder(g_pending_yaw_degrees, 360.0f);
    viewangles[0] = std::clamp(viewangles[0] + pitch_delta, -89.0f, 89.0f);
    viewangles[1] = std::remainder(viewangles[1] + yaw_delta, 360.0f);
    g_pending_pitch_degrees = 0.0f;
    g_pending_yaw_degrees = 0.0f;

    bool movement_claimed = false;
    bool want_crouch = false;
    bool want_prone = false;
    for (const Touch &touch : g_touches) {
        if (!touch.down) continue;
        switch (touch.role) {
        case TouchRole::Move:
            if (!movement_claimed) {
                const int forward = move_axis(touch.origin_y - touch.y);
                const int right = move_axis(touch.x - touch.origin_x);
                const int current_forward = static_cast<signed char>(command->forwardmove);
                const int current_right = static_cast<signed char>(command->rightmove);
                command->forwardmove = static_cast<char>(std::clamp(current_forward + forward, -127, 127));
                command->rightmove = static_cast<char>(std::clamp(current_right + right, -127, 127));
                movement_claimed = true;
            }
            break;
        case TouchRole::Sprint: command->buttons |= BUTTON_SPRINT; break;
        case TouchRole::Slide:
            command->buttons |= BUTTON_SPRINT;
            want_crouch = true;
            break;
        case TouchRole::Attack: command->buttons |= BUTTON_ATTACK; break;
        case TouchRole::Ads: command->buttons |= BUTTON_ADS; break;
        case TouchRole::Jump: command->buttons |= BUTTON_JUMP; break;
        case TouchRole::Reload: command->buttons |= BUTTON_RELOAD; break;
        case TouchRole::Use: command->buttons |= BUTTON_USE; break;
        case TouchRole::Melee: command->buttons |= BUTTON_MELEE; break;
        case TouchRole::Crouch: want_crouch = true; break;
        case TouchRole::Prone: want_prone = true; break;
        case TouchRole::None:
        case TouchRole::Look: break;
        }
    }
    if (want_prone) {
        command->buttons |= BUTTON_PRONE;
        command->buttons &= ~BUTTON_CROUCH;
    } else if (want_crouch) {
        command->buttons |= BUTTON_CROUCH;
        command->buttons &= ~BUTTON_PRONE;
    }
}
