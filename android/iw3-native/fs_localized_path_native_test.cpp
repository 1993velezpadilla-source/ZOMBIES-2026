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
static int g_fatal_errors = 0;
static std::vector<std::string> g_probed_paths;
static std::vector<std::string> g_iwd_game_folders;

static bool g_force_empty_homepath = false;
static int g_registered_dvars = 0;
static int g_cdkey_reads = 0;
static int g_add_commands_calls = 0;
static int g_path_command_calls = 0;
static int g_clear_modified_calls = 0;
static dvar_s g_dvar_slots[16]{};
static const char *g_dvar_names[16]{};
static int g_dvar_slot_count = 0;

const dvar_t *fs_homepath = nullptr;
const dvar_s *fs_debug = nullptr;
const dvar_s *fs_restrict = nullptr;
const dvar_s *fs_ignoreLocalized = nullptr;
const dvar_s *fs_basepath = nullptr;
const dvar_s *fs_copyfiles = nullptr;
const dvar_s *fs_cdpath = nullptr;
const dvar_s *fs_gameDirVar = nullptr;
const dvar_s *fs_basegame = nullptr;
int fs_iwdFileCount = 0;
int fs_checksumFeed = 0;

void __cdecl FS_Startup(char *gameName);

static dvar_s *dvar_slot(const char *name) {
    for (int i = 0; i < g_dvar_slot_count; ++i) {
        if (std::strcmp(g_dvar_names[i], name) == 0) return &g_dvar_slots[i];
    }
    assert(g_dvar_slot_count < 16);
    const int index = g_dvar_slot_count++;
    g_dvar_names[index] = name;
    g_dvar_slots[index].name = name;
    ++g_registered_dvars;
    return &g_dvar_slots[index];
}

const dvar_s *__cdecl Dvar_RegisterInt(const char *name, int value, DvarLimits, uint16_t, const char *) {
    dvar_s *d = dvar_slot(name);
    d->current.integer = value;
    d->reset.integer = value;
    return d;
}

const dvar_s *__cdecl Dvar_RegisterBool(const char *name, bool value, uint16_t, const char *) {
    dvar_s *d = dvar_slot(name);
    d->current.enabled = value;
    d->reset.enabled = value;
    return d;
}

const dvar_s *__cdecl Dvar_RegisterString(const char *name, const char *value, uint16_t, const char *) {
    dvar_s *d = dvar_slot(name);
    const char *initial = value ? value : "";
    if (g_force_empty_homepath && std::strcmp(name, "fs_homepath") == 0) initial = "";
    d->current.string = initial;
    d->reset.string = initial;
    return d;
}

void __cdecl Dvar_SetDomainFunc(dvar_s *dvar, bool (__cdecl *domainFunc)(dvar_s *, DvarValue)) {
    assert(dvar);
    dvar->domainFunc = domainFunc;
}

void __cdecl Dvar_ClearModified(dvar_s *dvar) {
    assert(dvar);
    dvar->modified = false;
    ++g_clear_modified_calls;
}

bool __cdecl FS_GameDirDomainFunc(dvar_s *, DvarValue) { return true; }

char *Sys_Cwd() {
    static char root[] = "/private/iw3";
    return root;
}

char *Sys_DefaultCDPath() {
    static char empty[] = "";
    return empty;
}

void QDECL Com_Printf(int, const char *, ...) {}
void __cdecl Com_ReadCDKey() { ++g_cdkey_reads; }
void FS_AddCommands() { ++g_add_commands_calls; }
void FS_Path_f() { ++g_path_command_calls; }

char *va(const char *format, ...) {
    static thread_local char buffer[256];
    va_list args;
    va_start(args, format);
    std::vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    return buffer;
}

const char *__cdecl SEH_GetLanguageName(uint32_t language) {
    return language == 0 ? "english" : "";
}

void __cdecl FS_AddIwdFilesForGameDirectory(char *path, char *game_folder) {
    assert(path && *path);
    assert(game_folder && *game_folder);
    ++g_iwd_scans;
    g_iwd_game_folders.emplace_back(game_folder);
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

void QDECL Com_Error(errorParm_t code, const char *fmt, ...) {
    assert(code == ERR_FATAL);
    assert(fmt && *fmt);
    ++g_fatal_errors;
}

void MyAssertHandler(const char *, int, int, const char *, ...) {
    std::abort();
}

static void test_original_path_builder() {
    char path[256]{};
    FS_BuildOSPath("/private//iw3/", "main", "english//voice", path);
    assert(std::strcmp(path, "/private/iw3/main/english/voice") == 0);

    // Android must retain the POSIX root through the authentic path builder.
    FS_BuildOSPath("/private\\iw3//", "main", "maps\\mp//test.d3dbsp", path);
    assert(std::strcmp(path, "/private/iw3/main/maps/mp/test.d3dbsp") == 0);
    assert(path[0] == '/');

    std::string oversized(300, 'x');
    std::strcpy(path, "stale");
    FS_BuildOSPathForThread(oversized.c_str(), "main", "", path, FS_THREAD_BACKEND);
    assert(path[0] == '\0');

    g_fatal_errors = 0;
    std::strcpy(path, "stale");
    FS_BuildOSPathForThread(oversized.c_str(), "main", "", path, FS_THREAD_MAIN);
    assert(g_fatal_errors == 1);
    assert(path[0] == '\0');
}

int main() {
    test_original_path_builder();
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

    // Execute the authentic FS_RegisterDvars and FS_Startup bodies with only
    // the platform/Dvar registry services supplied by this host harness.
    // An explicit empty fs_homepath must not become a relative search root.
    g_directory_probes = 0;
    g_iwd_scans = 0;
    g_probed_paths.clear();
    g_iwd_game_folders.clear();
    g_force_empty_homepath = true;
    char main_game[] = "main";
    FS_Startup(main_game);

    assert(fs_basepath && std::strcmp(fs_basepath->current.string, "/private/iw3") == 0);
    assert(fs_homepath && fs_homepath->current.string && fs_homepath->current.string[0] == '\0');
    assert(g_registered_dvars == 9);
    assert(g_cdkey_reads == 1);
    assert(g_add_commands_calls == 1);
    assert(g_path_command_calls == 1);
    assert(g_clear_modified_calls == 1);
    assert(g_directory_probes == 7);
    assert(g_probed_paths.size() == 7);
    assert(g_iwd_scans == 14);
    assert(g_iwd_game_folders.size() == 14);

    int startup_paths = 0;
    bool saw_main = false;
    bool saw_main_shared = false;
    for (searchpath_s *entry = fs_searchpaths; entry; entry = entry->next) {
        ++startup_paths;
        assert(entry->dir);
        assert(entry->dir->path[0] != '\0');
        assert(std::strcmp(entry->dir->path, "/private/iw3") == 0);
        if (std::strcmp(entry->dir->gamedir, "main") == 0) saw_main = true;
        if (std::strcmp(entry->dir->gamedir, "main_shared") == 0) saw_main_shared = true;
    }
    assert(startup_paths == 14);
    assert(saw_main && saw_main_shared);
    std::puts("IW3_ORIGINAL_FS_STARTUP_EMPTY_HOMEPATH_PASS");

    while (fs_searchpaths) {
        searchpath_s *next = fs_searchpaths->next;
        std::free(fs_searchpaths->dir);
        std::free(fs_searchpaths);
        fs_searchpaths = next;
    }
    return 0;
}
