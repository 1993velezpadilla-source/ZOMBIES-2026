#include "iw3_android_thread_values.h"

#include <qcommon/threads.h>
#include <universal/q_shared.h>

// Android OS boundary only: invoke the *original* Com_InitThreadData from
// universal/q_shared.cpp after selecting the original MAIN context table.
// This initializes the original va, jmp_buf and trace slots (1, 2 and 3).
// It does NOT start Com_Init, configure the profile slot (0), create renderer
// threads or replace the original engine's main-thread bootstrap.
bool IW3_AndroidBindMainThreadSharedData() {
    if (!IW3_AndroidBindThreadContext(THREAD_CONTEXT_MAIN)) {
        return false;
    }
    Com_InitThreadData(THREAD_CONTEXT_MAIN);
    if (!IW3_AndroidThreadHasErrorJump()) {
        IW3_AndroidUnbindThreadContext();
        return false;
    }
    return true;
}
