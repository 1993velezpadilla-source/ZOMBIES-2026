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

void *Z_Malloc(int size, const char *name, int type);
void Z_Free(void *ptr, int type);
int Com_BlockChecksumKey32(const unsigned char *data, int length, int key);

extern int fs_iwdFileCount;
extern int fs_checksumFeed;
