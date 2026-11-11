#pragma once
// Portable OS services used by unmodified KisakCOD surface-name lookup.
// Original surfaceflags.h and all original 60 material entries remain real
// engine data. This adapter changes *only* Win32 runtime dependencies.
#include "iw3_android_math_compat.h"
#include <cstdlib>
#include <strings.h>

// Win32 MSVC originally uses _stricmp via IW3 I_stricmp. Android bionic
// strcasecmp has the equivalent ASCII case-insensitive lookup semantics.
static inline int I_stricmp(const char *a, const char *b) {
    return strcasecmp(a, b);
}

// A genuine fail-closed native platform assertion; never silence bad
// indices or fabricate surface types.
[[noreturn]] static inline void MyAssertHandler(
    const char * /*filename*/, int /*line*/, int /*type*/,
    const char * /*fmt*/, ...) {
    std::abort();
}
