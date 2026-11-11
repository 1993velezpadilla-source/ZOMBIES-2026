#include "iw3_android_iwd_directory_compat.h"
#include <universal/com_memory.h>

#include <algorithm>
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
    // FS_FreeFileList reads the HunkUser owner in list[-1]. Reserve that
    // native-width prefix and a terminating NULL, as original IW3 lists do.
    const std::size_t pointerCount = entries.size() + 2;
    if (pointerCount >
        (std::numeric_limits<std::size_t>::max() - stringBytes) / sizeof(char *))
        return nullptr;
    const std::size_t total = pointerCount * sizeof(char *) + stringBytes;
    const std::size_t headerAndRounding = offsetof(HunkUser, buf) + 4095u;
    if (total > static_cast<std::size_t>(std::numeric_limits<int32_t>::max()) - headerAndRounding)
        return nullptr;

    const std::size_t reservation = (total + headerAndRounding) & ~std::size_t(4095u);
    HunkUser *owner = Hunk_UserCreate(static_cast<int32_t>(reservation),
                                    "Android Sys_ListFiles", true, false, 3);
    auto **storage = static_cast<char **>(Hunk_UserAlloc(
        owner, static_cast<uint32_t>(total), static_cast<int32_t>(alignof(char *))));
    storage[0] = reinterpret_cast<char *>(owner);
    char **list = storage + 1;
    list[entries.size()] = nullptr;
    char *cursor = reinterpret_cast<char *>(list + entries.size() + 1);
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
