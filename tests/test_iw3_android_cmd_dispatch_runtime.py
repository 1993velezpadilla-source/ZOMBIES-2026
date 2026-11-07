"""Execute original command bodies with instrumented unit-test service boundaries.

This is a host regression, not Cmd_Init/Android/gameplay evidence. Generated
test translation units are temporary and are never linked into JNI.
"""
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source
from tools.iw3_android.prepare_real_engine_cmd_args import prepare as prepare_args
from tools.iw3_android.prepare_real_engine_cmd_tokenizer import prepare as prepare_tokens

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalCommandDispatchRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        work = Path(cls.temp.name)
        source = (ENGINE / "src/qcommon/cmd.cpp").read_text()
        prepare_args(ENGINE, work / "args.cpp")
        prepare_tokens(ENGINE, work / "tokens.cpp")
        signatures = (
            "static void Cmd_ResetArgs(CmdArgs* args, CmdArgsPrivate* argsPriv)",
            "void Cmd_AddCommandInternal(const char* cmdName, void(__cdecl* function)(), cmd_function_s* allocedCmd)",
            "cmd_function_s* Cmd_FindCommand(const char* cmdName)",
            "void __cdecl Cmd_RemoveCommand(const char *cmdName)",
            "void __cdecl Cmd_Shutdown()",
            "void __cdecl Cmd_ComErrorCleanup()",
            "void __cdecl Cmd_ExecuteSingleCommand(int32_t  localClientNum, int32_t  controllerIndex, char *text)",
        )
        state_names = (
            "cmd_functions", "sv_cmd_functions", "sv_cmd_args",
            "sv_cmd_argsPrivate", "cmd_insideCBufExecute",
        )
        states = []
        for name in state_names:
            matches = re.findall(r"(?m)^(?:static )?(?:cmd_function_s\s*\*|CmdArgsPrivate|CmdArgs|bool)\s*"
                                 + name + r"(?:\[1\])?(?: = NULL)?;", source)
            if len(matches) != 1:
                raise AssertionError(f"Expected one original declaration for {name}: {matches}")
            states.append(matches[0])
        shared = (ENGINE / "src/universal/q_shared.cpp").read_text()
        strings = [function_source(shared, sig) for sig in (
            "bool I_isupper(int c)",
            "int I_strnicmp(const char* s0, const char* s1, int n)",
            "int I_stricmp(const char* s0, const char* s1)",
        )]
        fixture = (ROOT / "tests/fixtures/iw3_cmd_dispatch_runtime.cpp").read_text()
        generated = fixture.replace("// ORIGINAL_COMMAND_BODIES", "\n".join(
            states + strings + [function_source(source, sig) for sig in signatures]))
        (work / "dispatch.cpp").write_text(generated)
        cls.binary = work / "dispatch"
        command = [os.environ.get("CXX", "g++"), "-std=c++20", "-DKISAK_SP=1",
                   "-DRELEASE_ASSERTS=1", "-UNDEBUG", "-g", "-O1",
                   "-I", str(ENGINE / "src"), "-I", str(ENGINE / "deps"),
                   *shlex.split(os.environ.get("IW3_CMD_TEST_CXXFLAGS", "")),
                   str(work / "dispatch.cpp"), "-o", str(cls.binary)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def run_case(self, case):
        result = subprocess.run([str(self.binary), case], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_empty_registry_falls_back_without_crashing(self):
        self.run_case("empty")

    def test_single_registered_command_executes(self):
        self.run_case("single")

    def test_head_middle_and_tail_dispatch(self):
        self.run_case("list")

    def test_nested_command_preserves_outer_arguments(self):
        self.run_case("nested")

    def test_unknown_command_and_empty_input_cleanup(self):
        self.run_case("fallback")
