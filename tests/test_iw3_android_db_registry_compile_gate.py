"""Keep the complete original IW3 database registry in the Android ARM64 compile audit."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "third_party/KisakCOD/src/database/db_registry.cpp"
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"
WORKFLOW = ROOT / ".github/workflows/iw3-original-native-android.yml"


class OriginalDbRegistryCompileGateTests(unittest.TestCase):
    def test_original_registry_uses_the_real_android_fastfile_opener(self):
        source = REGISTRY.read_text(encoding="utf-8")
        android = source.index("#if defined(__ANDROID__)")
        opener = source.index('#include "db_fastfile_posix_open.h"', android)
        compat = source.index('#include "db_registry_android_compat.h"', opener)
        end = source.index("#endif", compat)
        self.assertLess(android, opener)
        self.assertLess(opener, compat)
        self.assertLess(compat, end)
        self.assertIn("DBFastFilePosixOpenEnginePath(filename, &zoneFileSize, &zoneOpenError)", source)
        self.assertIn("zone->fileSize = zoneFileSize;", source)
        self.assertIn("return DBFastFilePosixFileSizeEnginePath(filename);", source)
    def test_android_registry_does_not_import_win32_directinput_local_header(self):
        source = REGISTRY.read_text(encoding="utf-8")
        android_branch = source.index("#if defined(__ANDROID__)\n#include <qcommon/qcommon.h>")
        win_local = source.index("#include <win32/win_local.h>")
        branch_else = source.index("#else", android_branch)
        branch_end = source.index("#endif", branch_else)
        self.assertLess(android_branch, branch_else)
        self.assertLess(branch_else, win_local)
        self.assertLess(win_local, branch_end)
        self.assertIn("bool __cdecl IsConfigFile(const char *name)", source)
    def test_windows_file_open_path_remains_separate(self):
        source = REGISTRY.read_text(encoding="utf-8")
        self.assertIn("#else\n    if (I_stricmp(zoneName, \"mp_patch\"))", source)
        self.assertIn('CreateFileA("update:\\\\mp_patch.ff"', source)
        self.assertIn("size = GetFileSize(zoneFile, 0);", source)

    def test_cmake_compiles_the_complete_original_registry_as_object_only(self):
        source = CMAKE.read_text(encoding="utf-8")
        target = source.index("add_library(iw3_sp_db_registry_full_compile OBJECT")
        original = source.index('"${IW3_ENGINE_SOURCE_ROOT}/database/db_registry.cpp"', target)
        self.assertLess(target, original)
        self.assertIn("target_compile_definitions(iw3_sp_db_registry_full_compile PRIVATE KISAK_SP=1)", source)
        self.assertIn("-fms-extensions -Wall -Wextra", source[target:])

    def test_arm64_workflow_checks_registry_object_and_real_entry_points(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        for marker in (
            "iw3_sp_db_registry_full_compile.dir",
            "IW3_ORIGINAL_DB_REGISTRY_AARCH64_OBJECT_PASS",
            "DB_TryLoadXFileInternal",
            "DB_FileSize",
            "IW3_DB_REGISTRY_RUNTIME_LINKED=false",
        ):
            self.assertIn(marker, source)

    def test_registry_object_is_preserved_as_non_game_evidence(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("iw3-build-arm64/CMakeFiles/iw3_sp_db_registry_full_compile.dir/**/*.o", source)
        self.assertIn("iw3-db-registry-undefined.txt", source)
        self.assertIn("IW3_PLAYABLE_APK=false", source)

    def test_android_d3d9_header_exposes_only_opaque_abi_types(self):
        source = (ROOT / "third_party/KisakCOD/src/gfx_d3d/r_d3d9_opaque.h").read_text(encoding="utf-8")
        for declaration in (
            "enum _D3DFORMAT : int",
            "D3DFMT_D24S8 = 75",
            "D3DFMT_D24X8 = 77",
            "D3DFMT_D16 = 80",
            "enum _D3DCUBEMAP_FACES : int",
            "struct _D3DDISPLAYMODE",
            "static_assert(sizeof(_D3DDISPLAYMODE) == 16",
            "struct IDirect3DDevice9;",
        ):
            self.assertIn(declaration, source)
        self.assertNotIn("CreateDevice(", source)
        self.assertNotIn("inline", source)

    def test_r_init_uses_sdk_headers_only_outside_android(self):
        source = (ROOT / "third_party/KisakCOD/src/gfx_d3d/r_init.h").read_text(encoding="utf-8")
        guard = source.index("#if !defined(__ANDROID__)")
        windows = source.index("#include <Windows.h>", guard)
        d3d = source.index("#include <d3d9.h>", windows)
        end = source.index("#endif", d3d)
        self.assertLess(guard, windows)
        self.assertLess(windows, d3d)
        self.assertLess(d3d, end)

    def test_android_registry_platform_services_have_real_posix_backing(self):
        compat = (ROOT / "third_party/KisakCOD/src/database/db_registry_android_compat.h").read_text(encoding="utf-8")
        platform = (ROOT / "android/iw3-native/iw3_android_platform.cpp").read_text(encoding="utf-8")
        registry = REGISTRY.read_text(encoding="utf-8")
        self.assertIn("CRITSECT_MISSING_ASSET = 0x17", compat)
        self.assertIn("__atomic_add_fetch(value, 1u, __ATOMIC_SEQ_CST)", compat)
        self.assertIn("__atomic_sub_fetch(value, 1u, __ATOMIC_SEQ_CST)", compat)
        self.assertIn("char *Sys_DefaultInstallPath()", compat)
        self.assertIn("char *Sys_DefaultInstallPath() {", platform)
        self.assertIn("z2026_platform_copy_data_root(install_root, sizeof(install_root))", platform)
        self.assertIn('#include "db_registry_android_compat.h"', registry)
    def test_renderer_backend_does_not_force_d3d9_sdk_on_android(self):
        source = (ROOT / "third_party/KisakCOD/src/gfx_d3d/rb_backend.h").read_text(encoding="utf-8")
        guard = source.index("#if !defined(__ANDROID__)")
        include = source.index("#include <d3d9.h>", guard)
        end = source.index("#endif", include)
        self.assertLess(guard, include)
        self.assertLess(include, end)
    def test_original_r_gfx_selects_opaque_android_d3d_declarations(self):
        source = (ROOT / "third_party/KisakCOD/src/gfx_d3d/r_gfx.h").read_text(encoding="utf-8")
        self.assertIn('#if defined(__ANDROID__)\n#include "r_d3d9_opaque.h"\n#else\n#include <d3d9.h>\n#endif', source)


if __name__ == "__main__":
    unittest.main()
