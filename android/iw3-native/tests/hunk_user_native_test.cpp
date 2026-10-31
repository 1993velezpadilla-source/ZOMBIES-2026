#include <qcommon/qcommon.h>
#include <universal/assertive.h>
#include <universal/com_memory.h>

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

void MyAssertHandler(const char *filename, int line, int type, const char *fmt, ...)
{
    std::fprintf(stderr, "Unexpected engine assertion in HunkUser test: %s:%d (%d)\n",
                 filename ? filename : "?", line, type);
    (void)fmt;
    std::abort();
}

void __cdecl Com_Error(errorParm_t code, const char *fmt, ...)
{
    std::fprintf(stderr, "Unexpected Com_Error in HunkUser test: %d\n",
                 static_cast<int>(code));
    (void)fmt;
    std::abort();
}

int main()
{
    HunkUser *user = Hunk_UserCreate(0x20000, "hunk-user-native-test", false, false, 0);
    assert(user != nullptr);
    assert((reinterpret_cast<uintptr_t>(user->buf) & 31u) == 0u);

    char *copy = Hunk_CopyString(user, "stringed-loader");
    assert(copy != nullptr);
    assert(std::strcmp(copy, "stringed-loader") == 0);

    auto *large = static_cast<uint8_t *>(Hunk_UserAlloc(user, 8192u, 32));
    assert(large != nullptr);
    assert((reinterpret_cast<uintptr_t>(large) & 31u) == 0u);
    large[0] = 0x31;
    large[4095] = 0x52;
    large[8191] = 0x73;
    assert(large[0] == 0x31);
    assert(large[4095] == 0x52);
    assert(large[8191] == 0x73);

    Hunk_UserReset(user);
    char *afterReset = Hunk_CopyString(user, "after-reset");
    assert(afterReset != nullptr);
    assert(std::strcmp(afterReset, "after-reset") == 0);
    Hunk_UserDestroy(user);
    return 0;
}
