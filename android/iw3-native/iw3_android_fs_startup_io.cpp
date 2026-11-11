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

extern "C" IW3_ANDROID_EXPORT int z2026_iw3_fs_startup_path_smoke() {
    char path[1024]{};
    if (z2026_platform_copy_data_root(path, sizeof(path)) < 0) return 0;
    char *cwd = Sys_Cwd();
    char *cdpath = Sys_DefaultCDPath();
    return cwd && std::strcmp(cwd, path) == 0 && cdpath && cdpath[0] == '\0';
}
