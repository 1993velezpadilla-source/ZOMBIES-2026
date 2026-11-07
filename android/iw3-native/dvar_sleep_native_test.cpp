#include <cassert>
#include <chrono>
#include <cstdio>

void NET_Sleep(int msec);

int main()
{
    using clock = std::chrono::steady_clock;
    const auto zero_start = clock::now();
    NET_Sleep(0);
    assert(clock::now() - zero_start < std::chrono::seconds(1));

    // The original Win32 implementation is Sleep(msec). A positive delay
    // must not return early; allow 1 ms of clock/scheduler tolerance.
    const auto positive_start = clock::now();
    NET_Sleep(5);
    const auto elapsed = clock::now() - positive_start;
    assert(elapsed >= std::chrono::milliseconds(4));
    assert(elapsed < std::chrono::seconds(1));

    std::puts("IW3_ANDROID_DVAR_NET_SLEEP_HOST_GREEN");
    return 0;
}
