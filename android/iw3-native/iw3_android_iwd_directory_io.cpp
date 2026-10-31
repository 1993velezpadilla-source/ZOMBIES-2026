#include "iw3_android_iwd_directory_compat.h"

#include <algorithm>
#include <cstdarg>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <limits>
#include <string>
#include <vector>

// FS_BuildOSPath is provided by the original body in the IWD lookup source slice.


// The diagnostic JNI library retains its narrow English-only fallback, but
// the combined startup dependency audit must use the original language registry
// extracted from KisakCOD stringed_hooks.cpp instead of these diagnostic helpers.
#if !defined(IW3_IWD_DIRECTORY_LINK_AUDIT)
// Diagnostic-only fallback; it is not used by the combined original-engine audit.
int __cdecl SEH_GetLanguageIndexForName(const char *name, int *index) {
    if (!name || !index || I_stricmp(name, "english") != 0) return 0;
    *index = 0;
    return 1;
}
const char *__cdecl SEH_GetLanguageName(uint32_t language) {
    return language == 0 ? "english" : "";
}
#endif

#if !defined(IW3_IWD_DIRECTORY_LINK_AUDIT)
// Console output adapter for this isolated native file-system test. It logs
// the original format string without interpreting platform-specific formats.
void __cdecl Com_PrintWarning(int, const char *format, ...) {
    if (format) { std::fputs("IW3 file warning: ", stderr); std::fputs(format, stderr); }
}
#endif
#if !defined(IW3_IWD_DIRECTORY_LINK_AUDIT)
// The diagnostic shared library has no full console subsystem. For the
// combined startup audit, use the separately compiled Android Dvar log sink
// as the single Com_Printf definition instead of defining it twice.
void __cdecl Com_Printf(int, const char *format, ...) {
    if (format) std::fputs(format, stderr);
}
#endif

// The original FS_BuildOSPathForThread reports an ERR_FATAL when an engine path
// exceeds its fixed limit. This narrow Android diagnostic boundary has no
// engine-level error recovery loop yet, so preserve fail-closed fatal behavior
// rather than returning a truncated path or pretending ERR_DROP is recoverable.


#if !defined(IW3_IWD_DIRECTORY_LINK_AUDIT)
// The diagnostic shared library uses this narrow formatter. The ARM64
// dependency audit instead links the original q_shared.cpp Com_sprintf body.
int Com_sprintf(char *dest, uint32_t size, const char *format, ...) {
    if (!dest || size == 0 || !format) return -1;
    va_list args;
    va_start(args, format);
    const int written = std::vsnprintf(dest, static_cast<std::size_t>(size),
                                       format, args);
    va_end(args);
    dest[size - 1] = '\0';
    if (written < 0) dest[0] = '\0';
    return written;
}
#endif

void __cdecl MyAssertHandler(const char *filename, int line, int type,
                             const char *format, ...) {
    std::fprintf(stderr, "IW3 assertion failed at %s:%d (type %d): ",
                 filename ? filename : "<unknown>", line, type);
    if (format) {
        va_list args;
        va_start(args, format);
        std::vfprintf(stderr, format, args);
        va_end(args);
    }
    std::fputc('\n', stderr);
    std::abort();
}
