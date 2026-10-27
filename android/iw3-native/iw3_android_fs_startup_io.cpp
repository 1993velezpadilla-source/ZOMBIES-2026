#include "iw3_android_platform.h"

#include <cstring>

// The original FS_RegisterDvars calls Sys_Cwd for fs_basepath. Android's
// process working directory is not a reliable game-data location, so return
// the app-private filesDir configured by nativeSetDataRoot instead.
char *Sys_Cwd() {
    static thread_local char path[1024]{};
    if (z2026_platform_copy_data_root(path, sizeof(path)) < 0) {
        path[0] = '\0';
    }
    return path;
}

// Android has no optical-disc install path. The original dvar registration
// expects an empty CD path and then searches basepath/homepath as usual.
char *Sys_DefaultCDPath() {
    static char empty_path[] = "";
    return empty_path;
}

// Original com_files.cpp only supplies this helper under WIN32. Android
// keeps the same 0/1 contract but scans strictly beneath the configured app
// data root; paths outside that root fail closed as "no contents".
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

    const int result = z2026_platform_directory_has_contents(relative);
    return result > 0 ? 1 : 0;
}

extern "C" IW3_ANDROID_EXPORT int z2026_iw3_fs_startup_path_smoke() {
    char path[1024]{};
    if (z2026_platform_copy_data_root(path, sizeof(path)) < 0) return 0;
    char *cwd = Sys_Cwd();
    char *cdpath = Sys_DefaultCDPath();
    return cwd && std::strcmp(cwd, path) == 0 && cdpath && cdpath[0] == '\0';
}
