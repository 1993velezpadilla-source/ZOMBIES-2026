#include "iw3_android_thread_values.h"

#include <cstdlib>

// Original qcommon/threads.cpp owns this exact 4-slot array on Windows.
// Build this Android provider INSTEAD of the Win32-only threads.cpp; never
// link both providers. Slots are indexed by original ThreadContext_t values.
void* g_threadValues[THREAD_CONTEXT_COUNT][4] = {};

namespace {
constexpr int kThreadValueSlots = 4;
thread_local void** s_threadLocals = nullptr;

void ValidateSlot(int index) {
    // Com_Init/Com_Error dereference slot 2 as a jmp_buf*. An unbound thread
    // or an invalid slot must fail immediately, not corrupt adjacent state.
    if (!s_threadLocals || index < 0 || index >= kThreadValueSlots) {
        std::abort();
    }
}
} // namespace

bool IW3_AndroidBindThreadContext(ThreadContext_t context) {
    const int index = static_cast<int>(context);
    if (index < 0 || index >= THREAD_CONTEXT_COUNT) {
        return false;
    }
    s_threadLocals = g_threadValues[index];
    return true;
}

void IW3_AndroidUnbindThreadContext() {
    s_threadLocals = nullptr;
}

bool IW3_AndroidThreadHasErrorJump() {
    return s_threadLocals && s_threadLocals[2] != nullptr;
}

// Preserve the mangled C++ symbols consumed by the original common.cpp.
void Sys_SetValue(int valueIndex, void* data) {
    ValidateSlot(valueIndex);
    s_threadLocals[valueIndex] = data;
}

void* Sys_GetValue(int valueIndex) {
    ValidateSlot(valueIndex);
    return s_threadLocals[valueIndex];
}
