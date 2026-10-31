#include "iw3_android_iwd_lookup_compat.h"
#include "iw3_android_platform.h"

#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <unistd.h>

// Root-confined FILE adapters for the original directory fallback branch.
// They preserve FS_FileOpenReadBinary/FS_FileClose semantics without
// colliding with this source snapshot's iobuf-typed public declarations.
FILE *z2026_iw3_lookup_file_open_read_binary(const char *path) {
    if (!path) return nullptr;
    const int fd = z2026_platform_open_engine_path_fd(path);
    if (fd < 0) return nullptr;
    FILE *stream = ::fdopen(fd, "rb");
    if (!stream) ::close(fd);
    return stream;
}

void z2026_iw3_lookup_file_close_binary(FILE *stream) {
    if (stream) std::fclose(stream);
}

// The diagnostic APK registers nonlocalized English fixtures only. The
// combined engine audit must bind the original StringEd language provider.
#if !defined(IW3_IWD_DIRECTORY_LINK_AUDIT)
int __cdecl SEH_GetCurrentLanguage() {
    return 0;
}
#endif

// Error-only adapters for original diagnostics/path-overflow handling. They
// fail closed; they do not provide gameplay or suppress an engine fatal error.
char *QDECL va(const char *format, ...) {
    static thread_local char buffer[2048];
    if (!format) return const_cast<char *>("");
    va_list args;
    va_start(args, format);
    const int written = std::vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    if (written < 0) buffer[0] = '\0';
    buffer[sizeof(buffer) - 1] = '\0';
    return buffer;
}

void QDECL Com_Error(errorParm_t code, const char *format, ...) {
    std::fprintf(stderr, "IW3 original file lookup fatal error (%d): ",
                 static_cast<int>(code));
    if (format) {
        va_list args;
        va_start(args, format);
        std::vfprintf(stderr, format, args);
        va_end(args);
    }
    std::fputc('\n', stderr);
    std::abort();
}
