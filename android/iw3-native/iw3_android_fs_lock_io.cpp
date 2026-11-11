#include "qcommon/fast_critical_section.h"

#include <cassert>
#include <sched.h>
#include <cstdint>

// Android/POSIX port of the original KisakCOD writer gate from
// universal/win_common.cpp. Preserve the engine's 8-byte counter ABI while
// using compiler atomics with sequentially-consistent ordering (the original
// Interlocked operations are full barriers).
void Sys_LockWrite(FastCriticalSection *critSect) {
    assert(critSect != nullptr);
    if (!critSect) return;

    for (;;) {
        if (__atomic_load_n(&critSect->readCount, __ATOMIC_SEQ_CST) == 0) {
            const uint32_t writers =
                __atomic_add_fetch(&critSect->writeCount, 1U, __ATOMIC_SEQ_CST);
            if (writers == 1U &&
                __atomic_load_n(&critSect->readCount, __ATOMIC_SEQ_CST) == 0) {
                return;
            }
            __atomic_sub_fetch(&critSect->writeCount, 1U, __ATOMIC_SEQ_CST);
        }
        // Match the original NET_Sleep(0) contention yield without importing
        // the Windows networking layer into the Android engine module.
        (void)sched_yield();
    }
}

void Sys_UnlockWrite(FastCriticalSection *critSect) {
    assert(critSect != nullptr);
    if (!critSect) return;
    const uint32_t writers = __atomic_load_n(&critSect->writeCount, __ATOMIC_SEQ_CST);
    assert(writers > 0U);
    if (writers == 0U) return;
    __atomic_sub_fetch(&critSect->writeCount, 1U, __ATOMIC_SEQ_CST);
}
