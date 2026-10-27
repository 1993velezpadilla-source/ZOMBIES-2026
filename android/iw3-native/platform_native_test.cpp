#include "iw3_android_platform.h"
#include "iw3_android_usercmd_compat.h"

#include <cassert>
#include <chrono>
#include <cstdlib>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <dirent.h>
#include <fcntl.h>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include <thread>
#include <vector>

extern "C" int z2026_iw3_fs_startup_path_smoke();

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
    const std::string empty_path = std::string(root) + "/empty.txt";
    const int empty_fd = open(empty_path.c_str(), O_WRONLY | O_CREAT | O_EXCL, 0600);
    assert(empty_fd >= 0);
    close(empty_fd);
    assert(z2026_platform_set_data_root(root) == 0);
    char copied_root[1024]{};
    assert(z2026_platform_copy_data_root(copied_root, sizeof(copied_root)) ==
           static_cast<int>(std::strlen(root)));
    assert(std::strcmp(copied_root, root) == 0);
    assert(z2026_iw3_fs_startup_path_smoke() == 1);
    char too_small_root[1] = {'x'};
    assert(z2026_platform_copy_data_root(too_small_root, sizeof(too_small_root)) == -1);
    assert(too_small_root[0] == '\0');
    assert(z2026_platform_set_data_root(".") == -1);
    unsigned char buffer[4]{};
    assert(z2026_platform_read_file("sample.txt", buffer, sizeof(buffer)) == 3);
    assert(std::memcmp(buffer, "IW3", 3) == 0);
    // A null output is valid only for a zero-capacity existence/empty-file probe.
    assert(z2026_platform_read_file("empty.txt", nullptr, 0) == 0);
    assert(z2026_platform_read_file("sample.txt", nullptr, 0) == -1);
    assert(z2026_platform_read_file("sample.txt", nullptr, 1) == -1);
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
    // The original desktop FS_LoadZipFile passes FS_BuildOSPath absolute
    // paths. Android accepts only absolute paths rooted beneath filesDir.
    int engine_path_fd = z2026_platform_open_engine_path_fd(path.c_str());
    assert(engine_path_fd >= 0);
    unsigned char engine_path_bytes[3]{};
    assert(read(engine_path_fd, engine_path_bytes, sizeof(engine_path_bytes)) == 3);
    assert(std::memcmp(engine_path_bytes, "IW3", 3) == 0);
    close(engine_path_fd);
    assert(z2026_platform_open_engine_path_fd("/etc/passwd") == -1);
    const std::string prefix_attack = std::string(root) + "-sibling/sample.txt";
    assert(z2026_platform_open_engine_path_fd(prefix_attack.c_str()) == -1);
    const std::string windows_engine_path = std::string(root) + "\\sample.txt";
    int windows_path_fd = z2026_platform_open_engine_path_fd(windows_engine_path.c_str());
    assert(windows_path_fd >= 0);
    close(windows_path_fd);
    assert(z2026_platform_open_engine_path_fd("main\\..\\sample.txt") == -1);
    // FS_ReplaceSeparators also converts the leading slash of an absolute
    // original-engine path. It must still be recognized as absolute and rooted.
    const std::string windows_rooted_engine_path =
        std::string("\\") + std::string(root).substr(1) + "\\sample.txt";
    int windows_rooted_fd =
        z2026_platform_open_engine_path_fd(windows_rooted_engine_path.c_str());
    assert(windows_rooted_fd >= 0);
    close(windows_rooted_fd);
    assert(z2026_platform_open_engine_path_fd("\\etc\\passwd") == -1);
    assert(z2026_platform_write_file("../escape.bin", "bad", 3) == -1);
    assert(z2026_platform_write_file("/absolute.bin", "bad", 3) == -1);
    assert(z2026_platform_write_file("generated.iwd", "IWD", 3) == 3);
    assert(z2026_platform_read_file("generated.iwd", buffer, sizeof(buffer)) == 3);
    assert(std::memcmp(buffer, "IWD", 3) == 0);

    // The original engine caps the list at 1024 before qsorting it.
    // Capture this directory's native readdir prefix so the platform adapter
    // cannot silently replace it with the lexicographically smallest archives.
    const std::string many_iwd_dir = std::string(root) + "/many-iwd";
    assert(mkdir(many_iwd_dir.c_str(), 0700) == 0);
    constexpr int kManyIwdCount = 1030;
    for (int i = 0; i < kManyIwdCount; ++i) {
        char name[40]{};
        assert(std::snprintf(name, sizeof(name), "archive-%04d.iwd", i) > 0);
        const std::string full_path = many_iwd_dir + "/" + name;
        const int many_fd = open(full_path.c_str(), O_WRONLY | O_CREAT | O_EXCL, 0600);
        assert(many_fd >= 0);
        close(many_fd);
    }
    std::vector<std::string> expected_iwd_names;
    expected_iwd_names.reserve(1024);
    DIR *expected_stream = opendir(many_iwd_dir.c_str());
    assert(expected_stream);
    while (dirent *entry = readdir(expected_stream)) {
        if (entry->d_name[0] == '.') continue;
        const std::string name(entry->d_name);
        if (name.size() < 4 || name.substr(name.size() - 4) != ".iwd") continue;
        if (expected_iwd_names.size() < 1024) expected_iwd_names.push_back(name);
    }
    assert(closedir(expected_stream) == 0);
    assert(expected_iwd_names.size() == 1024);
    std::vector<char> many_iwd_names(1024 * 32);
    std::size_t many_iwd_count = 0;
    const int many_iwd_bytes = z2026_platform_list_iwd_files(
        "many-iwd", many_iwd_names.data(), many_iwd_names.size(), &many_iwd_count);
    assert(many_iwd_bytes > 0 && many_iwd_count == kManyIwdCount);
    std::size_t many_offset = 0;
    int returned_iwd_count = 0;
    while (many_offset < static_cast<std::size_t>(many_iwd_bytes)) {
        const char *name = many_iwd_names.data() + many_offset;
        const std::size_t remaining =
            static_cast<std::size_t>(many_iwd_bytes) - many_offset;
        const void *end_name = std::memchr(name, '\0', remaining);
        assert(end_name);
        const std::size_t name_length =
            static_cast<const char *>(end_name) - name;
        assert(returned_iwd_count < static_cast<int>(expected_iwd_names.size()));
        const std::string &expected_name = expected_iwd_names[returned_iwd_count];
        assert(name_length == expected_name.size());
        assert(std::memcmp(name, expected_name.data(), name_length) == 0);
        many_offset += name_length + 1;
        ++returned_iwd_count;
    }
    assert(many_offset == static_cast<std::size_t>(many_iwd_bytes));
    assert(returned_iwd_count == 1024);
    char undersized_iwd_output[1]{};
    std::size_t undersized_iwd_count = 99;
    assert(z2026_platform_list_iwd_files(
        "many-iwd", undersized_iwd_output, sizeof(undersized_iwd_output),
        &undersized_iwd_count) == -1);
    assert(undersized_iwd_count == 0);
    for (int i = 0; i < kManyIwdCount; ++i) {
        char name[40]{};
        assert(std::snprintf(name, sizeof(name), "archive-%04d.iwd", i) > 0);
        assert(unlink((many_iwd_dir + "/" + name).c_str()) == 0);
    }
    assert(rmdir(many_iwd_dir.c_str()) == 0);

    char iwd_names[512]{};
    std::size_t iwd_count = 0;
    const int iwd_name_bytes = z2026_platform_list_iwd_files(
        "", iwd_names, sizeof(iwd_names), &iwd_count);
    assert(iwd_name_bytes == static_cast<int>(sizeof("generated.iwd")));
    assert(iwd_count == 1 && std::strcmp(iwd_names, "generated.iwd") == 0);
    std::size_t absolute_iwd_count = 0;
    const int absolute_iwd_name_bytes = z2026_platform_list_iwd_files(
        root, iwd_names, sizeof(iwd_names), &absolute_iwd_count);
    assert(absolute_iwd_name_bytes == iwd_name_bytes);
    assert(absolute_iwd_count == 1 && std::strcmp(iwd_names, "generated.iwd") == 0);
    std::size_t repeated_iwd_count = 0;
    assert(z2026_platform_list_iwd_files("", iwd_names, sizeof(iwd_names),
                                         &repeated_iwd_count) == iwd_name_bytes);
    assert(repeated_iwd_count == 1 && std::strcmp(iwd_names, "generated.iwd") == 0);
    std::size_t overflow_count = 99;
    assert(z2026_platform_list_iwd_files("", iwd_names, 2, &overflow_count) == -1);
    assert(overflow_count == 0);
    assert(z2026_platform_list_iwd_files("../", iwd_names, sizeof(iwd_names),
                                         &overflow_count) == -1);
    assert(z2026_platform_unlink_file("generated.iwd") == 0);
    assert(z2026_platform_open_read_fd("generated.iwd") == -1);
    // Actual IW3 game data is nested (e.g. main/zone), not flat.
    // Exercise an app-owned nested file while rejecting directory symlinks.
    const std::string main_dir = std::string(root) + "/main";
    assert(mkdir(main_dir.c_str(), 0700) == 0);
    assert(z2026_platform_directory_has_contents("main") == 0);
    assert(z2026_platform_directory_has_contents(main_dir.c_str()) == 0);
    const std::string nested = main_dir + "/native-test.iwd";
    const int nested_fd = open(nested.c_str(), O_WRONLY | O_CREAT | O_EXCL, 0600);
    assert(nested_fd >= 0);
    assert(write(nested_fd, "IWD", 3) == 3);
    close(nested_fd);
    assert(z2026_platform_directory_has_contents("main") == 1);
    assert(z2026_platform_directory_has_contents(main_dir.c_str()) == 1);
    assert(z2026_platform_read_file("main/native-test.iwd", buffer, sizeof(buffer)) == 3);
    assert(std::memcmp(buffer, "IWD", 3) == 0);
    int nested_engine_fd = z2026_platform_open_engine_path_fd(nested.c_str());
    assert(nested_engine_fd >= 0);
    unsigned char nested_bytes[3]{};
    assert(read(nested_engine_fd, nested_bytes, sizeof(nested_bytes)) == 3);
    assert(std::memcmp(nested_bytes, "IWD", 3) == 0);
    close(nested_engine_fd);
    std::size_t nested_iwd_count = 0;
    const int nested_iwd_bytes = z2026_platform_list_iwd_files(
        "main", iwd_names, sizeof(iwd_names), &nested_iwd_count);
    assert(nested_iwd_bytes == static_cast<int>(sizeof("native-test.iwd")));
    assert(nested_iwd_count == 1 && std::strcmp(iwd_names, "native-test.iwd") == 0);
    const std::string windows_nested = std::string(root) + "\\main\\native-test.iwd";
    int windows_nested_fd = z2026_platform_open_engine_path_fd(windows_nested.c_str());
    assert(windows_nested_fd >= 0);
    close(windows_nested_fd);
    std::size_t windows_list_count = 0;
    assert(z2026_platform_list_iwd_files(
        (std::string(root) + "\\main").c_str(), iwd_names, sizeof(iwd_names),
        &windows_list_count) == nested_iwd_bytes);
    assert(windows_list_count == 1 && std::strcmp(iwd_names, "native-test.iwd") == 0);
    assert(z2026_platform_read_file("main/../sample.txt", buffer, sizeof(buffer)) == -1);
    const std::string linked_dir = std::string(root) + "/linked-main";
    assert(symlink(main_dir.c_str(), linked_dir.c_str()) == 0);
    assert(z2026_platform_directory_has_contents("linked-main") == -1);
    assert(z2026_platform_read_file("linked-main/native-test.iwd", buffer, sizeof(buffer)) == -1);
    std::size_t linked_count = 99;
    assert(z2026_platform_list_iwd_files("linked-main", iwd_names,
                                         sizeof(iwd_names), &linked_count) == -1);
    assert(linked_count == 0);
    assert(unlink(linked_dir.c_str()) == 0);
    assert(unlink(nested.c_str()) == 0);
    assert(z2026_platform_directory_has_contents("main") == 0);
    assert(rmdir(main_dir.c_str()) == 0);
    assert(z2026_platform_directory_has_contents("main") == -1);

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
    assert(z2026_platform_touch_event(32, .5f, .5f, 1) == -1);
    // Finite coordinates may legitimately leave the view while Android
    // still owns the pointer. Clamp them; do not drop the event.
    assert(z2026_platform_touch_event(0, 1.01f, .5f, 1) == 0);
    assert(z2026_platform_touch_snapshot(0, &x, &y) == 1);
    assert(std::fabs(x - 1.0f) < .001f && std::fabs(y - .5f) < .001f);
    assert(z2026_platform_touch_event(0, 1.25f, .5f, 0) == 0);
    assert(z2026_platform_touch_snapshot(0, &x, &y) == 0);
    assert(z2026_platform_touch_event(0, NAN, .5f, 1) == -1);

    // Releasing an attack pointer outside the screen must not leave ATTACK
    // stuck in subsequent original-layout usercmd snapshots.
    z2026_platform_touch_reset();
    assert(z2026_platform_touch_event(6, .90f, .85f, 1) == 0);
    assert(z2026_platform_touch_event(6, 1.25f, .85f, 1) == 0);
    assert(z2026_platform_touch_snapshot(6, &x, &y) == 1);
    assert(std::fabs(x - 1.0f) < .001f && std::fabs(y - .85f) < .001f);
    assert(z2026_platform_touch_event(6, 1.25f, .85f, 0) == 0);
    assert(z2026_platform_touch_snapshot(6, &x, &y) == 0);
    int off_view_release_cmd[10]{};
    assert(z2026_platform_usercmd_snapshot(1202, off_view_release_cmd, 10) == 0);
    assert((off_view_release_cmd[1] & BUTTON_ATTACK) == 0);

    // MotionEvent pointer IDs are not guaranteed to be 0..9. ID 31 must map
    // to an available native slot and remain independent from pointer ID 4.
    z2026_platform_touch_reset();
    x = y = 4.0f;
    assert(z2026_platform_touch_snapshot(31, &x, &y) == 0);
    assert(x == 0.0f && y == 0.0f);
    assert(z2026_platform_touch_event(31, .90f, .85f, 1) == 0); // attack
    assert(z2026_platform_touch_event(4, .08f, .88f, 1) == 0); // sprint
    assert(z2026_platform_touch_snapshot(31, &x, &y) == 1);
    assert(std::fabs(x - .90f) < .001f && std::fabs(y - .85f) < .001f);
    assert(z2026_platform_touch_snapshot(4, &x, &y) == 1);
    int sparse_pointer_cmd[10]{};
    assert(z2026_platform_usercmd_snapshot(1200, sparse_pointer_cmd, 10) == 0);
    assert((sparse_pointer_cmd[1] & BUTTON_ATTACK) != 0);
    assert((sparse_pointer_cmd[1] & BUTTON_SPRINT) != 0);
    assert(z2026_platform_touch_event(31, .90f, .85f, 0) == 0);
    assert(z2026_platform_touch_snapshot(31, &x, &y) == 0);
    assert(z2026_platform_touch_snapshot(4, &x, &y) == 1);
    int sparse_pointer_release_cmd[10]{};
    assert(z2026_platform_usercmd_snapshot(1201, sparse_pointer_release_cmd, 10) == 0);
    assert((sparse_pointer_release_cmd[1] & BUTTON_ATTACK) == 0);
    assert((sparse_pointer_release_cmd[1] & BUTTON_SPRINT) != 0);
    assert(z2026_platform_touch_event(4, .08f, .88f, 0) == 0);
    z2026_platform_touch_reset();

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

    // Sprint and slide are independent touch roles. Slide must reach the
    // original usercmd as the sprint+crouch chord and may coexist with jump.
    z2026_platform_touch_reset();
    assert(z2026_platform_touch_event(0, .08f, .88f, 1) == 0); // sprint
    assert(z2026_platform_touch_event(1, .27f, .88f, 1) == 0); // slide
    assert(z2026_platform_touch_event(2, .70f, .65f, 1) == 0); // jump
    int sprint_slide_fields[10]{};
    assert(z2026_platform_usercmd_snapshot(5000, sprint_slide_fields, 10) == 0);
    assert((sprint_slide_fields[1] & BUTTON_SPRINT) != 0);
    assert((sprint_slide_fields[1] & BUTTON_CROUCH) != 0);
    assert((sprint_slide_fields[1] & BUTTON_JUMP) != 0);
    usercmd_s sprint_slide_command{};
    float sprint_slide_angles[3] = {};
    z2026_platform_apply_touch_to_usercmd(&sprint_slide_command, sprint_slide_angles);
    assert((sprint_slide_command.buttons & BUTTON_SPRINT) != 0);
    assert((sprint_slide_command.buttons & BUTTON_CROUCH) != 0);
    assert((sprint_slide_command.buttons & BUTTON_JUMP) != 0);
    assert(z2026_platform_touch_event(1, .27f, .88f, 0) == 0);
    int sprint_only_fields[10]{};
    assert(z2026_platform_usercmd_snapshot(5001, sprint_only_fields, 10) == 0);
    assert((sprint_only_fields[1] & BUTTON_SPRINT) != 0);
    assert((sprint_only_fields[1] & BUTTON_CROUCH) == 0);
    assert((sprint_only_fields[1] & BUTTON_JUMP) != 0);
    usercmd_s sprint_only_command{};
    z2026_platform_apply_touch_to_usercmd(&sprint_only_command, sprint_slide_angles);
    assert((sprint_only_command.buttons & BUTTON_SPRINT) != 0);
    assert((sprint_only_command.buttons & BUTTON_CROUCH) == 0);
    assert(z2026_platform_touch_event(0, .08f, .88f, 0) == 0);
    z2026_platform_touch_reset();

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
