#pragma once
// Portable include adapter for the original KisakCOD ZIP32/IWD reader.
// The parser body is staged from third_party/KisakCOD/src/qcommon/unzip.cpp.
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#ifndef __cdecl
#define __cdecl
#endif
#include <zlib/zlib.h>
#include "com_fileaccess.h"

// The original engine Com_Memcpy implementation is linked from com_shared.cpp.
void __cdecl Com_Memcpy(void *dest_p, const void *src_p, const size_t count);
#ifndef iassert
#define iassert(expr) assert(expr)
#endif
