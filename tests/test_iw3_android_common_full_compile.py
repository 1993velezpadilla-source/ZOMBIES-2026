from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OriginalCommonBootstrapCompileGateTests(unittest.TestCase):
    def test_android_target_compiles_the_complete_original_common_translation_unit(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        self.assertRegex(
            cmake,
            r"add_library\(iw3_sp_common_full_compile OBJECT\s+"
            r'"\$\{IW3_ENGINE_SOURCE_ROOT\}/qcommon/common\.cpp"\s*\)',
        )

    def test_gate_uses_real_single_player_headers_and_not_the_jni_diagnostic(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        start = cmake.index("add_library(iw3_sp_common_full_compile OBJECT")
        end = cmake.index("endif()", start)
        block = cmake[start:end]
        preamble = cmake[cmake.rfind("# Compile the complete original Com_Init/Com_Frame", 0, start):start]
        self.assertIn("KISAK_SP=1", block)
        self.assertIn("IW3_ENGINE_SOURCE_ROOT}/../deps", block)
        self.assertIn("NOT linked into the JNI diagnostic APK", preamble)
        self.assertNotIn("target_sources(iw3_sp_math", block)

    def test_ci_verifies_aarch64_symbols_and_archives_the_original_bootstrap_object(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("CMakeFiles/iw3_sp_common_full_compile.dir", workflow)
        self.assertIn("IW3_ORIGINAL_COMMON_BOOTSTRAP_AARCH64_OBJECT_PASS", workflow)
        self.assertIn("Com_Init(char*)", workflow)
        self.assertIn("Com_Frame()", workflow)
        self.assertIn("iw3-common-full-undefined.txt", workflow)


    def test_shared_renderer_headers_use_opaque_d3d9_types_on_android(self):
        for relative in (
            "third_party/KisakCOD/src/gfx_d3d/rb_backend.h",
            "third_party/KisakCOD/src/gfx_d3d/r_buffers.h",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("#if defined(__ANDROID__)", source)
            self.assertIn('#include "r_d3d9_opaque.h"', source)
            self.assertIn("#include <d3d9.h>", source)
            self.assertIn("#else\n#include <d3d9.h>\n#endif", source)

    def test_android_common_bootstrap_excludes_only_optional_desktop_script_debugger(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        start = cmake.index("add_library(iw3_sp_common_full_compile OBJECT")
        end = cmake.index("endif()", start)
        self.assertIn("IW3_ANDROID_DISABLE_SCRIPT_DEBUGGER=1", cmake[start:end])

        common = (ROOT / "third_party/KisakCOD/src/qcommon/common.cpp").read_text(encoding="utf-8")
        vm = (ROOT / "third_party/KisakCOD/src/script/scr_vm.h").read_text(encoding="utf-8")
        self.assertIn("#if !defined(IW3_ANDROID_DISABLE_SCRIPT_DEBUGGER)\n#include <script/scr_debugger.h>\n#endif", common)
        self.assertIn("#if !defined(IW3_ANDROID_DISABLE_SCRIPT_DEBUGGER)\n#include \"scr_debugger.h\"\n#endif", vm)
        for call in ("Scr_UpdateDebugSocket()", "Scr_CanDrawScript()", "Scr_DrawScript()", "Scr_UpdateRemoteDebugger()"):
            self.assertIn(call, common)
        self.assertIn("newEvent = 0;", common)

    def test_android_common_uses_bionic_crt_time_and_prefetch_services(self):
        source = (ROOT / "third_party/KisakCOD/src/qcommon/common.cpp").read_text(encoding="utf-8")
        self.assertIn("#if defined(__ANDROID__)", source)
        self.assertIn("#define _vsnprintf vsnprintf", source)
        self.assertIn("#define _snprintf snprintf", source)
        self.assertIn("jmp_buf *value = (jmp_buf *)Sys_GetValue(2);", source)
        self.assertIn("longjmp(*value, -1);", source)
        self.assertNotIn("longjmp((int*)value, -1);", source)
        self.assertIn('__builtin_prefetch(s, 0, 0);', source)
        self.assertIn("time_t aclock;", source)
        self.assertIn("time(&aclock);", source)
        self.assertIn("newtime = localtime(&aclock);", source)
        self.assertIn('#define CPUSTRING "android-arm64"', source)

    def test_android_server_demo_file_type_alias_matches_bionic_FILE(self):
        server = (ROOT / "third_party/KisakCOD/src/server/server.h").read_text(encoding="utf-8")
        demo = (ROOT / "third_party/KisakCOD/src/server/sv_demo.cpp").read_text(encoding="utf-8")
        self.assertIn("#if defined(__ANDROID__)", server)
        self.assertIn("#include <stdio.h>", server)
        self.assertIn("using _iobuf = FILE;", server)
        self.assertIn("FILE *g_fileMarkHistory;", demo)
        self.assertIn("_iobuf *__cdecl SV_DemoOpenFile", demo)

    def test_original_bootstrap_translation_unit_contains_engine_entrypoints(self):
        source = (ROOT / "third_party/KisakCOD/src/qcommon/common.cpp").read_text(encoding="utf-8")
        self.assertRegex(source, r"void\s+__cdecl\s+Com_Init\s*\(")
        self.assertRegex(source, r"void\s+__cdecl\s+Com_Frame\s*\(")
        self.assertIn("FS_InitFilesystem()", source)
        self.assertIn("Com_InitXAssets()", source)


if __name__ == "__main__":
    unittest.main()
