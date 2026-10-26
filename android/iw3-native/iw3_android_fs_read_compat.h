#pragma once
// ABI boundary for verbatim KisakCOD FS_FileForHandle and FS_Read bodies.
// The original FS_CheckFileSystemStarted body is supplied by the original
// lookup module. com_files.cpp keeps fsh[65] file-local static; the Android
// diagnostic defines a separate
// native-width table solely for the IWD ZIP-branch probe; the original full
// open/close lifecycle is still not integrated and this is not a game runtime.
#include <cstddef>
#include <cstdio>
#include "iw3_android_iwd_lookup_compat.h"
#include "iw3_android_unzip_compat.h"

static_assert(sizeof(void *) == 8, "IW3 FS_Read audit requires a 64-bit ABI");
static_assert(sizeof(fileHandleData_t) == 304,
              "Unexpected native 64-bit fileHandleData_t layout");
static_assert(offsetof(fileHandleData_t, zipFile) == 32,
              "Unexpected native 64-bit fileHandleData_t::zipFile offset");
static_assert(offsetof(fileHandleData_t, name) == 44,
              "Unexpected native 64-bit fileHandleData_t::name offset");

extern fileHandleData_t fsh[65];
FILE *__cdecl FS_FileForHandle(int f);
