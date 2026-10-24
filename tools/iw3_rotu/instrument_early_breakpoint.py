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
    db_needle = "        Profile_Recover(1);\\n#ifdef __llvm__"
    if db_source.count(db_needle) != 1:
        raise ValueError("Cannot locate unique database setjmp recovery path")
    db_payload = (
        "        Profile_Recover(1);\\n"
        "        {\\n"
        "            FILE *diagnostic = nullptr;\\n"
        "            if (fopen_s(&diagnostic, \\"kisak-database-diagnostic.txt\\", \\"a\\") == 0 && diagnostic) {\\n"
        "                fprintf(diagnostic, \\"DB_THREAD_RECOVERY error=%s\\\\n\\", com_errorMessage);\\n"
        "                fclose(diagnostic);\\n"
        "            }\\n"
        "        }\\n"
        "#ifdef __llvm__"
    )
    db_source = "#include <cstdio>\\nextern char com_errorMessage[4096];\\n" + db_source.replace(db_needle, db_payload, 1)
    db_file.write_text(db_source, encoding="utf-8")
    return target

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source-copy",type=Path,required=True)
    a=p.parse_args()
    out=patch(a.source_copy)
    print("Instrumented ephemeral source only:",out)
