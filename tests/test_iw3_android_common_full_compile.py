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
            self.assertRegex(source, r"#else\\s*#include <d3d9\\.h>\\s*#endif")

    def test_original_bootstrap_translation_unit_contains_engine_entrypoints(self):
        source = (ROOT / "third_party/KisakCOD/src/qcommon/common.cpp").read_text(encoding="utf-8")
        self.assertRegex(source, r"void\s+__cdecl\s+Com_Init\s*\(")
        self.assertRegex(source, r"void\s+__cdecl\s+Com_Frame\s*\(")
        self.assertIn("FS_InitFilesystem()", source)
        self.assertIn("Com_InitXAssets()", source)


if __name__ == "__main__":
    unittest.main()
