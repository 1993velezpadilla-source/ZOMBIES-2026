// Executes the authentic KisakCOD parser bodies with only OS/error sinks adapted.
#include <universal/q_shared.h>
#include <universal/q_parse.h>
#include <universal/assertive.h>
#include <qcommon/qcommon.h>

#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>

bool __cdecl Sys_IsMainThread();
bool __cdecl Sys_IsRenderThread();
bool __cdecl Sys_IsDatabaseThread();
bool __cdecl Sys_IsServerThread();

bool __cdecl Sys_IsMainThread() { return true; }
bool __cdecl Sys_IsRenderThread() { return false; }
bool __cdecl Sys_IsDatabaseThread() { return false; }
bool __cdecl Sys_IsServerThread() { return false; }

void QDECL Com_Printf(int channel, const char *fmt, ...)
{
    (void)channel;
    (void)fmt;
}

void QDECL Com_Error(errorParm_t code, const char *fmt, ...)
{
    (void)code;
    (void)fmt;
    std::abort();
}

void MyAssertHandler(const char *filename, int line, int type, const char *fmt, ...)
{
    (void)filename;
    (void)line;
    (void)type;
    (void)fmt;
    std::abort();
}

static void expect_token(const char **cursor, const char *expected)
{
    const parseInfo_t *parsed = Com_Parse(cursor);
    if (std::strcmp(parsed->token, expected) != 0)
    {
        std::fprintf(stderr, "parser token mismatch: expected <%s>, got <%s>\n",
                     expected, parsed->token);
        std::exit(1);
    }
}

int main()
{
    Com_InitParse();
    Com_BeginParseSession("android-fs-startup-token-test");
    const char *text = "set fs_game \"mods/test\" // comment\r\nnext 42";
    expect_token(&text, "set");
    Com_UngetToken();
    expect_token(&text, "set");
    expect_token(&text, "fs_game");
    expect_token(&text, "mods/test");
    expect_token(&text, "next");
    if (Com_GetCurrentParseLine() != 2)
    {
        std::fprintf(stderr, "parser line counter mismatch: got %d\n",
                     Com_GetCurrentParseLine());
        return 2;
    }
    expect_token(&text, "42");
    expect_token(&text, "");
    Com_EndParseSession();

    Com_BeginParseSession("android-fs-startup-csv-test");
    Com_SetCSV(1);
    const char *csv = "alpha,\"two,words\",omega\n";
    expect_token(&csv, "alpha");
    expect_token(&csv, "two,words");
    expect_token(&csv, "omega");
    expect_token(&csv, "");
    Com_EndParseSession();

    std::puts("IW3_ORIGINAL_Q_PARSE_HOST_RUNTIME_PASS");
    return 0;
}
