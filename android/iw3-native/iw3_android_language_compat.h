#pragma once
#include <stdint.h>

#ifndef __cdecl
#define __cdecl
#endif

// Native layout of the original KisakCOD languageInfo_t. The old source
// comment describes the Win32 layout (8 bytes); LP64 requires 16 bytes.
struct languageInfo_t {
    const char *pszName;
    int bPresent;
};
static_assert(sizeof(languageInfo_t) == (sizeof(void *) == 8 ? 16u : 8u),
              "KisakCOD languageInfo_t must use native pointer layout");

extern languageInfo_t g_languages[15];
const char *__cdecl SEH_GetLanguageName(uint32_t iLanguage);
int __cdecl SEH_GetLanguageIndexForName(const char *pszLanguageName,
                                        int *piLanguageIndex);
