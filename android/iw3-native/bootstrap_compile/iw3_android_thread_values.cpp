// Android implementation of KisakCOD's Sys_SetValue/Sys_GetValue platform contract.
// Windows stores four slots per engine thread context in g_threadValues.
// Android pthreads have independent TLS; use four slots per actual thread rather
// than sharing pointers across the client/server/database threads.
// This is platform plumbing, not an engine/gameplay implementation.
#include <qcommon/threads.h>
#include <cassert>

namespace {
constexpr int kEngineValueSlots = 4;
thread_local void* threadValues[kEngineValueSlots] = {};
}

void __cdecl Sys_SetValue(int valueIndex, void* data)
{
    assert(valueIndex >= 0 && valueIndex < kEngineValueSlots);
    if (valueIndex < 0 || valueIndex >= kEngineValueSlots)
        return;
    threadValues[valueIndex] = data;
}

void* __cdecl Sys_GetValue(int valueIndex)
{
    assert(valueIndex >= 0 && valueIndex < kEngineValueSlots);
    if (valueIndex < 0 || valueIndex >= kEngineValueSlots)
        return nullptr;
    return threadValues[valueIndex];
}
