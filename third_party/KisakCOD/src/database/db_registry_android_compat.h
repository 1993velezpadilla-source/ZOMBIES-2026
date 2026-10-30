#pragma once

// Android-only declarations for genuine platform services consumed by the
// original database registry. These are implemented with POSIX/app-private
// primitives; this header does not provide renderer or database stubs.
#include <cstdint>
#include <cstdio>

#include "iw3_android_platform.h"

constexpr int CRITSECT_MISSING_ASSET = 0x17; // KisakCOD SP win_local.h ABI value

static inline int InterlockedIncrement(volatile uint32_t *value)
{
    return static_cast<int>(__atomic_add_fetch(value, 1u, __ATOMIC_SEQ_CST));
}

static inline int InterlockedDecrement(volatile uint32_t *value)
{
    return static_cast<int>(__atomic_sub_fetch(value, 1u, __ATOMIC_SEQ_CST));
}

// db_registry.cpp uses _itoa only for decimal FastFile size diagnostics.
static inline char *_itoa(int value, char *buffer, int radix)
{
    if (!buffer)
        return nullptr;
    if (radix == 10)
        std::snprintf(buffer, 16, "%d", value);
    else if (radix == 16)
        std::snprintf(buffer, 16, "%x", static_cast<unsigned int>(value));
    else
        buffer[0] = '\0';
    return buffer;
}

// Android implementation returns the configured app-private filesDir. The
// original DB_BuildOSPath_Mod path is subsequently normalized and confined by
// DBFastFilePosixOpenEnginePath.
char *Sys_DefaultInstallPath();
