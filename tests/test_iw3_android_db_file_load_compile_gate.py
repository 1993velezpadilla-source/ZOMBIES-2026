"""Ensure the complete original IW3 FastFile loader is compiled for Android ARM64."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATABASE_H = ROOT / "third_party/KisakCOD/src/database/database.h"
LOADER_CPP = ROOT / "third_party/KisakCOD/src/database/db_file_load.cpp"
RENDERER_COMPAT = ROOT / "third_party/KisakCOD/src/database/db_fastfile_android_renderer_compat.h"
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"
WORKFLOW = ROOT / ".github/workflows/iw3-original-native-android.yml"


class OriginalDbFileLoadCompileGateTests(unittest.TestCase):
    def test_database_header_does_not_import_win32_local_on_android(self):
        source = DATABASE_H.read_text(encoding="utf-8")
        guard = source.index("#if !defined(__ANDROID__)")
        include = source.index('#include <win32/win_local.h>')
        end_guard = source.index("#endif", guard)
        self.assertLess(guard, include)
        self.assertLess(include, end_guard)
        self.assertIn("#if !defined(__ANDROID__)\nvoid __stdcall DB_FileReadCompletion", source)

    def test_full_loader_uses_android_declarations_not_d3d_headers(self):
        source = LOADER_CPP.read_text(encoding="utf-8")
        android_branch = source.index("#if defined(__ANDROID__)")
        compat_include = source.index('#include "db_fastfile_android_renderer_compat.h"')
        windows_branch = source.index("#else", compat_include)
        d3d_include = source.index("#include <gfx_d3d/r_image.h>")
        self.assertLess(android_branch, compat_include)
        self.assertLess(compat_include, windows_branch)
        self.assertGreater(d3d_include, windows_branch)
        self.assertIn("#include <unistd.h>", source)

    def test_renderer_boundary_contains_declarations_only(self):
        source = RENDERER_COMPAT.read_text(encoding="utf-8")
        for symbol in (
            "R_DelayLoadImage(XAssetHeader header)",
            "R_FinishStaticVertexBuffer(IDirect3DVertexBuffer9 *buffer)",
            "R_FinishStaticIndexBuffer(IDirect3DIndexBuffer9 *buffer)",
        ):
            self.assertIn(symbol + ";", source)
        self.assertNotIn("{", source)
        self.assertNotIn("inline", source)

    def test_cmake_compiles_the_complete_original_loader_translation_unit(self):
        source = CMAKE.read_text(encoding="utf-8")
        target = source.index("add_library(iw3_sp_db_file_load_full_compile OBJECT")
        original = source.index('"${IW3_ENGINE_SOURCE_ROOT}/database/db_file_load.cpp"', target)
        self.assertLess(target, original)
        self.assertIn("target_compile_definitions(iw3_sp_db_file_load_full_compile PRIVATE KISAK_SP=1)", source)
        self.assertIn("target_compile_options(iw3_sp_db_file_load_full_compile PRIVATE", source)
        self.assertIn("-fms-extensions -Wall -Wextra", source)

    def test_arm64_gate_checks_real_loader_symbol_and_unresolved_renderer_edges(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        for marker in (
            "iw3_sp_db_file_load_full_compile.dir",
            "IW3_ORIGINAL_DB_FILE_LOAD_AARCH64_OBJECT_PASS",
            "DB_LoadXFileInternal()",
            "R_DelayLoadImage",
            "R_FinishStaticVertexBuffer",
            "R_FinishStaticIndexBuffer",
            "IW3_DB_FILE_LOAD_RUNTIME_LINKED=false",
            "IW3_PLAYABLE_APK=false",
        ):
            self.assertIn(marker, source)

    def test_android_lp64_asset_layouts_are_not_mistaken_for_win32_disk_layouts(self):
        bsp = (ROOT / "third_party/KisakCOD/src/gfx_d3d/r_bsp.h").read_text(encoding="utf-8")
        sound = (ROOT / "third_party/KisakCOD/src/sound/snd_public.h").read_text(encoding="utf-8")
        self.assertIn("#if defined(__ANDROID__)\n// Native LP64 engine layout.", bsp)
        self.assertIn("static_assert(sizeof(GfxWorld) == 1032);", bsp)
        for declaration in (
            "static_assert(sizeof(LoadedSound) == 64);",
            "static_assert(sizeof(SndCurve) == 80);",
            "static_assert(sizeof(snd_alias_t) == 128);",
            "static_assert(sizeof(snd_alias_list_t) == 24);",
        ):
            self.assertIn(declaration, sound)
        self.assertIn("typedef struct HWND__ *HWND;", sound)

    def test_ode_uses_portable_stdarg_header_on_android(self):
        source = (ROOT / "third_party/KisakCOD/deps/ode/error.h").read_text(encoding="utf-8")
        self.assertIn("#if defined(__ANDROID__)\n#include <stdarg.h>\n#else\n#include <vadefs.h>\n#endif", source)


if __name__ == "__main__":
    unittest.main()
