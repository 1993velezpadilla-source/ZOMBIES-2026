#pragma once

#include <universal/q_shared.h>

// These are the original engine-facing system service signatures that
// win_local.h normally exposes. Android provides POSIX implementations at the
// platform boundary; declarations here let the authentic filesystem TU compile
// without importing DirectInput/Win32 headers.
void __cdecl Sys_Mkdir(const char *path);
int __cdecl Sys_CountFileList(char **list);
char **__cdecl Sys_ListFiles(
    const char *directory,
    const char *extension,
    const char *filter,
    int *numfiles,
    int wantsubs);
char *__cdecl Sys_Cwd();
const char *__cdecl Sys_DefaultCDPath();
int __cdecl Sys_DirectoryHasContents(const char *directory);

// Shared with the original-source FS_Read extraction; preserves the Windows
// InterlockedCompareExchange return-old-value contract using native atomics.
uint32_t z2026_iw3_interlocked_compare_exchange(
    volatile uint32_t *destination, uint32_t exchange, uint32_t comparand);
