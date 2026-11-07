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

// I_strncpyz is already supplied by the original IWD-services archive in the
// ARM64 audit. Keep the isolated host test focused on I_strncat's call contract
// without linking that archive's allocator/checksum objects into this test.
void I_strncpyz(char* dest, const char* src, int destsize)
{
    if (!dest || !src || destsize < 1) std::abort();
    std::strncpy(dest, src, static_cast<std::size_t>(destsize - 1));
    dest[destsize - 1] = '\\0';
}

int main()
{
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
