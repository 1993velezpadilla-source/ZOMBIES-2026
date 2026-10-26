#include "iw3_android_fs_read_compat.h"

// The complete upstream com_files.cpp is not linked into this diagnostic
// target; it owns a file-local static fsh[65]. Provide the same original
// fileHandleData_t table type at native 64-bit width for the isolated IWD
// ZIP-branch probe. The original FS_Read body is compiled verbatim and reads
// through unzReadCurrentFile; full open/close handle lifecycle remains pending.
fileHandleData_t fsh[65]{};

extern "C" void z2026_iw3_fs_file_close(FILE *stream) {
    if (stream) std::fclose(stream);
}
