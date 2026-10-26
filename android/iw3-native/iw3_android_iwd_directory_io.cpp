#include "iw3_android_iwd_directory_compat.h"

#include <algorithm>
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

void __cdecl FS_BuildOSPath(const char *base, const char *game,
                            const char *qpath, char *ospath) {
    if (!ospath) return;
    ospath[0] = '\0';
    std::string result;
    auto append = [&result](const char *part) {
        if (!part || !*part) return;
        if (!result.empty() && result.back() != '/') result.push_back('/');
        result += part;
    };
    append(base);
    append(game);
    if (qpath && *qpath) append(qpath);
    else if (result.empty() || result.back() != '/') result.push_back('/');
    // FS_AddIwdFilesForGameDirectory owns a 260-byte stack buffer. Fail closed
    // instead of truncating a path that would identify a different archive.
    if (result.size() >= 260) return;
    std::memcpy(ospath, result.c_str(), result.size() + 1);
}

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
void __cdecl Com_Printf(int, const char *format, ...) {
    if (format) std::fputs(format, stderr);
}
