#pragma once
// ABI audit boundary for the verbatim original KisakCOD FS_Read body.
// This header is for a separate compile-only archive, not the JNI runtime.
// The original com_files.cpp owns fsh as a file-local static array, so the
// declaration below intentionally remains unresolved until that owning TU (or
// a genuine engine accessor) is ported. Do not link this archive into the game.
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
