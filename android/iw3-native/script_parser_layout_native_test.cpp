#include <cstddef>
#include <script/scr_parser.h>
#include <script/scr_main.h>
#include <script/scr_vm.h>
#include <script/scr_evaluate.h>
#include <script/scr_compiler.h>
#include <win32/win_input.h>

static_assert(sizeof(void *) == 8, "This gate must compile for Android ARM64");
static_assert(sizeof(scrVarPub_t) == 0x200A0);
static_assert(offsetof(scrVarPub_t, programHunkUser) == 80);
static_assert(offsetof(scrVarPub_t, varUsagePos) == 0x20088);
static_assert(sizeof(scrVmGlob_t) == 0x2048);
static_assert(sizeof(scrVmPub_t) == 0x8540);
static_assert(sizeof(scrVmDebugPub_t) == 0x26410);
static_assert(sizeof(debugger_sval_s) == 0x8);
static_assert(sizeof(sval_u) == 0x8);
static_assert(sizeof(ScriptExpression_t) == 0x18);
static_assert(sizeof(Scr_Breakpoint) == 0x30);
static_assert(sizeof(Scr_WatchElement_s) == 0xA0);
static_assert(sizeof(Scr_OpcodeList_s) == 0x10);
static_assert(sizeof(Scr_WatchElementNode_s) == 0x10);
static_assert(sizeof(Scr_WatchElementDoubleNode_t) == 0x10);
static_assert(sizeof(scrDebuggerGlob_t) == 0x368);
static_assert(sizeof(ArchivedCanonicalStringInfo) == 0x10);
static_assert(sizeof(scrEvaluateGlob_t) == 0x20);
static_assert(sizeof(CaseStatementInfo) == 0x20);
static_assert(sizeof(BreakStatementInfo) == 0x18);
static_assert(sizeof(ContinueStatementInfo) == 0x18);
static_assert(sizeof(VariableCompileValue) == 0x18);
static_assert(sizeof(scrCompileGlob_t) == 0x390);


static_assert(sizeof(OpcodeLookup) == 0x20);
static_assert(sizeof(SourceBufferInfo) == 56);
static_assert(sizeof(SaveSourceBufferInfo) == 0x10);
static_assert(sizeof(scrParserGlob_t) == 0x50);
static_assert(sizeof(scrParserPub_t) == 0x20);
static_assert(offsetof(scrParserGlob_t, currentCodePos) == 40);
static_assert(offsetof(scrParserGlob_t, saveSourceBufferLookup) == 56);
static_assert(offsetof(scrParserPub_t, scriptfilename) == 16);
static_assert(offsetof(scrParserPub_t, sourceBuf) == 24);

extern "C" int iw3_script_parser_layout_abi_anchor()
{
    return static_cast<int>(sizeof(scrParserGlob_t) + sizeof(scrParserPub_t));
}
