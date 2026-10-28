// Portable provider for the original IW3 filesystem wildcard service.
//
// KisakCOD's q_shared.h declares Com_Filter/Com_FilterPath, and the original
// FS_ListFilteredFilesInLocation body calls Com_FilterPath, but the vendored
// source slice does not contain their provider. This ports the id Tech 3
// wildcard semantics needed by that original filesystem path; it is not a
// replacement filesystem, renderer, or game loop.
#include "q_shared.h"

#include <cctype>
#include <cstddef>
#include <cstring>

namespace {
static bool FilterCharEqual(char lhs, char rhs, int caseSensitive)
{
    if (caseSensitive)
        return lhs == rhs;
    return std::toupper(static_cast<unsigned char>(lhs)) ==
           std::toupper(static_cast<unsigned char>(rhs));
}

static const char *FilterFindSubstring(const char *text, const char *needle,
                                       int caseSensitive)
{
    if (!*needle)
        return text;

    for (const char *candidate = text; *candidate; ++candidate)
    {
        size_t index = 0;
        while (needle[index] && candidate[index] &&
               FilterCharEqual(candidate[index], needle[index], caseSensitive))
            ++index;
        if (!needle[index])
            return candidate;
    }
    return nullptr;
}
} // namespace

char __cdecl Com_Filter(const char *filter, char *name, int casesensitive)
{
    if (!filter || !name)
        return 0;

    while (*filter)
    {
        if (*filter == '*')
        {
            ++filter;
            char literal[MAX_TOKEN_CHARS];
            size_t length = 0;
            while (*filter && *filter != '*' && *filter != '?')
            {
                if (length + 1 >= sizeof(literal))
                    return 0;
                literal[length++] = *filter++;
            }
            literal[length] = '\0';

            if (length)
            {
                const char *match = FilterFindSubstring(name, literal, casesensitive);
                if (!match)
                    return 0;
                name = const_cast<char *>(match + length);
            }
        }
        else if (*filter == '?')
        {
            if (!*name)
                return 0;
            ++filter;
            ++name;
        }
        else if (*filter == '[' && filter[1] == '[')
        {
            // Original id Tech 3 pattern syntax: "[[" escapes a literal '['.
            ++filter;
        }
        else if (*filter == '[')
        {
            const char *cursor = filter + 1;
            bool found = false;

            while (*cursor && !found)
            {
                if (*cursor == ']' && cursor[1] != ']')
                    break;

                if (cursor[1] == '-' && cursor[2] &&
                    (cursor[2] != ']' || cursor[3] == ']'))
                {
                    if (*name)
                    {
                        const int value = static_cast<unsigned char>(*name);
                        int lower = static_cast<unsigned char>(cursor[0]);
                        int upper = static_cast<unsigned char>(cursor[2]);
                        if (!casesensitive)
                        {
                            lower = std::toupper(static_cast<unsigned char>(lower));
                            upper = std::toupper(static_cast<unsigned char>(upper));
                        }
                        found = casesensitive
                            ? value >= lower && value <= upper
                            : std::toupper(static_cast<unsigned char>(value)) >= lower &&
                              std::toupper(static_cast<unsigned char>(value)) <= upper;
                    }
                    cursor += 3;
                }
                else
                {
                    if (*name && FilterCharEqual(*cursor, *name, casesensitive))
                        found = true;
                    ++cursor;
                }
            }

            if (!found || !*cursor)
                return 0;

            while (*cursor)
            {
                if (*cursor == ']' && cursor[1] != ']')
                    break;
                ++cursor;
            }
            if (*cursor != ']')
                return 0;

            filter = cursor + 1;
            ++name;
        }
        else
        {
            if (!*name || !FilterCharEqual(*filter, *name, casesensitive))
                return 0;
            ++filter;
            ++name;
        }
    }

    // Preserve the original helper's prefix-match behavior when the pattern
    // ends; callers that need full-path equality supply an anchored pattern.
    return 1;
}

char __cdecl Com_FilterPath(const char *filter, const char *name, int casesensitive)
{
    if (!filter || !name)
        return 0;

    char normalizedFilter[MAX_QPATH];
    char normalizedName[MAX_QPATH];
    size_t index = 0;

    for (; index < MAX_QPATH - 1 && filter[index]; ++index)
        normalizedFilter[index] = (filter[index] == '\\' || filter[index] == ':')
            ? '/' : filter[index];
    normalizedFilter[index] = '\0';

    index = 0;
    for (; index < MAX_QPATH - 1 && name[index]; ++index)
        normalizedName[index] = (name[index] == '\\' || name[index] == ':')
            ? '/' : name[index];
    normalizedName[index] = '\0';

    return Com_Filter(normalizedFilter, normalizedName, casesensitive);
}
