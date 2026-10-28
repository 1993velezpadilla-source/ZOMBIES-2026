#include "iw3_android_language_compat.h"

#include <cassert>
#include <cctype>
#include <cstdint>
#include <cstring>
#include <string>

int I_stricmp(const char *left, const char *right)
{
    if (!left || !right)
        return left ? 1 : right ? -1 : 0;
    while (*left && *right)
    {
        const int a = std::tolower(static_cast<unsigned char>(*left));
        const int b = std::tolower(static_cast<unsigned char>(*right));
        if (a != b)
            return a - b;
        ++left;
        ++right;
    }
    return std::tolower(static_cast<unsigned char>(*left)) -
           std::tolower(static_cast<unsigned char>(*right));
}

int main()
{
    const char *expected[] = {
        "english", "french", "german", "italian", "spanish",
        "british", "russian", "polish", "korean", "taiwanese",
        "japanese", "chinese", "thai", "leet", "czech"
    };
    static_assert(sizeof(expected) / sizeof(expected[0]) == 15,
                  "KisakCOD source language registry changed");
    assert(sizeof(g_languages) / sizeof(g_languages[0]) == 15);

    for (int i = 0; i < 15; ++i)
    {
        assert(std::strcmp(g_languages[i].pszName, expected[i]) == 0);
        assert(std::strcmp(SEH_GetLanguageName(static_cast<uint32_t>(i)),
                           expected[i]) == 0);

        int index = -1;
        assert(SEH_GetLanguageIndexForName(expected[i], &index) == 1);
        assert(index == i);

        std::string mixedCase(expected[i]);
        for (char &ch : mixedCase)
            ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
        index = -1;
        assert(SEH_GetLanguageIndexForName(mixedCase.c_str(), &index) == 1);
        assert(index == i);
    }

    int index = -1;
    assert(SEH_GetLanguageIndexForName("not-a-kisak-language", &index) == 0);
    assert(index == 0);
    assert(std::strcmp(SEH_GetLanguageName(15), "english") == 0);
    return 0;
}
