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
    if (!directory) return nullptr;

    bool directory_only = wantsubs != 0;
    const char *effective_extension = extension;
    if (effective_extension && effective_extension[0] == '/') {
        directory_only = true;
        ++effective_extension;
    }

    // Preserve the original IW3 IWD path's 1024-entry native readdir prefix.
    // Other filesystem queries must enumerate ordinary assets and directories;
    // the old adapter rejected every non-IWD extension, filter and directory
    // query, preventing the original FS/StringEd search graph from finding assets.
    const bool iwd_fast_path =
        !directory_only && (!filter || !*filter) &&
        effective_extension && I_stricmp(effective_extension, "iwd") == 0;

    std::vector<char> names(8 * 1024 * 1024);
    std::size_t raw_count = 0;
    const int bytes = iwd_fast_path
        ? z2026_platform_list_iwd_files(directory, names.data(), names.size(),
                                        &raw_count)
        : z2026_platform_list_directory_entries(
              directory, directory_only ? 1 : 0, names.data(), names.size(),
              &raw_count);
    if (bytes < 0 || raw_count == 0) return nullptr;

    // The IWD fast path returns the total count but stores only the first 1024
    // names. Generic enumeration returns every name in the NUL-separated buffer.
    const std::size_t available = iwd_fast_path
        ? std::min<std::size_t>(raw_count, 1024)
        : raw_count;
    std::vector<std::string> entries;
    entries.reserve(available);
    std::size_t offset = 0;
    for (std::size_t i = 0; i < available; ++i) {
        if (offset >= static_cast<std::size_t>(bytes)) return nullptr;
        const char *name = names.data() + offset;
        const std::size_t remaining = static_cast<std::size_t>(bytes) - offset;
        const void *end = std::memchr(name, '\0', remaining);
        if (!end) return nullptr;
        const std::size_t length =
            static_cast<const char *>(end) - name;
        if (length == 0) return nullptr;

        bool matches = true;
        if (!directory_only && effective_extension && *effective_extension) {
            const std::size_t extension_length = std::strlen(effective_extension);
            const bool extension_has_dot = effective_extension[0] == '.';
            if (extension_length > length ||
                I_stricmp(name + length - extension_length,
                          effective_extension) != 0) {
                matches = false;
            } else if (!extension_has_dot &&
                       (length <= extension_length ||
                        name[length - extension_length - 1] != '.')) {
                matches = false;
            }
        }
        if (matches && filter && *filter &&
            !Com_FilterPath(filter, name, 0)) {
            matches = false;
        }
        if (matches) entries.emplace_back(name, length);
        offset += length + 1;
    }

    if (entries.empty() ||
        entries.size() > static_cast<std::size_t>(std::numeric_limits<int>::max()))
        return nullptr;

    std::size_t stringBytes = 0;
    for (const auto &name : entries) {
        if (name.size() + 1 >
            std::numeric_limits<std::size_t>::max() - stringBytes)
            return nullptr;
        stringBytes += name.size() + 1;
    }
    if (entries.size() >
        (std::numeric_limits<std::size_t>::max() - stringBytes) / sizeof(char *))
        return nullptr;
    const std::size_t total = entries.size() * sizeof(char *) + stringBytes;
    if (!total || total > static_cast<std::size_t>(std::numeric_limits<int32_t>::max()))
        return nullptr;

    auto **list = static_cast<char **>(
        Z_Malloc(static_cast<int32_t>(total), "Android Sys_ListFiles", 3));
    if (!list) return nullptr;
    char *cursor = reinterpret_cast<char *>(list + entries.size());
    for (std::size_t i = 0; i < entries.size(); ++i) {
        list[i] = cursor;
        std::memcpy(cursor, entries[i].c_str(), entries[i].size() + 1);
        cursor += entries[i].size() + 1;
    }

    // Keep the original IWD over-limit signal so FS_AddIwdFilesForGameDirectory
    // emits its own warning and clamps to 1024 without changing archive order.
    *numfiles = iwd_fast_path && raw_count > 1024
        ? 1025 : static_cast<int>(entries.size());
    return list;
}

void __cdecl FS_FreeFileList(const char **list) {
    if (list) Z_Free(const_cast<char **>(list), 3);
}

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
