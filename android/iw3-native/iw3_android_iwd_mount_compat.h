#pragma once
// ABI adapter for the verbatim original KisakCOD FS_LoadZipFile function.
// It is compiled into an audit archive and exercised by the JNI IWD-index smoke;
// neither use is a complete game runtime. Engine structures remain original.
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
extern searchpath_s *fs_searchpaths;
void __cdecl FS_AddSearchPath(searchpath_s *search);
