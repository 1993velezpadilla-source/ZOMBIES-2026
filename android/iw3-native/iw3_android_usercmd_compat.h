#pragma once
// Compile the authentic IW3 SP usercmd_s declaration from qcommon/msg.h on
// Android/host. Temporary aliases adapt MSVC integer spellings only; the
// struct fields and BUTTON_* values remain the original engine header.
#include "iw3_android_math_compat.h"
#include <cstddef>
#include <cstdint>
#ifndef KISAK_SP
#define KISAK_SP 1
#define Z2026_UNDEFINE_KISAK_SP
#endif
#define __int8 char
#define __int16 short
#define __int32 int
#define __int64 long long
#include "msg.h"
#undef __int8
#undef __int16
#undef __int32
#undef __int64
#ifdef Z2026_UNDEFINE_KISAK_SP
#undef KISAK_SP
#undef Z2026_UNDEFINE_KISAK_SP
#endif
static_assert(sizeof(usercmd_s) == 56, "IW3 SP usercmd_s layout changed");
static_assert(offsetof(usercmd_s, serverTime) == 0);
static_assert(offsetof(usercmd_s, buttons) == 4);
static_assert(offsetof(usercmd_s, angles) == 8);
static_assert(offsetof(usercmd_s, weapon) == 20);
static_assert(offsetof(usercmd_s, forwardmove) == 22);
static_assert(offsetof(usercmd_s, gunPitch) == 28);
static_assert(offsetof(usercmd_s, meleeChargeDist) == 52);
static_assert(offsetof(usercmd_s, selectedLocation) == 53);
