#include "iw3_android_platform.h"

#include <cstddef>
#include <cstring>

// The original com_files.cpp defines Sys_DirectoryHasContents only under
// WIN32. Android keeps its 0/1 contract while translating the engine's absolute
// app-root path to a relative path for the openat/no-follow platform scanner.
// POSIX/Android use the platform's default C calling convention; __cdecl is a
// Win32-only spelling and is intentionally not used by this adapter.
int Sys_DirectoryHasContents(const char *directory) {
    if (!directory) return 0;

    char root[1024]{};
    const int root_length_value = z2026_platform_copy_data_root(root, sizeof(root));
    if (root_length_value <= 0 ||
        static_cast<std::size_t>(root_length_value) >= sizeof(root)) return 0;

    const std::size_t root_length = static_cast<std::size_t>(root_length_value);
    if (std::strncmp(directory, root, root_length) != 0) return 0;

    const char boundary = directory[root_length];
    const char *relative = nullptr;
    if (boundary == '\0') {
        relative = "";
    } else if (boundary == '/' || boundary == '\\') {
        relative = directory + root_length + 1;
    } else {
        // Reject sibling paths such as files-evil when root is files.
        return 0;
    }

    // The platform scanner rejects traversal, symlinks and unreadable paths.
    // Treat any error as empty, matching the original Windows helper.
    const int result = z2026_platform_directory_has_contents(relative);
    return result > 0 ? 1 : 0;
}
