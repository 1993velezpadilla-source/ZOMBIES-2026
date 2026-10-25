#include "iw3_android_unzip_compat.h"
#include <cerrno>
#include <climits>
#include <sys/types.h>

// Original FS_File* interface semantics used by KisakCOD's unzip.cpp:
// 0=current, 1=end, 2=absolute beginning (not stdio's SEEK_* constants).
FILE *__cdecl FS_FileOpenReadBinary(const char *filename) {
    if (!filename || !*filename) return nullptr;
    return std::fopen(filename, "rb");
}
void __cdecl FS_FileClose(FILE *stream) {
    if (stream) std::fclose(stream);
}
uint32_t __cdecl FS_FileRead(void *ptr, uint32_t len, FILE *stream) {
    if (!stream || (!ptr && len)) return 0;
    return static_cast<uint32_t>(std::fread(ptr, 1, len, stream));
}
int __cdecl FS_FileSeek(FILE *file, int offset, int whence) {
    if (!file) return -1;
    int origin;
    switch (whence) {
        case 0: origin = SEEK_CUR; break;
        case 1: origin = SEEK_END; break;
        case 2: origin = SEEK_SET; break;
        default: return -1;
    }
    return ::fseeko(file, static_cast<off_t>(offset), origin);
}
int __cdecl FileWrapper_Seek(FILE *file, int offset, int origin) {
    return FS_FileSeek(file, offset, origin);
}
int __cdecl FS_FileGetFileSize(FILE *file) {
    if (!file) return -1;
    const off_t current = ::ftello(file);
    if (current < 0 || ::fseeko(file, 0, SEEK_END) != 0) return -1;
    const off_t end = ::ftello(file);
    const int restore = ::fseeko(file, current, SEEK_SET);
    if (end < 0 || restore != 0 || end > INT_MAX) return -1;
    return static_cast<int>(end);
}
int __cdecl FileWrapper_GetFileSize(FILE *file) {
    return FS_FileGetFileSize(file);
}
uint32_t FS_FileTell(FILE *file) {
    if (!file) return UINT32_MAX;
    const off_t position = ::ftello(file);
    if (position < 0 || static_cast<uint64_t>(position) > UINT32_MAX) return UINT32_MAX;
    return static_cast<uint32_t>(position);
}
