#pragma once
// ABI boundary for exact KisakCOD file-handle allocation/open/read/close bodies.
// The original engine-owned fsh[65] is defined in
// src/universal/com_files_handle_table.cpp and shared with com_files.cpp.
// This generated-source slice uses that same table, with narrow Android
// platform services; the full com_files.cpp translation unit is not linked here.
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include "iw3_android_iwd_lookup_compat.h"
#include "iw3_android_unzip_compat.h"

static_assert(sizeof(void *) == 8, "IW3 FS lifecycle requires a 64-bit ABI");
static_assert(sizeof(fileHandleData_t) == 304,
              "Unexpected native 64-bit fileHandleData_t layout");
static_assert(offsetof(fileHandleData_t, zipFile) == 32,
              "Unexpected native 64-bit fileHandleData_t::zipFile offset");
static_assert(offsetof(fileHandleData_t, name) == 44,
              "Unexpected native 64-bit fileHandleData_t::name offset");

extern fileHandleData_t fsh[65];
extern int fs_fakeChkSum;
extern "C" void z2026_iw3_fs_file_close(FILE *stream);
int z2026_iw3_fs_file_get_size(FILE *stream);
bool z2026_iw3_is_fastfile_load();
bool z2026_iw3_is_database_thread();
char *z2026_iw3_safe_translate(char *text);
void z2026_iw3_fs_copy_file(char *from, char *to);
uint32_t z2026_iw3_interlocked_compare_exchange(
    volatile uint32_t *destination, uint32_t exchange, uint32_t comparand);

// Only the FILE* platform boundary is adapted; ZIP handling remains upstream.
#define FS_FileClose z2026_iw3_fs_file_close
FILE *__cdecl FS_FileForHandle(int f);
int __cdecl FS_HandleForFile(FsThread thread);
BOOL __cdecl FS_PureIgnoresExtension(const char *extension);
char __cdecl FS_FilesAreLoadedGlobally(const char *filename);
int __cdecl FS_IwdIsPure(iwd_t *iwd);
