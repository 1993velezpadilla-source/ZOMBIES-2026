#pragma once

// Narrow Android compatibility surface for compiling the authentic KisakCOD
// dvar.cpp translation unit. These wrappers preserve Win32 Interlocked return
// semantics; lock and network sleep services remain real unresolved engine
// dependencies until the Android runtime service graph is linked.
#include <cstdint>
#include <cstdio>
#include <qcommon/fast_critical_section.h>

using LONG = std::int32_t;

// Only these declarations from the Win32 network/math headers are used by
// this TU. Keep their original ABI without importing net_chan.h or the POSIX
// random() declaration conflict from com_math.h.
void NET_Sleep(int msec);
bool __cdecl Vec4Compare(const float *a, const float *b);

#ifndef CLAMP
#define CLAMP(x, low, high) ((x) < (low) ? (low) : ((x) > (high) ? (high) : (x)))
#endif

template <typename T>
inline T InterlockedIncrement(volatile T *value) noexcept
{
    return __atomic_add_fetch(value, static_cast<T>(1), __ATOMIC_SEQ_CST);
}

template <typename T>
inline T InterlockedDecrement(volatile T *value) noexcept
{
    return __atomic_sub_fetch(value, static_cast<T>(1), __ATOMIC_SEQ_CST);
}

// Windows InterlockedCompareExchange returns the value observed before the
// operation, not a boolean. Keep that contract for the original dvar sorter.
template <typename T>
inline T InterlockedCompareExchange(
    volatile T *destination, T exchange, T comparand) noexcept
{
    T expected = comparand;
    (void)__atomic_compare_exchange_n(
        destination, &expected, exchange, false,
        __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST);
    return expected;
}

#ifndef _snprintf
#define _snprintf std::snprintf
#endif
