#include "iw3_android_fs_read_compat.h"

#include <cstdlib>
#include <climits>
#include <cstdio>

// fsh is defined once by the shared original-engine source
// com_files_handle_table.cpp. This file supplies only narrow platform services.

namespace {
dvar_s g_z2026_fs_debug{};
dvar_s g_z2026_fs_restrict{};
dvar_s g_z2026_fs_copyfiles{};
dvar_s g_z2026_fs_cdpath{};
dvar_s g_z2026_fs_basepath{};
}

const dvar_s *fs_debug = &g_z2026_fs_debug;
const dvar_s *fs_restrict = &g_z2026_fs_restrict;
const dvar_s *fs_copyfiles = &g_z2026_fs_copyfiles;
const dvar_s *fs_cdpath = &g_z2026_fs_cdpath;
const dvar_s *fs_basepath = &g_z2026_fs_basepath;
int fs_numServerIwds = 0;
int fs_serverIwds[1024]{};
int fs_fakeChkSum = 0;

// The fixture runs only the main-thread file slot. These service adapters fail
// closed for unsupported database/fastfile scheduling and copy-file behavior.
bool z2026_iw3_is_fastfile_load() { return false; }
bool z2026_iw3_is_database_thread() { return false; }
char *z2026_iw3_safe_translate(char *text) {
    return text ? text : const_cast<char *>("");
}
void z2026_iw3_fs_copy_file(char *, char *) {
    std::abort();
}
uint32_t z2026_iw3_interlocked_compare_exchange(
        volatile uint32_t *destination, uint32_t exchange, uint32_t comparand) {
    if (!destination) return 0;
    uint32_t expected = comparand;
    __atomic_compare_exchange_n(destination, &expected, exchange, false,
                                __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST);
    return expected;
}

int z2026_iw3_fs_file_get_size(FILE *stream) {
    if (!stream) return -1;
    const long original = std::ftell(stream);
    if (original < 0 || std::fseek(stream, 0, SEEK_END) != 0) return -1;
    const long end = std::ftell(stream);
    const int restore_rc = std::fseek(stream, original, SEEK_SET);
    if (end < 0 || end > INT_MAX || restore_rc != 0) return -1;
    return static_cast<int>(end);
}

extern "C" void z2026_iw3_fs_file_close(FILE *stream) {
    if (stream) std::fclose(stream);
}
