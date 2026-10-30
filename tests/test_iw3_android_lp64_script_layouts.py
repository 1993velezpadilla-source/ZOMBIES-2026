"""Regression coverage for LP64 layouts pulled in by original IW3 frame code.

These assertions permit native-width compilation only. They do not claim that
the original script VM or the full Android runtime has been linked/executed.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD/src"


class Lp64ScriptLayoutTests(unittest.TestCase):
    def test_pointer_bearing_script_records_keep_win32_and_lp64_assertions(self):
        header = (ENGINE / "script/scr_variable.h").read_text(encoding="utf-8")
        self.assertIn("KISAK_SCRIPT_POINTER_LAYOUT_LP64", header)
        expected = {
            "VariableStackBuffer": ("0x10", "0xC"),
            "VariableUnion": ("0x8", "0x4"),
            "VariableValue": ("0x10", "0x8"),
            "VariableValueInternal_u": ("0x8", "0x4"),
            "VariableValueInternal": ("0x18", "0x10"),
            "scrVarDebugPub_t": ("0x140008", "0xE0004"),
            "scrVarGlob_t": ("0x240000", "0x180000"),
            "scr_classStruct_t": ("0x10", "0xC"),
            "VariableDebugInfo": ("0x20", "0x10"),
            "ThreadDebugInfo": ("0x110", "0x8C"),
        }
        for name, (lp64_size, win32_size) in expected.items():
            with self.subTest(name=name):
                self.assertIn(f"sizeof({name}) == {lp64_size}", header)
                self.assertIn(f"sizeof({name}) == {win32_size}", header)
        self.assertIn("#undef KISAK_SCRIPT_POINTER_LAYOUT_LP64", header)

    def test_network_address_alignment_is_standard_cpp(self):
        header = (ENGINE / "qcommon/net_chan.h").read_text(encoding="utf-8")
        self.assertIn("struct alignas(4) netadr_t", header)
        self.assertNotIn("struct __declspec(align(4)) netadr_t", header)

    def test_math_header_avoids_android_posix_random_collision(self):
        header = (ENGINE / "universal/com_math.h").read_text(encoding="utf-8")
        source = (ENGINE / "universal/com_math.cpp").read_text(encoding="utf-8")
        self.assertIn("float __cdecl Com_Random();", header)
        self.assertNotIn("float __cdecl random();", header)
        self.assertIn("float __cdecl Com_Random()", source)
        self.assertIn("return (Com_Random() * 2.0 - 1.0);", source)
        self.assertIn("#define KISAK_FORCEINLINE static inline __attribute__((always_inline))", header)

    def test_no_other_engine_callsite_depends_on_posix_random_name(self):
        # Strip comments first so a note in source does not count as a callsite.
        pattern = re.compile(r"\brandom\s*\(")
        ignored = {
            ENGINE / "universal/com_math.cpp",
            ENGINE / "universal/com_math.h",
        }
        hits = []
        for path in ENGINE.rglob("*"):
            if path.suffix not in {".c", ".cc", ".cpp", ".h", ".hpp", ".inl"} or path in ignored:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            text = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
            if pattern.search(text):
                hits.append(str(path.relative_to(ROOT)))
        self.assertEqual(hits, [], "Rename these engine callsites to the portable engine RNG: " + ", ".join(hits))



    def test_original_parser_pointer_bearing_runtime_layouts_cover_win32_and_lp64(self):
        header = (ENGINE / "script/scr_parser.h").read_text(encoding="utf-8")
        expected = {
            "OpcodeLookup": ("0x20", "0x18"),
            "SourceBufferInfo": ("56", "44"),
            "SaveSourceBufferInfo": ("0x10", "0x8"),
            "scrParserGlob_t": ("0x50", "0x34"),
            "scrParserPub_t": ("0x20", "0x10"),
        }
        for name, (lp64_size, win32_size) in expected.items():
            with self.subTest(name=name):
                self.assertIn(
                    f"sizeof({name}) == (sizeof(void *) == 8 ? {lp64_size} : {win32_size})",
                    header,
                )

    def test_original_parser_tracker_uses_native_struct_sizes_not_win32_literals(self):
        source = (ENGINE / "script/scr_parser.cpp").read_text(encoding="utf-8")
        start = source.index("void __cdecl TRACK_scr_parser()")
        end = source.index("void __cdecl Scr_InitOpcodeLookup()", start)
        body = source[start:end]
        self.assertIn('track_static_alloc_internal(&scrParserGlob, sizeof(scrParserGlob), "scrParserGlob", 7);', body)
        self.assertIn('track_static_alloc_internal(&scrParserPub, sizeof(scrParserPub), "scrParserPub", 7);', body)
        self.assertNotRegex(body, r"track_static_alloc_internal\(&scrParserGlob,\s*52")
        self.assertNotRegex(body, r"track_static_alloc_internal\(&scrParserPub,\s*16")

    def test_android_ndk_compiles_the_original_parser_header_layout_fixture(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn("iw3_sp_script_parser_layout_full_compile OBJECT", cmake)
        self.assertIn("script_parser_layout_native_test.cpp", cmake)
        fixture = (ROOT / "android/iw3-native/script_parser_layout_native_test.cpp").read_text(encoding="utf-8")
        for assertion in (
            "sizeof(OpcodeLookup) == 0x20",
            "sizeof(SourceBufferInfo) == 56",
            "sizeof(SaveSourceBufferInfo) == 0x10",
            "sizeof(scrParserGlob_t) == 0x50",
            "sizeof(scrParserPub_t) == 0x20",
            "offsetof(scrParserGlob_t, currentCodePos) == 40",
            "offsetof(scrParserPub_t, scriptfilename) == 16",
        ):
            self.assertIn(assertion, fixture)


    def test_original_script_variable_publication_has_win32_and_lp64_layouts(self):
        header = (ENGINE / "script/scr_main.h").read_text(encoding="utf-8")
        self.assertIn(
            "sizeof(scrVarPub_t) == (sizeof(void *) == 8 ? 0x200A0 : 0x2007C)",
            header,
        )

    def test_original_script_vm_static_tracking_uses_native_sizes(self):
        source = (ENGINE / "script/scr_vm.cpp").read_text(encoding="utf-8")
        start = source.index("void __cdecl TRACK_scr_vm()")
        end = source.index("void __cdecl Scr_ClearErrorMessage()", start)
        body = source[start:end]
        for expression in (
            "sizeof(scrVmGlob)",
            "sizeof(scrVmPub)",
            "sizeof(g_script_error)",
            "sizeof(scrVmDebugPub)",
        ):
            self.assertIn(expression, body)
        for win32_literal in ("8232", "17192", "2112", "147984"):
            self.assertNotIn(win32_literal, body)

    def test_android_ndk_builds_complete_original_script_vm_translation_unit(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn("iw3_sp_script_vm_full_compile OBJECT", cmake)
        self.assertIn('"${IW3_ENGINE_SOURCE_ROOT}/script/scr_vm.cpp"', cmake)
        self.assertIn("target_compile_definitions(iw3_sp_script_vm_full_compile PRIVATE KISAK_SP=1)", cmake)
        self.assertIn("IW3_CLIENT_RUNTIME_LINKED=false", (ROOT / "docs/IW3_ANDROID_PHASE_EA_SCRIPT_VM_LP64_TRACKING.md").read_text(encoding="utf-8"))


    def test_original_script_vm_compile_gate_is_not_linked_into_jni_diagnostic(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        target_start = cmake.index("add_library(iw3_sp_script_vm_full_compile OBJECT")
        target_end = cmake.index("endif()", target_start)
        target_block = cmake[target_start:target_end]
        self.assertIn("script/scr_vm.cpp", target_block)
        self.assertNotIn("iw3_sp_script_vm_full_compile", cmake[cmake.index("add_library(iw3_sp_math SHARED"):])

    def test_original_script_yacc_header_uses_abi_neutral_allocator_pointer(self):
        header = (ENGINE / "script/scr_yacc.h").read_text(encoding="utf-8")
        self.assertNotIn("#include <Windows.h>", header)
        self.assertIn("void *__cdecl yy_flex_alloc(uint32_t size);", header)
        self.assertNotIn("LPVOID __cdecl yy_flex_alloc", header)



    def test_original_vm_debugger_evaluator_and_compiler_layouts_are_lp64_aware(self):
        expected = {
            "script/scr_debugger.h": (
                "sizeof(debugger_sval_s) == (sizeof(void *) == 8 ? 0x8 : 0x4)",
                "sizeof(sval_u) == (sizeof(void *) == 8 ? 0x8 : 0x4)",
                "sizeof(ScriptExpression_t) == (sizeof(void *) == 8 ? 0x18 : 0xC)",
                "sizeof(Scr_Breakpoint) == (sizeof(void *) == 8 ? 0x30 : 0x1C)",
                "sizeof(Scr_WatchElement_s) == (sizeof(void *) == 8 ? 0xA0 : 0x64)",
                "sizeof(scrDebuggerGlob_t) == (sizeof(void *) == 8 ? 0x368 : 0x2B8)",
            ),
            "script/scr_evaluate.h": (
                "sizeof(ArchivedCanonicalStringInfo) == (sizeof(void *) == 8 ? 0x10 : 0x8)",
                "sizeof(scrEvaluateGlob_t) == (sizeof(void *) == 8 ? 0x20 : 0x10)",
            ),
            "script/scr_compiler.h": (
                "sizeof(CaseStatementInfo) == (sizeof(void *) == 8 ? 0x20 : 0x10)",
                "sizeof(BreakStatementInfo) == (sizeof(void *) == 8 ? 0x18 : 0xC)",
                "sizeof(ContinueStatementInfo) == (sizeof(void *) == 8 ? 0x18 : 0xC)",
                "sizeof(VariableCompileValue) == (sizeof(void *) == 8 ? 0x18 : 0xC)",
                "sizeof(scrCompileGlob_t) == (sizeof(void *) == 8 ? 0x390 : 0x1D8)",
            ),
        }
        for relative_path, assertions in expected.items():
            header = (ENGINE / relative_path).read_text(encoding="utf-8")
            for assertion in assertions:
                with self.subTest(path=relative_path, assertion=assertion):
                    self.assertIn(assertion, header)

    def test_script_vm_static_tracking_uses_native_object_sizes(self):
        source = (ENGINE / "script/scr_vm.cpp").read_text(encoding="utf-8")
        start = source.index("void __cdecl TRACK_scr_vm()")
        end = source.index("void __cdecl Scr_ClearErrorMessage()", start)
        body = source[start:end]
        for expression in ("sizeof(scrVmGlob)", "sizeof(scrVmPub)", "sizeof(g_script_error)", "sizeof(scrVmDebugPub)"):
            self.assertIn(expression, body)
        for win32_size in ("8232", "17192", "2112", "147984"):
            self.assertNotIn(win32_size, body)

    def test_script_vm_diagnostic_logging_is_format_safe_and_null_safe(self):
        source = (ENGINE / "script/scr_vm.cpp").read_text(encoding="utf-8")
        self.assertIn("if (!logFile)", source)
        self.assertIn("fputs(buffer, logFile);", source)
        self.assertNotIn("fprintf(logFile, buffer)", source)
        self.assertIn("void __cdecl Sys_Error(const char *error, ...);", source)

    def test_android_input_header_does_not_require_win32_tagpoint(self):
        header = (ENGINE / "win32/win_input.h").read_text(encoding="utf-8")
        self.assertIn("#if !defined(__ANDROID__)\nvoid __cdecl IN_SetCursorPos(tagPOINT x);\n#endif", header)

    def test_arm64_fixture_asserts_script_vm_live_layouts(self):
        fixture = (ROOT / "android/iw3-native/script_parser_layout_native_test.cpp").read_text(encoding="utf-8")
        for assertion in (
            "sizeof(scrVarPub_t) == 0x200A0",
            "sizeof(scrVmGlob_t) == 0x2048",
            "sizeof(scrVmPub_t) == 0x8540",
            "sizeof(scrVmDebugPub_t) == 0x26410",
            "sizeof(scrDebuggerGlob_t) == 0x368",
            "sizeof(scrCompileGlob_t) == 0x390",
        ):
            self.assertIn(assertion, fixture)



    def test_script_vm_profiling_uses_arm64_architectural_counter(self):
        source = (ENGINE / "script/scr_vm.cpp").read_text(encoding="utf-8")
        self.assertIn("mrs %0, cntvct_el0", source)
        self.assertIn("static inline uint64_t IW3_ScriptProfileCounter()", source)
        self.assertIn("return __rdtsc();", source)
        self.assertNotIn("time = __rdtsc();", source)
        self.assertNotIn("timeSpent = __rdtsc() - time;", source)

    def test_original_frame_script_vm_scheduler_edges_are_relocatably_audited(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        frame = (ENGINE / "game/g_runframe.cpp").read_text(encoding="utf-8")
        vm = (ENGINE / "script/scr_vm.cpp").read_text(encoding="utf-8")
        self.assertIn("Scr_RunCurrentThreads();", frame)
        self.assertIn("Scr_IncTime();", frame)
        self.assertIn("void __cdecl Scr_RunCurrentThreads()", vm)
        self.assertIn("void __cdecl Scr_IncTime()", vm)
        self.assertIn('ld.lld" -r "$frame_object" "$script_vm_object"', workflow)
        self.assertIn("iw3-frame-script-vm-before-undefined.txt", workflow)
        self.assertIn("iw3-frame-script-vm-undefined.txt", workflow)
        self.assertIn("IW3_ORIGINAL_FRAME_SCRIPT_VM_RELOCATABLE_LINK_PASS", workflow)
        self.assertIn("IW3_FRAME_SCRIPT_VM_RUNTIME_LINKED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)
        self.assertIn("grep -F 'G_UpdatePlayer'", workflow)
        self.assertIn("G_RunFrame(ServerFrameExtent, int)", workflow)
        self.assertIn("iw3-frame-original-elf.txt", workflow)
        self.assertIn("iw3-original-frame-plus-script-vm-arm64.o", workflow)
        self.assertNotIn('cp "$frame_vm_combined" "$RUNNER_TEMP/iw3-original-frame-plus-script-vm-arm64.o"', workflow)



if __name__ == "__main__":
    unittest.main()
