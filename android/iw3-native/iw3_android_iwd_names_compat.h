#pragma once
// Platform header only. All four functions are verbatim KisakCOD C++,
// including the real q_shared.cpp I_islower helper. No fake archive index.
#include <ctype.h>
#if !defined(_MSC_VER) && !defined(__cdecl)
#define __cdecl
#endif

char *__cdecl IwdFileLanguage(const char *pszIwdFileName);
