#pragma once
// Platform header only. Original KisakCOD filename, language and IWD sort
// functions plus their q_shared.cpp helpers. No fake archive index.
#include <ctype.h>
#include <stdint.h>
#include <string.h>
#if !defined(_MSC_VER) && !defined(__cdecl)
#define __cdecl
#endif

char *__cdecl IwdFileLanguage(const char *pszIwdFileName);

int __cdecl FS_PathCmp(const char *s1, const char *s2);
int __cdecl iwdsort(const char **a, char **b);
int __cdecl I_strncmp(const char *s0, const char *s1, int n);
int __cdecl I_stricmp(const char *s0, const char *s1);
