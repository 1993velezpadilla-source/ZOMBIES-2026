#!/usr/bin/env python3
"""Insert opt-in early breakpoint logging into a disposable KisakCOD copy.

Do NOT edit the pinned vendored third_party/KisakCOD source. This adds a
WinMain-entry vectored exception logger in a freshly copied runner tree and
does not disable/skip/assert/consume the breakpoint. Logs exception location
and PDB symbol if Windows allows it, then returns EXCEPTION_CONTINUE_SEARCH.
"""
from pathlib import Path
import argparse
import sys

MARKER = "int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {"
HEADER = r'''
// ZOMBIES-2026 temporary diagnostic: NOT part of upstream KisakCOD.
#include <Windows.h>
#include <cstdio>
#include <DbgHelp.h>
#pragma comment(lib, "Dbghelp.lib")
static LONG WINAPI Z2026_LogFirstBreakpoint(PEXCEPTION_POINTERS exception)
{
    if (!exception || !exception->ExceptionRecord ||
        exception->ExceptionRecord->ExceptionCode != EXCEPTION_BREAKPOINT)
        return EXCEPTION_CONTINUE_SEARCH;
    FILE *f = nullptr;
    if (fopen_s(&f, "kisak-breakpoint-diagnostic.txt", "a") != 0 || !f)
        return EXCEPTION_CONTINUE_SEARCH;
    void *fault = exception->ExceptionRecord->ExceptionAddress;
    fprintf(f, "BREAKPOINT code=%08lx fault=%p\n",
        (unsigned long)exception->ExceptionRecord->ExceptionCode, fault);
    HANDLE process = GetCurrentProcess();
    if (SymInitialize(process, nullptr, TRUE))
    {
        char buffer[sizeof(SYMBOL_INFO) + MAX_SYM_NAME + 4] = {};
        PSYMBOL_INFO info = reinterpret_cast<PSYMBOL_INFO>(buffer);
        info->SizeOfStruct = sizeof(SYMBOL_INFO);
        info->MaxNameLen = MAX_SYM_NAME;
        DWORD64 displacement = 0;
        if (SymFromAddr(process, (DWORD64)(UINT_PTR)fault, &displacement, info))
            fprintf(f, "SYMBOL %s +0x%llx\n", info->Name, (unsigned long long)displacement);
        else
            fprintf(f, "SYMBOL_LOOKUP_FAILED winerr=%lu\n", GetLastError());
        IMAGEHLP_LINE64 source = {};
        source.SizeOfStruct = sizeof(source);
        DWORD linediff = 0;
        if (SymGetLineFromAddr64(process, (DWORD64)(UINT_PTR)fault, &linediff, &source))
            fprintf(f, "SOURCE %s:%lu\n", source.FileName, (unsigned long)source.LineNumber);
        SymCleanup(process);
    }
    fflush(f);
    fclose(f);
    return EXCEPTION_CONTINUE_SEARCH; // Original exception semantics unchanged.
}
'''
def patch(root: Path) -> Path:
    target=root/"src/win32/win_main.cpp"
    s=target.read_text(encoding="utf-8")
    if s.count(MARKER)!=1:
        raise ValueError("Cannot find unique WinMain signature")
    if "Z2026_LogFirstBreakpoint" in s:
        raise ValueError("Already instrumented")
    s=HEADER+"\n"+s.replace(MARKER,MARKER+"\n    AddVectoredExceptionHandler(1, Z2026_LogFirstBreakpoint);",1)
    target.write_text(s,encoding="utf-8")
    # The original DB_Thread uses a deliberate __debugbreak() after its
    # setjmp error recovery path. Log the underlying Com_Error message BEFORE
    # that breakpoint, without suppressing or consuming it.
    db_file = root / "src/database/db_registry.cpp"
    db_source = db_file.read_text(encoding="utf-8")
    db_needle = "        Profile_Recover(1);\n#ifdef __llvm__"
    if db_source.count(db_needle) != 1:
        raise ValueError("Cannot locate unique database setjmp recovery path")
    db_payload = """        Profile_Recover(1);
        {
            FILE *diagnostic = nullptr;
            if (fopen_s(&diagnostic, "kisak-database-diagnostic.txt", "a") == 0 && diagnostic) {
                fprintf(diagnostic, "DB_THREAD_RECOVERY error=%s\\n", com_errorMessage);
                fclose(diagnostic);
            }
        }
#ifdef __llvm__"""
    db_source = "#include <cstdio>\nextern char com_errorMessage[4096];\n" + db_source.replace(db_needle, db_payload, 1)
    db_file.write_text(db_source, encoding="utf-8")
    # Observe an actual CL_Connect_f invocation without changing authentication,
    # player profile checks, or packet behavior. This is a disposable copy.
    cl_file = root / "src/client_mp/cl_main_pc_mp.cpp"
    client = cl_file.read_text(encoding="utf-8")
    entry = "void __cdecl CL_Connect_f()\n{"
    if client.count(entry) != 1:
        raise ValueError("Cannot locate unique MP client connect function")
    trace_helper = r"""
// Z2026 local-only diagnostic. No nickname, CD key or authentication details.
#include <cstdio>
static void Z2026_TraceConnect(int argc, int state)
{
    FILE* out = nullptr;
    if (fopen_s(&out, "kisak-client-connect-diagnostic.txt", "a") == 0 && out)
    {
        fprintf(out, "CL_CONNECT_ENTER argc=%d state=%d\n", argc, state);
        fclose(out);
    }
}
static bool Z2026_TraceProfile(bool hasProfile)
{
    FILE* out = nullptr;
    if (fopen_s(&out, "kisak-client-connect-diagnostic.txt", "a") == 0 && out)
    {
        fprintf(out, "CL_CONNECT_PROFILE_CHECK has_profile=%d\n", int(hasProfile));
        fclose(out);
    }
    return hasProfile; // Preserve upstream behavior exactly.
}
static void Z2026_TraceStage(const char* stage, int detail)
{
    FILE* out = nullptr;
    if (fopen_s(&out, "kisak-client-connect-diagnostic.txt", "a") == 0 && out)
    {
        fprintf(out, "CL_CONNECT_STAGE %s detail=%d\n", stage, detail);
        fclose(out);
    }
}
"""
    start = client.index(entry)
    profile_marker = "if (Com_HasPlayerProfile())"
    following = client.find(profile_marker, start)
    if following < 0 or following - start > 2800:
        raise ValueError("Unable to locate connect profile gate")
    client = (trace_helper + "\n" +
        client[:start].replace(entry, entry, 1) +
        client[start:].replace(entry, entry +
            "\n    Z2026_TraceConnect(Cmd_Argc(), (int)clientUIActives[0].connectionState);", 1))
    profile_pos = client.index(profile_marker, client.index(entry))
    client = client[:profile_pos] + client[profile_pos:].replace(
        profile_marker, "if (Z2026_TraceProfile(Com_HasPlayerProfile()))", 1)
    # Fine-grained trace: previous run proved CL_Connect_f was called, but
    # never reached the profile check. Record progress before/after the map
    # tick, name resolver, and the *unchanged* local/Steam authentication gate.
    # These probes report state; they neither short-circuit Steam nor weaken
    # connection validation.
    segment_start = client.index(entry)
    segment_end = client.index("// This is called by the Client", segment_start)
    segment = client[segment_start:segment_end]
    checkpoints = (
        ("            SV_Frame(0);", """            Z2026_TraceStage("SV_FRAME_ENTER", 0);
            SV_Frame(0);
            Z2026_TraceStage("SV_FRAME_RETURN", 0);"""),
        ("            if (NET_StringToAdr(cls.servername, &clc->serverAddress))",
         """            Z2026_TraceStage("NET_RESOLVE_ENTER", 0);
            if (NET_StringToAdr(cls.servername, &clc->serverAddress))"""),
        ("                if (NET_IsLocalAddress(clc->serverAddress) || CL_CDKeyValidate(clc->serverAddress))",
         """                Z2026_TraceStage("AUTH_GATE_ENTER", (int)clc->serverAddress.type);
                Z2026_TraceStage("LOCAL_CLASSIFICATION", NET_IsLocalAddress(clc->serverAddress) ? 1 : 0);
                if (NET_IsLocalAddress(clc->serverAddress) || CL_CDKeyValidate(clc->serverAddress))"""),
    )
    for needle, replacement in checkpoints:
        if segment.count(needle) != 1:
            raise ValueError("Unable to locate unique connect stage: " + needle)
        segment = segment.replace(needle, replacement, 1)
    client = client[:segment_start] + segment + client[segment_end:]

    # The address '127.0.0.1' is NA_IP, whereas NET_IsLocalAddress
    # recognizes only NA_LOOPBACK / NA_BOT in this upstream source.
    # Detect whether the subsequent Steam ticket call returns, without
    # pretending that an IPv4 loopback address has passed authentication.
    auth_start = client.index("bool __cdecl CL_CDKeyValidate(netadr_t addr)")
    auth_end = client.index("//bool __cdecl CL_CDKeyValidate(const char *key", auth_start)
    auth_segment = client[auth_start:auth_end]
    auth_return = "    return Steam_UpdateClientAuthTicket(addr);"
    if auth_segment.count(auth_return) != 1:
        raise ValueError("Unable to locate unique Windows Steam ticket return")
    auth_segment = auth_segment.replace(
        auth_return,
        """    Z2026_TraceStage("STEAM_TICKET_ENTER", 0);
    const bool ticketOk = Steam_UpdateClientAuthTicket(addr);
    Z2026_TraceStage("STEAM_TICKET_RETURN", ticketOk ? 1 : 0);
    return ticketOk;""",
        1
    )
    client = client[:auth_start] + auth_segment + client[auth_end:]
    cl_file.write_text(client, encoding="utf-8")
    return target

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source-copy",type=Path,required=True)
    a=p.parse_args()
    out=patch(a.source_copy)
    print("Instrumented ephemeral source only:",out)
