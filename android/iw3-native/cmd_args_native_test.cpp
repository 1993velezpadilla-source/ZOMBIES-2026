// Host regression for the original KisakCOD command-argument accessors.
#include <universal/q_shared.h>
#include <universal/assertive.h>
#include <qcommon/cmd.h>

#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>

CmdArgs cmd_args{};

void MyAssertHandler(const char *, int, int, const char *, ...)
{
    std::abort();
}

int main()
{
    const char *outer[] = {"set", "fs_game", "mods/test"};
    const char *inner[] = {"map"};
    cmd_args.nesting = 0;
    cmd_args.argc[0] = 3;
    cmd_args.argv[0] = outer;

    assert(Cmd_Argc() == 3);
    assert(std::strcmp(Cmd_Argv(0), "set") == 0);
    assert(std::strcmp(Cmd_Argv(1), "fs_game") == 0);
    assert(std::strcmp(Cmd_Argv(2), "mods/test") == 0);
    assert(Cmd_Argv(3)[0] == '\0');

    cmd_args.nesting = 1;
    cmd_args.argc[1] = 1;
    cmd_args.argv[1] = inner;
    assert(Cmd_Argc() == 1);
    assert(std::strcmp(Cmd_Argv(0), "map") == 0);
    assert(Cmd_Argv(1)[0] == '\0');

    cmd_args.nesting = 0;
    assert(Cmd_Argc() == 3);
    std::puts("IW3_ORIGINAL_CMD_ARG_ACCESSORS_HOST_RUNTIME_PASS");
    return 0;
}
