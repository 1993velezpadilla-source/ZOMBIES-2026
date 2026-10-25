#include "iw3_android_platform.h"
#include "iw3_android_usercmd_compat.h"

#include <algorithm>
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
enum class TouchRole : std::uint8_t {
    None, Move, Look, Attack, Ads, Jump, Reload, Use, Melee, Crouch, Prone
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


extern "C" IW3_ANDROID_EXPORT int z2026_platform_open_read_fd(
    const char *relative) {
    if (!valid_path(relative)) return -1;
    std::lock_guard<std::mutex> lock(g_data_mutex);
    if (g_data_root_fd < 0) return -1;
    return open_beneath_root(g_data_root_fd, relative);
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
