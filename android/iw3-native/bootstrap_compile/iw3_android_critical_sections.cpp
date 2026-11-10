// POSIX boundary for the original KisakCOD SP Sys_* critical-section contract.
// Win32 CRITICAL_SECTION is recursive; std::recursive_mutex preserves that
// property while keeping each engine critical-section index independent.
// This is synchronization plumbing, not a replacement game engine.
#include <array>
#include <cassert>
#include <mutex>

namespace {
constexpr int kSpCriticalSectionCount = 35; // win_local.h: 0x00..0x22, CRITSECT_COUNT
std::array<std::recursive_mutex, kSpCriticalSectionCount> criticalSections;
bool validIndex(int index) {
    assert(index >= 0 && index < kSpCriticalSectionCount);
    return index >= 0 && index < kSpCriticalSectionCount;
}
}

void Sys_InitializeCriticalSections() {
    // Static recursive mutexes are initialized before the first engine call.
}
void Sys_EnterCriticalSection(int critSect) {
    if (validIndex(critSect)) criticalSections[critSect].lock();
}
void Sys_LeaveCriticalSection(int critSect) {
    if (validIndex(critSect)) criticalSections[critSect].unlock();
}
