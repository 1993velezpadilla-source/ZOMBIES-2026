#pragma once
// Narrow declarations for compiling the verbatim original filtered-file search
// functions as an ABI/dependency audit archive. No engine service is replaced.
#ifndef __cdecl
#define __cdecl
#endif
#include "com_files.h"

#ifndef BOOL
typedef int BOOL;
#endif

struct HunkUser;
HunkUser* __cdecl Hunk_UserCreate(int maxSize, const char* name,
                                  bool fixed, bool tempMem, int type);
void* Hunk_UserAlloc(HunkUser* user, uint32_t size, int alignment);
void __cdecl Hunk_UserDestroy(HunkUser* user);

void __cdecl FS_CheckFileSystemStarted();
char __cdecl FS_SanitizeFilename(const char* filename, char* sanitizedName, int sanitizedNameSize);
int __cdecl FS_ReturnPath(const char* zname, char* zpath, int* depth);
int __cdecl FS_AddFileToList(HunkUser* user, const char* name, const char** list, int nfiles);
BOOL __cdecl FS_UseSearchPath(const searchpath_s* pSearch);
char** Sys_ListFiles(const char* directory, const char* extension,
                     const char* filter, int* numfiles, int wantsubs);

bool __cdecl FS_CheckLocation(const char* path, int lookInFlags);
const char** __cdecl FS_ListFilteredFiles(
    searchpath_s* searchPath,
    const char* path,
    const char* extension,
    const char* filter,
    FsListBehavior_e behavior,
    int* numfiles);
void __cdecl MyAssertHandler(const char* filename, int line, int type,
                             const char* format, ...);
