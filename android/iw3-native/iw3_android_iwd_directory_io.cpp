#include "iw3_android_iwd_directory_compat.h"

#include <algorithm>
#include <cstdarg>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <limits>
#include <string>
#include <vector>

char **Sys_ListFiles(const char *directory, const char *extension,
                     const char *filter, int *numfiles, int wantsubs) {
    if (!numfiles) return nullptr;
    *numfiles = 0;
    if (!directory || (extension && *extension && I_stricmp(extension, "iwd")) ||
        (filter && *filter) || wantsubs != 0) return nullptr;

    std::vector<char> names(1024 * 1024);
    std::size_t count = 0;
    const int bytes = z2026_platform_list_iwd_files(
        directory, names.data(), names.size(), &count);
    if (bytes < 0 || count == 0) return nullptr;

    // The original engine caps the scan to 1024 entries. Keep enough entries
    // for that cap and report 1025 when more exist so its original warning and
    // cap path are still taken without allocating an unbounded pointer table.
    const std::size_t take = std::min<std::size_t>(count, 1024);
    std::vector<std::string> entries;
    entries.reserve(take);
    std::size_t offset = 0;
    for (std::size_t i = 0; i < take; ++i) {
        if (offset >= static_cast<std::size_t>(bytes)) return nullptr;
        const char *name = names.data() + offset;
        const std::size_t remaining = static_cast<std::size_t>(bytes) - offset;
        const void *end = std::memchr(name, '\0', remaining);
        if (!end) return nullptr;
        const auto length = static_cast<const char *>(end) - name;
        if (length <= 0) return nullptr;
        entries.emplace_back(name, static_cast<std::size_t>(length));
        offset += static_cast<std::size_t>(length) + 1;
    }

    std::size_t stringBytes = 0;
    for (const auto &name : entries) {
        if (name.size() + 1 > std::numeric_limits<std::size_t>::max() - stringBytes)
            return nullptr;
        stringBytes += name.size() + 1;
    }
    if (take > (std::numeric_limits<std::size_t>::max() - stringBytes) / sizeof(char *))
        return nullptr;
    const std::size_t total = take * sizeof(char *) + stringBytes;
    if (!total || total > static_cast<std::size_t>(std::numeric_limits<int32_t>::max()))
        return nullptr;

    auto **list = static_cast<char **>(
        Z_Malloc(static_cast<int32_t>(total), "Android Sys_ListFiles IWD", 3));
    if (!list) return nullptr;
    char *cursor = reinterpret_cast<char *>(list + take);
    for (std::size_t i = 0; i < take; ++i) {
        list[i] = cursor;
        std::memcpy(cursor, entries[i].c_str(), entries[i].size() + 1);
        cursor += entries[i].size() + 1;
    }
    *numfiles = count > 1024 ? 1025 : static_cast<int>(count);
    return list;
}

void __cdecl FS_FreeFileList(const char **list) {
    if (list) Z_Free(const_cast<char **>(list), 3);
}

// FS_BuildOSPath is provided by the original body in the IWD lookup source slice.


// The directory scanner's platform boundary is intentionally limited to the
// English locale until the authentic stringed subsystem is ported. Non-English
// localized IWDs fail closed rather than being assigned a fabricated index.
int __cdecl SEH_GetLanguageIndexForName(const char *name, int *index) {
    if (!name || !index || I_stricmp(name, "english") != 0) return 0;
    *index = 0;
    return 1;
}
const char *__cdecl SEH_GetLanguageName(uint32_t language) {
    return language == 0 ? "english" : "";
}

// Console output adapter for this isolated native file-system test. It logs
// the original format string without interpreting platform-specific formats.
void __cdecl Com_PrintWarning(int, const char *format, ...) {
    if (format) { std::fputs("IW3 file warning: ", stderr); std::fputs(format, stderr); }
}
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
