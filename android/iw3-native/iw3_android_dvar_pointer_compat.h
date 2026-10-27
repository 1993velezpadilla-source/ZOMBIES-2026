#pragma once

// Narrow include surface for compiling authentic KisakCOD dvar functions in
// host/Android ABI audits. This is not a replacement dvar implementation.
#include <universal/q_shared.h>
#include <qcommon/qcommon.h>
#include <universal/com_memory.h>
#include <cstdio>
#include <cstdint>

#ifndef __cdecl
#define __cdecl
#endif

#ifndef _snprintf
#define _snprintf std::snprintf
#endif

// The full dvar.cpp normally receives this declaration through the Windows
// platform header. Keep the original assertion call signature available to
// the isolated source slice without importing Windows.h.
void __cdecl MyAssertHandler(
    const char *filename, int line, int type, const char *format, ...);
