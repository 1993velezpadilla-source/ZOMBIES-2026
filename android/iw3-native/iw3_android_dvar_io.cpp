// Android/POSIX implementation of the original KisakCOD NET_Sleep service.
// win32/win_net.cpp implements this service as Sleep(msec). The dvar registry
// uses 0 for yielding while a critical-section counter changes and positive
// values for short back-off waits; no networking implementation is substituted.
#include <cerrno>
#include <time.h>
#include <sched.h>

void NET_Sleep(int msec)
{
    if (msec <= 0)
    {
        // Sleep(0) yields the current time slice instead of busy-spinning.
        (void)sched_yield();
        return;
    }

    timespec remaining{};
    remaining.tv_sec = static_cast<time_t>(msec / 1000);
    remaining.tv_nsec = static_cast<long>(msec % 1000) * 1000000L;
    while (nanosleep(&remaining, &remaining) == -1)
    {
        if (errno != EINTR)
            return;
    }
}
