#include "iw3_android_fs_startup_compat.h"

#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <strings.h>
#include <vector>

searchpath_s *fs_searchpaths = nullptr;
char fs_gamedir[256] = {};

static int g_directory_probes = 0;
static int g_iwd_scans = 0;
static std::vector<std::string> g_probed_paths;
static std::vector<std::string> g_iwd_game_folders;

const char *__cdecl SEH_GetLanguageName(uint32_t language) {
    return language == 0 ? "english" : "";
}

void __cdecl FS_AddIwdFilesForGameDirectory(char *path, char *game_folder) {
    assert(path && *path);
    assert(game_folder && *game_folder);
    ++g_iwd_scans;
    g_iwd_game_folders.emplace_back(game_folder);
}

void __cdecl FS_BuildOSPath(const char *base, const char *game,
                            const char *qpath, char *ospath) {
    assert(ospath);
    const int written = std::snprintf(
        ospath, 260, "%s/%s/%s", base ? base : "", game ? game : "",
        qpath ? qpath : "");
    assert(written >= 0 && written < 260);
}

int __cdecl Sys_DirectoryHasContents(const char *directory) {
    assert(directory && *directory);
    ++g_directory_probes;
    g_probed_paths.emplace_back(directory);
    return 1;
}

int Com_sprintf(char *dest, uint32_t size, const char *format, ...) {
    if (!dest || size == 0 || !format) return -1;
    va_list args;
    va_start(args, format);
    const int result = std::vsnprintf(dest, static_cast<std::size_t>(size),
                                      format, args);
    va_end(args);
    dest[size - 1] = '\0';
    return result;
}

void I_strncpyz(char *dest, const char *src, int size) {
    if (!dest || size <= 0) return;
    if (!src) src = "";
    std::strncpy(dest, src, static_cast<std::size_t>(size - 1));
    dest[size - 1] = '\0';
}

int I_stricmp(const char *left, const char *right) {
    return strcasecmp(left ? left : "", right ? right : "");
}

void *Z_Malloc(int size, const char *, int) {
    if (size <= 0) return nullptr;
    return std::calloc(1, static_cast<std::size_t>(size));
}

void Com_PrintWarning(int, const char *, ...) {}

void MyAssertHandler(const char *, int, int, const char *, ...) {
    std::abort();
}

int main() {
    fs_searchpaths = nullptr;
    std::memset(fs_gamedir, 0, sizeof(fs_gamedir));
    g_directory_probes = 0;
    g_iwd_scans = 0;
    g_probed_paths.clear();
    g_iwd_game_folders.clear();

    // Execute the original FS_AddLocalizedGameDirectory and
    // FS_AddGameDirectory bodies. The narrow stubs only model their platform
    // services; path registration and language filtering remain engine code.
    char base[] = "/private/iw3";
    char game[] = "main";
    FS_AddLocalizedGameDirectory(base, game);

    // Only English has a language name in the Android adapter. Unsupported
    // language IDs must not alias the parent "main" directory as localized.
    assert(g_directory_probes == 1);
    assert(g_probed_paths.size() == 1);
    assert(g_probed_paths[0] == "/private/iw3/main/english");
    assert(g_iwd_scans == 2);
    assert(g_iwd_game_folders.size() == 2);

    int path_count = 0;
    int localized_count = 0;
    int nonlocalized_count = 0;
    bool saw_english = false;
    bool saw_plain_main = false;
    for (searchpath_s *entry = fs_searchpaths; entry; entry = entry->next) {
        ++path_count;
        assert(entry->dir);
        if (entry->bLocalized) {
            ++localized_count;
            assert(entry->language == 0);
            assert(std::strcmp(entry->dir->gamedir, "main/english") == 0);
            saw_english = true;
        } else {
            ++nonlocalized_count;
            assert(entry->language == 0);
            assert(std::strcmp(entry->dir->gamedir, "main") == 0);
            saw_plain_main = true;
        }
    }
    assert(path_count == 2);
    assert(localized_count == 1);
    assert(nonlocalized_count == 1);
    assert(saw_english && saw_plain_main);
    assert(std::strcmp(fs_gamedir, "main") == 0);

    while (fs_searchpaths) {
        searchpath_s *next = fs_searchpaths->next;
        std::free(fs_searchpaths->dir);
        std::free(fs_searchpaths);
        fs_searchpaths = next;
    }
    return 0;
}
