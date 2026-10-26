#include "com_files.h"

#include <cstddef>

// Keep the original engine's handle table ABI explicit on both supported
// layouts: Win32 remains 284 bytes; native 64-bit builds use 304 bytes.
static_assert(sizeof(fileHandleData_t) == (sizeof(void *) == 8 ? 304u : 284u),
              "Unexpected KisakCOD fileHandleData_t size");
static_assert(offsetof(fileHandleData_t, zipFile) ==
                  (sizeof(void *) == 8 ? 32u : 20u),
              "Unexpected KisakCOD fileHandleData_t::zipFile offset");
static_assert(offsetof(fileHandleData_t, name) ==
                  (sizeof(void *) == 8 ? 44u : 28u),
              "Unexpected KisakCOD fileHandleData_t::name offset");

// Shared by the authentic com_files.cpp implementation and the Android port's
// exact extracted FS_HandleForFile / open / read / close function bodies.
fileHandleData_t fsh[65] = {};
