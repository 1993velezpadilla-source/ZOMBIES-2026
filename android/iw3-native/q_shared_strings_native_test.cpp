#include "iw3_android_fs_startup_compat.h"

#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>

void QDECL Com_Error(errorParm_t, const char*, ...)
{
    std::abort();
}

void MyAssertHandler(const char*, int, int, const char*, ...)
{
    std::abort();
}

int main()
{
    char copied[8] = {};
    I_strncpyz(copied, "abcdefghijk", static_cast<int>(sizeof(copied)));
    assert(std::strcmp(copied, "abcdefg") == 0);

    char appended[16] = "iw3";
    I_strncat(appended, static_cast<int>(sizeof(appended)), "-arm64");
    assert(std::strcmp(appended, "iw3-arm64") == 0);

    char formatted[32] = {};
    const int fullLength = Com_sprintf(formatted, static_cast<uint32_t>(sizeof(formatted)),
                                       "%s:%d", "iw3", 64);
    assert(fullLength == 6);
    assert(std::strcmp(formatted, "iw3:64") == 0);

    char truncated[5] = {};
    const int truncatedLength = Com_sprintf(truncated, static_cast<uint32_t>(sizeof(truncated)),
                                            "%s", "abcdef");
    assert(truncatedLength == -1);
    assert(std::strcmp(truncated, "abcd") == 0);

    char zeroSized[1] = {'x'};
    const int zeroLength = Com_sprintf(zeroSized, 0, "%s", "not-written");
    assert(zeroLength == -1);
    assert(zeroSized[0] == 'x');

    std::puts("IW3_ORIGINAL_Q_SHARED_STRING_SERVICES_HOST_TEST_PASS");
    return 0;
}
