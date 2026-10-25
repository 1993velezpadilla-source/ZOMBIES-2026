#include "iw3_android_platform.h"
#include "iw3_android_usercmd_compat.h"

#include <cassert>
#include <chrono>
#include <cstdlib>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include <thread>

int main() {
    const std::uint64_t start = z2026_platform_monotonic_ns();
    std::this_thread::sleep_for(std::chrono::milliseconds(2));
    const std::uint64_t end = z2026_platform_monotonic_ns();
    assert(start != 0 && end > start);

    char tmp[] = "/tmp/z2026-iw3-XXXXXX";
    const char *root = mkdtemp(tmp);
    assert(root);
    const std::string path = std::string(root) + "/sample.txt";
    const int fd = open(path.c_str(), O_WRONLY | O_CREAT | O_EXCL, 0600);
    assert(fd >= 0);
    assert(write(fd, "IW3", 3) == 3);
    close(fd);
    assert(z2026_platform_set_data_root(root) == 0);
    assert(z2026_platform_set_data_root(".") == -1);
    unsigned char buffer[4]{};
    assert(z2026_platform_read_file("sample.txt", buffer, sizeof(buffer)) == 3);
    assert(std::memcmp(buffer, "IW3", 3) == 0);
    assert(z2026_platform_read_file("../sample.txt", buffer, sizeof(buffer)) == -1);
    assert(z2026_platform_read_file("/etc/passwd", buffer, sizeof(buffer)) == -1);
    assert(z2026_platform_read_file("sample.txt/..", buffer, sizeof(buffer)) == -1);
    assert(z2026_platform_read_file("sample.txt", buffer, 2) == -1);
    assert(z2026_platform_read_file("", buffer, sizeof(buffer)) == -1);
    assert(z2026_platform_read_file("fake.txt", buffer, sizeof(buffer)) == -1);

    // The original ZIP/IWD reader now opens relative archive names through
    // the retained data root, not unrestricted absolute fopen paths.
    const int rooted_fd = z2026_platform_open_read_fd("sample.txt");
    assert(rooted_fd >= 0);
    unsigned char rooted_bytes[3]{};
    assert(read(rooted_fd, rooted_bytes, sizeof(rooted_bytes)) == 3);
    assert(std::memcmp(rooted_bytes, "IW3", 3) == 0);
    close(rooted_fd);
    assert(z2026_platform_open_read_fd("../sample.txt") == -1);
    assert(z2026_platform_open_read_fd("/etc/passwd") == -1);
    assert(z2026_platform_write_file("../escape.bin", "bad", 3) == -1);
    assert(z2026_platform_write_file("/absolute.bin", "bad", 3) == -1);
    assert(z2026_platform_write_file("generated.iwd", "IWD", 3) == 3);
    assert(z2026_platform_read_file("generated.iwd", buffer, sizeof(buffer)) == 3);
    assert(std::memcmp(buffer, "IWD", 3) == 0);
    assert(z2026_platform_unlink_file("generated.iwd") == 0);
    assert(z2026_platform_open_read_fd("generated.iwd") == -1);
    // Actual IW3 game data is nested (e.g. main/zone), not flat.
    // Exercise an app-owned nested file while rejecting directory symlinks.
    const std::string main_dir = std::string(root) + "/main";
    assert(mkdir(main_dir.c_str(), 0700) == 0);
    const std::string nested = main_dir + "/native-test.iwd";
    const int nested_fd = open(nested.c_str(), O_WRONLY | O_CREAT | O_EXCL, 0600);
    assert(nested_fd >= 0);
    assert(write(nested_fd, "IWD", 3) == 3);
    close(nested_fd);
    assert(z2026_platform_read_file("main/native-test.iwd", buffer, sizeof(buffer)) == 3);
    assert(std::memcmp(buffer, "IWD", 3) == 0);
    assert(z2026_platform_read_file("main/../sample.txt", buffer, sizeof(buffer)) == -1);
    const std::string linked_dir = std::string(root) + "/linked-main";
    assert(symlink(main_dir.c_str(), linked_dir.c_str()) == 0);
    assert(z2026_platform_read_file("linked-main/native-test.iwd", buffer, sizeof(buffer)) == -1);
    assert(unlink(linked_dir.c_str()) == 0);
    assert(unlink(nested.c_str()) == 0);
    assert(rmdir(main_dir.c_str()) == 0);

    const std::string symlink_path = std::string(root) + "/outside";
    assert(symlink("/etc/passwd", symlink_path.c_str()) == 0);
    assert(z2026_platform_read_file("outside", buffer, sizeof(buffer)) == -1);
    assert(z2026_platform_open_read_fd("outside") == -1);
    assert(z2026_platform_write_file("outside", "bad", 3) == -1);
    assert(z2026_platform_unlink_file("outside") == 0);

    z2026_platform_touch_reset();
    float x = 4, y = 4;
    assert(z2026_platform_touch_snapshot(0, &x, &y) == 0);
    assert(z2026_platform_touch_event(0, 0.25f, 0.75f, 1) == 0);
    assert(z2026_platform_touch_snapshot(0, &x, &y) == 1);
    assert(std::fabs(x - .25f) < .001f && std::fabs(y - .75f) < .001f);
    assert(z2026_platform_touch_event(0, 0.25f, 0.75f, 0) == 0);
    assert(z2026_platform_touch_snapshot(0, &x, &y) == 0);
    assert(z2026_platform_touch_event(99, .5f, .5f, 1) == -1);
    assert(z2026_platform_touch_event(0, 1.01f, .5f, 1) == -1);
    assert(z2026_platform_touch_event(0, NAN, .5f, 1) == -1);

    // Use the actual IW3 SP usercmd_s ABI from qcommon/msg.h.
    z2026_platform_touch_reset();
    int cmd[10]{};
    assert(z2026_platform_usercmd_snapshot(1234, cmd, 10) == 0);
    assert(cmd[0] == 1234 && cmd[1] == 0);
    assert(cmd[2] == 0 && cmd[3] == 0 && cmd[4] == 0);
    assert(cmd[5] == 0 && cmd[6] == 0 && cmd[7] == 0);
    assert(z2026_platform_usercmd_snapshot(1234, cmd, 9) == -1);
    assert(z2026_platform_usercmd_snapshot(-1, cmd, 10) == -1);
    assert(z2026_platform_touch_event(0, .20f, .70f, 1) == 0);
    assert(z2026_platform_touch_event(0, .38f, .55f, 1) == 0);
    assert(z2026_platform_touch_event(1, .90f, .85f, 1) == 0); // attack
    assert(z2026_platform_touch_event(2, .70f, .85f, 1) == 0); // ADS
    assert(z2026_platform_touch_event(3, .70f, .65f, 1) == 0); // jump
    assert(z2026_platform_touch_event(4, .90f, .65f, 1) == 0); // reload
    assert(z2026_platform_touch_event(5, .90f, .48f, 1) == 0); // use
    assert(z2026_platform_touch_event(6, .70f, .48f, 1) == 0); // melee
    assert(z2026_platform_touch_event(7, .70f, .30f, 1) == 0); // crouch
    assert(z2026_platform_touch_event(8, .90f, .30f, 1) == 0); // prone
    assert(z2026_platform_touch_event(9, .55f, .50f, 1) == 0); // look
    assert(z2026_platform_touch_event(9, .65f, .45f, 1) == 0);
    assert(z2026_platform_usercmd_snapshot(4321, cmd, 10) == 0);
    assert(cmd[0] == 4321);
    assert((cmd[1] & BUTTON_ATTACK) != 0 && (cmd[1] & BUTTON_ADS) != 0);
    assert((cmd[1] & BUTTON_JUMP) != 0 && (cmd[1] & BUTTON_RELOAD) != 0);
    assert((cmd[1] & BUTTON_USE) != 0 && (cmd[1] & BUTTON_MELEE) != 0);
    assert((cmd[1] & BUTTON_CROUCH) != 0 && (cmd[1] & BUTTON_PRONE) != 0);
    assert(cmd[5] > 0 && cmd[6] > 0);
    assert(cmd[2] != 0 && cmd[3] != 0);
    assert(z2026_platform_touch_event(1, .90f, .85f, 0) == 0);
    assert(z2026_platform_usercmd_snapshot(4322, cmd, 10) == 0);
    assert((cmd[1] & BUTTON_ATTACK) == 0);
    z2026_platform_touch_reset();
    assert(z2026_platform_usercmd_snapshot(4323, cmd, 10) == 0);
    assert(cmd[1] == 0 && cmd[2] == 0 && cmd[3] == 0);
    assert(cmd[5] == 0 && cmd[6] == 0);

    // Prove the bridge mutates an actual original usercmd_s exactly where
    // CL_CreateCmd will call it, rather than merely returning a side snapshot.
    z2026_platform_touch_reset();
    usercmd_s actual_command{};
    float actual_viewangles[3] = {10.0f, 20.0f, 0.0f};
    assert(z2026_platform_touch_event(0, .20f, .70f, 1) == 0); // movement
    assert(z2026_platform_touch_event(0, .38f, .55f, 1) == 0);
    assert(z2026_platform_touch_event(1, .90f, .85f, 1) == 0); // attack
    assert(z2026_platform_touch_event(2, .55f, .50f, 1) == 0); // look
    assert(z2026_platform_touch_event(2, .65f, .45f, 1) == 0);
    z2026_platform_apply_touch_to_usercmd(&actual_command, actual_viewangles);
    assert((actual_command.buttons & BUTTON_ATTACK) != 0);
    assert(actual_command.forwardmove > 0 && actual_command.rightmove > 0);
    assert(std::fabs(actual_viewangles[0] - 1.0f) < .01f);
    assert(std::fabs(actual_viewangles[1] - 44.0f) < .01f);
    const float applied_pitch = actual_viewangles[0];
    const float applied_yaw = actual_viewangles[1];
    // CL_CreateCmd zeroes a fresh usercmd_s each frame; mirror that contract
    // instead of reusing a command whose button bits were already set.
    usercmd_s repeated_frame{};
    z2026_platform_apply_touch_to_usercmd(&repeated_frame, actual_viewangles);
    assert(actual_viewangles[0] == applied_pitch && actual_viewangles[1] == applied_yaw);
    assert((repeated_frame.buttons & BUTTON_ATTACK) != 0);
    assert(z2026_platform_touch_event(1, .90f, .85f, 0) == 0);
    usercmd_s released_frame{};
    z2026_platform_apply_touch_to_usercmd(&released_frame, actual_viewangles);
    assert((released_frame.buttons & BUTTON_ATTACK) == 0);
    z2026_platform_touch_reset();
    std::puts("IW3_ANDROID_TOUCH_TO_ORIGINAL_USERCMD_HOST_GREEN");

    unlink(symlink_path.c_str());
    unlink(path.c_str());
    rmdir(root);
    std::puts("IW3_ANDROID_PLATFORM_HOST_TEST_GREEN (time, sandbox IO, multi-touch)");
}
