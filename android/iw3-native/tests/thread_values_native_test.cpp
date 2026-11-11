// Host execution of the Android provider's original IW3 TLS slot ABI.
#include "iw3_android_thread_values.h"
#include <cassert>
#include <atomic>
#include <csetjmp>
#include <thread>

void* Sys_GetValue(int);
void Sys_SetValue(int, void*);
extern void* g_threadValues[THREAD_CONTEXT_COUNT][4];

static void TestJumpAndSlots(ThreadContext_t context, std::atomic<int>& ready) {
    assert(IW3_AndroidBindThreadContext(context));
    assert(!IW3_AndroidThreadHasErrorJump());
    int token = static_cast<int>(context) + 123;
    Sys_SetValue(0, &token);
    jmp_buf jump;
    Sys_SetValue(2, &jump);
    assert(IW3_AndroidThreadHasErrorJump());
    ready.fetch_add(1);
    while (ready.load() != 2) std::this_thread::yield();
    assert(Sys_GetValue(0) == &token);
    assert(Sys_GetValue(2) == &jump);
    assert(g_threadValues[static_cast<int>(context)][2] == &jump);
    int returned = setjmp(jump);
    if (returned == 0) {
        longjmp(*static_cast<jmp_buf*>(Sys_GetValue(2)), 7);
    }
    assert(returned == 7);
    Sys_SetValue(2, nullptr);
    Sys_SetValue(0, nullptr);
    assert(!IW3_AndroidThreadHasErrorJump());
    IW3_AndroidUnbindThreadContext();
    assert(!IW3_AndroidThreadHasErrorJump());
}

int main() {
    assert(!IW3_AndroidThreadHasErrorJump());
    assert(!IW3_AndroidBindThreadContext(static_cast<ThreadContext_t>(-1)));
    assert(!IW3_AndroidBindThreadContext(static_cast<ThreadContext_t>(THREAD_CONTEXT_COUNT)));
    std::atomic<int> ready{0};
    std::thread server(TestJumpAndSlots, THREAD_CONTEXT_SERVER, std::ref(ready));
    TestJumpAndSlots(THREAD_CONTEXT_MAIN, ready);
    server.join();
    assert(g_threadValues[THREAD_CONTEXT_MAIN][2] == nullptr);
    assert(g_threadValues[THREAD_CONTEXT_SERVER][2] == nullptr);
    return 0;
}
