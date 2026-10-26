#pragma once
// Narrow declarations for compiling the verbatim original
// FS_ListFilteredFilesInLocation body as an ABI/dependency audit archive.
// This header does not implement or replace any engine service.
#ifndef __cdecl
#define __cdecl
#endif
#include "com_files.h"

struct HunkUser;
HunkUser* __cdecl Hunk_UserCreate(int maxSize, const char* name,
                                  bool fixed, bool tempMem, int type);
void* Hunk_UserAlloc(HunkUser* user, uint32_t size, int alignment);
void __cdecl Hunk_UserDestroy(HunkUser* user);

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
