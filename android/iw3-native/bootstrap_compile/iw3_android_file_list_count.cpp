#include <cstddef>

// Platform boundary for the original FS_GetModList in universal/com_files.cpp.
// Sys_ListFiles returns a NULL-terminated array; ownership stays with the
// original filesystem and must be released by Sys_FreeFileList.
int Sys_CountFileList(char** files) {
    if (!files) return 0;
    int count = 0;
    while (files[count] != nullptr) ++count;
    return count;
}
