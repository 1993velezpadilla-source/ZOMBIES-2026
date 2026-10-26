#pragma once
// Platform boundary for the verbatim KisakCOD IWD directory-scanning function.
#include "iw3_android_iwd_mount_compat.h"
#include "iw3_android_platform.h"
#include <cstdint>
#include <cstdio>
#include <stringed/stringed_hooks.h>
#include <qcommon/qcommon.h>

#ifndef __cdecl
#define __cdecl
#endif

char **Sys_ListFiles(const char *directory, const char *extension,
                     const char *filter, int *numfiles, int wantsubs);
void __cdecl FS_FreeFileList(const char **list);
void __cdecl FS_BuildOSPath(const char *base, const char *game,
                            const char *qpath, char *ospath);
char *__cdecl IwdFileLanguage(const char *pszIwdFileName);
int __cdecl FS_PathCmp(const char *s1, const char *s2);
int __cdecl iwdsort(const char **a, char **b);
void __cdecl FS_AddIwdFilesForGameDirectory(char *path, char *pszGameFolder);
