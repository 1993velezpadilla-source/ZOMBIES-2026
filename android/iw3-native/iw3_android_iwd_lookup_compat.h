#pragma once
// Test-only adapter for the verbatim lookup prefix of original KisakCOD
// FS_FOpenFileReadForThread. It does not allocate a file handle or implement FS_Read.
#include "iw3_android_iwd_directory_compat.h"
#include <cstdio>

#ifndef __cdecl
#define __cdecl
#endif

char __cdecl FS_SanitizeFilename(const char *filename, char *sanitizedName, int sanitizedNameSize);
bool __cdecl FS_IsBackupSubStr(const char *filenameSubStr);
BOOL __cdecl FS_UseSearchPath(const searchpath_s *pSearch);
void __cdecl FS_CheckFileSystemStarted();
void __cdecl FS_BuildOSPathForThread(const char *base, const char *game,
                                     const char *qpath, char *ospath, FsThread thread);
int __cdecl FS_FilenameCompare(const char *s1, const char *s2);
extern const dvar_s *fs_ignoreLocalized;

extern "C" int z2026_iw3_original_searchpath_lookup(
    const char *filename, int *file, FsThread thread);
