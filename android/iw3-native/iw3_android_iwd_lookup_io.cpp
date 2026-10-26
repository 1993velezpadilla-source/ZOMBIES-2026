#include "iw3_android_iwd_lookup_compat.h"

#include <cstdarg>
#include <cstdio>
#include <cstdlib>

// The authentic lookup path only consults this when a localized searchpath is
// selected. This diagnostic registers nonlocalized English fixtures only.
int __cdecl SEH_GetCurrentLanguage() {
    return 0;
}

// Error-only adapters for original diagnostics/path-overflow handling. They
// fail closed; they do not provide gameplay or suppress an engine fatal error.
char *QDECL va(const char *format, ...) {
    static thread_local char buffer[2048];
    if (!format) return const_cast<char *>("");
    va_list args;
    va_start(args, format);
    const int written = std::vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    if (written < 0) buffer[0] = '\0';
    buffer[sizeof(buffer) - 1] = '\0';
    return buffer;
}

void QDECL Com_Error(errorParm_t code, const char *format, ...) {
    std::fprintf(stderr, "IW3 original file lookup fatal error (%d): ",
                 static_cast<int>(code));
    if (format) {
        va_list args;
        va_start(args, format);
        std::vfprintf(stderr, format, args);
        va_end(args);
    }
    std::fputc('\n', stderr);
    std::abort();
}
