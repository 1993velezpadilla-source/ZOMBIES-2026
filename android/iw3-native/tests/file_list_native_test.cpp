// Execute Android directory enumeration with the original IW3 allocator/free
// pair. No test implementation of Sys_ListFiles, HunkUser or FS_FreeFileList.
#include "iw3_android_iwd_directory_compat.h"
#include <universal/com_memory.h>
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <string>
#include <unistd.h>

void Com_Error(errorParm_t code, const char *format, ...)
{
    std::fprintf(stderr, "Unexpected engine error %d: ", int(code));
    va_list args;
    va_start(args, format);
    std::vfprintf(stderr, format, args);
    va_end(args);
    std::abort();
}

static void touch(const std::filesystem::path &path)
{
    FILE *file = std::fopen(path.c_str(), "wb");
    assert(file);
    assert(std::fclose(file) == 0);
}

static void checkAndFree(char **list, int count)
{
    assert(list && count > 0);
    const int stored = count > 1024 ? 1024 : count;
    assert(list[stored] == nullptr);
    auto *owner = reinterpret_cast<HunkUser *>(list[-1]);
    assert(owner && owner->fixed);
    assert(reinterpret_cast<uintptr_t>(list) >= reinterpret_cast<uintptr_t>(owner->buf));
    assert(reinterpret_cast<uintptr_t>(list) % alignof(char *) == 0);
    for (int i = 0; i < stored; ++i) {
        assert(list[i] && *list[i]);
        assert(reinterpret_cast<uintptr_t>(list[i]) < owner->pos);
    }
    // Original destructor reads list[-1] then releases the HunkUser reservation.
    FS_FreeFileList(const_cast<const char **>(list));
}

int main()
{
    char pattern[] = "/tmp/iw3-file-list-XXXXXX";
    char *root = mkdtemp(pattern);
    assert(root);
    std::filesystem::path base(root);
    std::filesystem::create_directory(base / "assets");
    std::filesystem::create_directory(base / "assets" / "subdir");
    touch(base / "assets" / "first.cfg");
    touch(base / "assets" / "SECOND.CFG");
    touch(base / "assets" / "language.str");
    assert(symlink("first.cfg", (base / "assets" / "linked.cfg").c_str()) == 0);
    assert(z2026_platform_set_data_root(root) == 0);
    int count = -1;
    for (int repeat = 0; repeat < 32; ++repeat) {
        char **list = Sys_ListFiles("assets", "cfg", nullptr, &count, 0);
        assert(count == 2);
        checkAndFree(list, count);
    }
    char **list = Sys_ListFiles("assets", ".cfg", "first*", &count, 0);
    assert(count == 1 && std::strcmp(list[0], "first.cfg") == 0);
    checkAndFree(list, count);
    list = Sys_ListFiles("assets", "/", nullptr, &count, 0);
    assert(count == 1 && std::strcmp(list[0], "subdir") == 0);
    checkAndFree(list, count);
    assert(Sys_ListFiles("assets", "missing", nullptr, &count, 0) == nullptr);
    assert(count == 0);
    assert(Sys_ListFiles("../", "cfg", nullptr, &count, 0) == nullptr);
    assert(count == 0);
    FS_FreeFileList(nullptr);
    std::filesystem::create_directory(base / "main");
    for (int i = 0; i < 1026; ++i)
        touch(base / "main" / ("iw_" + std::to_string(i) + ".iwd"));
    list = Sys_ListFiles("main", "iwd", nullptr, &count, 0);
    assert(count == 1025); // Original scanner's over-limit warning signal.
    checkAndFree(list, count);
    std::filesystem::remove_all(base);
    std::puts("IW3_ORIGINAL_FILE_LIST_OWNERSHIP_RUNTIME_PASS");
}
