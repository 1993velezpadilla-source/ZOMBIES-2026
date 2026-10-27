#include <cassert>
#include <cstddef>
#include <cstring>
#include <string>

#include "iw3_android_platform.h"

int Sys_DirectoryHasContents(const char *directory);

namespace {
const char kRoot[] = "/data/user/0/org.z2026.iw3nativeprobe/files";
std::string g_last_relative;
int g_platform_result = 1;
int g_platform_calls = 0;
}

extern "C" int z2026_platform_copy_data_root(char *destination, std::size_t capacity) {
    const std::size_t length = std::strlen(kRoot);
    if (!destination || capacity <= length) return -1;
    std::memcpy(destination, kRoot, length + 1);
    return static_cast<int>(length);
}

extern "C" int z2026_platform_directory_has_contents(const char *directory) {
    ++g_platform_calls;
    g_last_relative = directory ? directory : "<null>";
    return g_platform_result;
}

int main() {
    assert(Sys_DirectoryHasContents(kRoot) == 1);
    assert(g_last_relative.empty());

    const std::string nested = std::string(kRoot) + "/main";
    assert(Sys_DirectoryHasContents(nested.c_str()) == 1);
    assert(g_last_relative == "main");

    g_platform_result = 0;
    const std::string empty = std::string(kRoot) + "/empty";
    assert(Sys_DirectoryHasContents(empty.c_str()) == 0);
    assert(g_last_relative == "empty");

    g_platform_result = -1;
    assert(Sys_DirectoryHasContents(empty.c_str()) == 0);

    const int calls_before_reject = g_platform_calls;
    const std::string sibling = std::string(kRoot) + "-evil";
    assert(Sys_DirectoryHasContents(sibling.c_str()) == 0);
    assert(Sys_DirectoryHasContents("/etc") == 0);
    assert(Sys_DirectoryHasContents(nullptr) == 0);
    assert(g_platform_calls == calls_before_reject);

    return 0;
}
