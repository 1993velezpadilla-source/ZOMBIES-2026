from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "third_party/KisakCOD/src/database/db_registry.cpp"
OPEN_HELPER = ROOT / "third_party/KisakCOD/src/database/db_fastfile_posix_open.h"
PLATFORM_TEST = ROOT / "android/iw3-native/platform_native_test.cpp"
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"
WORKFLOW = ROOT / ".github/workflows/iw3-fastfile-posix-read-arm64.yml"


class FastFilePosixOpenRegression(unittest.TestCase):
    def test_original_registry_uses_android_fd_opener(self):
        source = REGISTRY.read_text(encoding="utf-8")
        start = source.index(
            "int32_t __cdecl DB_TryLoadXFileInternal(char *zoneName, int32_t zoneFlags)\n{"
        )
        end = source.index("\nvoid __cdecl DB_BuildOSPath(", start)
        body = source[start:end]
        self.assertIn('#include "db_fastfile_posix_open.h"', source)
        self.assertIn("DBFastFilePosixOpenEnginePath(filename, &zoneFileSize, &zoneOpenError)", body)
        self.assertIn("zone->fileSize = zoneFileSize;", body)
        self.assertIn("DB_LoadXFile(filename, zoneFile, zone->name", body)
        self.assertIn("fs_gameDirVar->current.string[0]", body)
        self.assertIn("DB_BuildOSPath(zoneName, 256, filename);", body)
        opener = body.index("DBFastFilePosixOpenEnginePath(filename")
        android_start = body.rfind("#if defined(__ANDROID__)", 0, opener)
        android_end = body.index("#else", android_start)
        android = body[android_start:android_end]
        windows_end = body.index("#endif", android_end)
        windows = body[android_end:windows_end]
        self.assertNotIn("fs_gameDirVar->current.integer", android)
        self.assertNotIn("CreateFileA", android)
        self.assertNotIn("GetFileSize", android)
        self.assertIn("CreateFileA", windows)

    def test_open_helper_checks_rooted_fd_type_size_and_opaque_encoding(self):
        source = OPEN_HELPER.read_text(encoding="utf-8")
        self.assertIn("z2026_platform_open_engine_path_fd(path)", source)
        self.assertIn("fstat(fd, &fileStat)", source)
        self.assertIn("S_ISREG(fileStat.st_mode)", source)
        self.assertIn("std::numeric_limits<int32_t>::max()", source)
        self.assertIn("DBFastFilePosixOpaqueFromFd(fd)", source)
        self.assertIn("close(fd)", source)
        self.assertIn("return invalidHandle;", source)

    def test_platform_runtime_exercises_open_read_and_reject_paths(self):
        source = PLATFORM_TEST.read_text(encoding="utf-8")
        self.assertIn("DBFastFilePosixOpenEnginePath(", source)
        self.assertIn("DBFastFilePosixFdFromOpaque(fastfile_opaque)", source)
        self.assertIn("DBFastFilePosixReadAt(opened_fastfile_fd", source)
        self.assertIn("linked.ff", source)
        self.assertIn("escaped_fastfile", source)

    def test_host_target_includes_original_database_header(self):
        source = CMAKE.read_text(encoding="utf-8")
        self.assertIn("ENGINE_SOURCE_ROOT}/database", source)

    def test_arm64_gate_tracks_and_compiles_the_opener_test(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        for required in (
            "third_party/KisakCOD/src/database/db_registry.cpp",
            "third_party/KisakCOD/src/database/db_fastfile_posix_open.h",
            "android/iw3-native/platform_native_test.cpp",
            "tests/test_iw3_android_fastfile_posix_open.py",
            "IW3_FASTFILE_POSIX_OPEN_HELPER_AARCH64_OBJECT_PASS",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
