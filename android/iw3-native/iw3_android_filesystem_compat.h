#pragma once

#include <universal/q_shared.h>

// These are the original engine-facing system service signatures that
// win_local.h normally exposes. Android provides POSIX implementations at the
// platform boundary; declarations here let the authentic filesystem TU compile
// without importing DirectInput/Win32 headers.
void __cdecl Sys_Mkdir(const char *path);
int __cdecl Sys_CountFileList(char **list);
char **__cdecl Sys_ListFiles(
    const char *directory,
    const char *extension,
    const char *filter,
    int *numfiles,
    int wantsubs);
char *__cdecl Sys_Cwd();
const char *__cdecl Sys_DefaultCDPath();
int __cdecl Sys_DirectoryHasContents(const char *directory);

// Windows InterlockedCompareExchange returns the previous value and writes
// exchange only when the target equals comparand. Preserve that contract on
// Android using the compiler's native atomic compare/exchange primitive.
template <typename T>
static inline T z2026_interlocked_compare_exchange(
    volatile T *destination, T exchange, T comparand)
{
    T expected = comparand;
    __atomic_compare_exchange_n(
        destination, &expected, exchange, false,
        __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST);
    return expected;
}
