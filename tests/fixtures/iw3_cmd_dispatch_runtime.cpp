// Host unit-test boundaries only; never built into the Android application.
#include <qcommon/qcommon.h>
#include <qcommon/cmd.h>
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include "args.cpp"
#include "tokens.cpp"

static int callbacks, forwarded, notifications, dvarCalls;
static bool dvarHandled;
const dvar_t *com_sv_running = nullptr;
bool com_inServerFrame = false;
bool Sys_IsMainThread() { return true; }
void SV_WaitServer() { std::abort(); }
void Cmd_CheckNotify() { ++notifications; }
int Dvar_Command() { ++dvarCalls; return dvarHandled; }
int SV_GameCommand() { std::abort(); }
void CL_ForwardCommandToServer(int, const char *) { ++forwarded; }
void Cbuf_AddServerText_f() { std::abort(); }
void Cmd_ExecuteServerString(char *) { std::abort(); }
void MyAssertHandler(const char *file, int line, int, const char *format, ...)
{
    std::fprintf(stderr, "%s:%d: ", file, line);
    va_list args; va_start(args, format); std::vfprintf(stderr, format, args); va_end(args);
    std::abort();
}
void Com_Printf(int, const char *format, ...)
{
    va_list args; va_start(args, format); std::vfprintf(stderr, format, args); va_end(args);
}
char *va(const char *format, ...)
{
    static thread_local char text[2048];
    va_list args; va_start(args, format); std::vsnprintf(text, sizeof(text), format, args); va_end(args);
    return text;
}

// ORIGINAL_COMMAND_BODIES

static void execute(const char *command)
{
    std::string text(command);
    Cmd_ExecuteSingleCommand(0, 0, text.data());
}
static void callback()
{
    ++callbacks;
    assert(Cmd_Argc() >= 1);
}
static void outer()
{
    assert(Cmd_Argc() == 2 && std::strcmp(Cmd_Argv(1), "keep me") == 0);
    execute("inner 7");
    assert(Cmd_Argc() == 2 && std::strcmp(Cmd_Argv(1), "keep me") == 0);
}

int main(int argc, char **argv)
{
    assert(argc == 2);
    Cmd_ComErrorCleanup();
    Cmd_Shutdown();
    cmd_function_s tail{}, middle{}, head{};
    if (!std::strcmp(argv[1], "empty")) {
        execute("unknown");
        assert(forwarded == 1 && dvarCalls == 1);
    } else if (!std::strcmp(argv[1], "single")) {
        Cmd_AddCommandInternal("one", callback, &tail);
        execute("ONE");
        assert(callbacks == 1 && forwarded == 0 && dvarCalls == 0);
    } else if (!std::strcmp(argv[1], "list")) {
        Cmd_AddCommandInternal("tail", callback, &tail);
        Cmd_AddCommandInternal("middle", callback, &middle);
        Cmd_AddCommandInternal("head", callback, &head);
        execute("head"); execute("middle"); execute("tail");
        assert(callbacks == 3 && forwarded == 0);
        Cmd_RemoveCommand("head"); Cmd_RemoveCommand("middle");
        execute("tail");
        assert(callbacks == 4);
        Cmd_RemoveCommand("tail");
        execute("unknown");
        assert(forwarded == 1);
    } else if (!std::strcmp(argv[1], "nested")) {
        Cmd_AddCommandInternal("inner", callback, &tail);
        Cmd_AddCommandInternal("outer", outer, &head);
        execute("outer \"keep me\"");
        assert(callbacks == 1 && notifications == 2 && forwarded == 0);
    } else {
        assert(!std::strcmp(argv[1], "fallback"));
        execute("   // empty");
        assert(notifications == 0 && forwarded == 0);
        Cmd_AddCommandInternal("known", callback, &tail);
        execute("unknown");
        assert(forwarded == 1 && dvarCalls == 1);
        dvarHandled = true;
        execute("known_dvar value");
        assert(forwarded == 1 && dvarCalls == 2);
    }
    assert(cmd_args.nesting == -1);
    assert(cmd_argsPrivate.totalUsedArgvPool == 0);
    assert(cmd_argsPrivate.totalUsedTextPool == 0);
    Cmd_Shutdown();
}
