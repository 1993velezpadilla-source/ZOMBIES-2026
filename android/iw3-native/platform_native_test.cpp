#include "iw3_android_platform.h"

#include <cassert>
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
    const std::string symlink_path = std::string(root) + "/outside";
    assert(symlink("/etc/passwd", symlink_path.c_str()) == 0);
    assert(z2026_platform_read_file("outside", buffer, sizeof(buffer)) == -1);

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

    unlink(symlink_path.c_str());
    unlink(path.c_str());
    rmdir(root);
    std::puts("IW3_ANDROID_PLATFORM_HOST_TEST_GREEN (time, sandbox IO, multi-touch)");
}
