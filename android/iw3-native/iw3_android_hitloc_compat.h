#pragma once
// Only Windows ABI spelling for an EXACT original IW3 SP g_combat function.
// No replacement combat/damage logic is implemented in this header.
#if !defined(_MSC_VER) && !defined(__cdecl)
#define __cdecl
#endif
#ifndef __int8
#define __int8 char
#endif
