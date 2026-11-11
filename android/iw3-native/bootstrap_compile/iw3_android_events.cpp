// Android/POSIX implementation of the original IW3 event API.
// Event handles remain opaque void* as required by qcommon/threads.h.
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <mutex>
#include <new>

namespace {
struct Event {
    std::mutex mutex;
    std::condition_variable condition;
    bool manual_reset;
    bool signaled;
    Event(bool manual, bool initial) : manual_reset(manual), signaled(initial) {}
};
}

void Sys_CreateEvent(bool manualReset, bool initialState, void** event) {
    if (!event) return;
    *event = new (std::nothrow) Event(manualReset, initialState);
}
void Sys_SetEvent(void** event) {
    if (!event || !*event) return;
    auto& e = *static_cast<Event*>(*event);
    {
        std::lock_guard<std::mutex> lock(e.mutex);
        e.signaled = true;
    }
    if (e.manual_reset) e.condition.notify_all();
    else e.condition.notify_one();
}
void Sys_ResetEvent(void** event) {
    if (!event || !*event) return;
    auto& e = *static_cast<Event*>(*event);
    std::lock_guard<std::mutex> lock(e.mutex);
    e.signaled = false;
}
bool Sys_WaitForSingleObjectTimeout(void** event, std::uint32_t msec) {
    if (!event || !*event) return false;
    auto& e = *static_cast<Event*>(*event);
    std::unique_lock<std::mutex> lock(e.mutex);
    // Win32 INFINITE (0xffffffff) means an unbounded wait, not a finite timeout.
    // The original IW3 callers use the Win32 event API contract.
    if (msec == UINT32_MAX) {
        e.condition.wait(lock, [&] { return e.signaled; });
    } else if (!e.condition.wait_for(lock, std::chrono::milliseconds(msec), [&] { return e.signaled; })) {
        return false;
    }
    if (!e.manual_reset) e.signaled = false;
    return true;
}
void Sys_WaitForSingleObject(void** event) {
    if (!event || !*event) return;
    auto& e = *static_cast<Event*>(*event);
    std::unique_lock<std::mutex> lock(e.mutex);
    e.condition.wait(lock, [&] { return e.signaled; });
    if (!e.manual_reset) e.signaled = false;
}
