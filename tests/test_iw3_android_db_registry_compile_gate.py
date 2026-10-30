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
        self.assertIn('#if defined(__ANDROID__)\n#include "db_fastfile_posix_open.h"\n#endif', source)
        self.assertIn("DBFastFilePosixOpenEnginePath(filename, &zoneFileSize, &zoneOpenError)", source)
        self.assertIn("zone->fileSize = zoneFileSize;", source)
        self.assertIn("return DBFastFilePosixFileSizeEnginePath(filename);", source)

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


if __name__ == "__main__":
    unittest.main()
