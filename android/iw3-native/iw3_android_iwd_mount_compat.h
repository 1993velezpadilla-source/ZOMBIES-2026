#pragma once
// Include adapter for a compile-only module containing the verbatim original
// KisakCOD FS_LoadZipFile function. Engine data structures come from the
// original com_files.h; this header declares only service/global dependencies.
#include <climits>
#include <cstdint>
#include "com_files.h"
#include "unzip.h"

#ifndef __cdecl
#define __cdecl
#endif

void *Z_Malloc(int32_t size, const char *name, int32_t type);
void Z_Free(void *ptr, int32_t type);
int __cdecl Com_BlockChecksumKey32(const uint8_t *data, uint32_t length, uint32_t initialCrc);
iwd_t *__cdecl FS_LoadZipFile(char *zipfile, char *basename);
int __cdecl FS_HashFileName(const char *fname, int hashSize);

extern int fs_iwdFileCount;
extern int fs_checksumFeed;
