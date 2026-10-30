"""Regression for native Android paths in the genuine KisakCOD filesystem TU.

The original Win32 normalizer produced backslashes on Android too. Those paths
cannot be used by rooted POSIX directory probes and IWD scans. The host test
executes authentic extracted FS_BuildOSPath/FS_Startup bodies with the same
native separator branch; it is not a gameplay or APK test.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/universal/com_files.cpp"
NATIVE = ROOT / "android/iw3-native/fs_localized_path_native_test.cpp"
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"
GENERATOR = ROOT / "tools/iw3_android/prepare_real_engine_fs_startup.py"


class AndroidOriginalFilesystemPosixPaths(unittest.TestCase):
    def test_original_path_normalizer_preserves_posix_root(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("void __cdecl FS_ReplaceSeparators(char *path)")
        end = source.index("void __cdecl FS_BuildOSPath(", start)
        body = source[start:end]
        self.assertIn("#if defined(__ANDROID__) || defined(IW3_FS_POSIX_PATHS_TEST)", body)
        self.assertIn("constexpr char nativeSeparator = '/';", body)
        self.assertIn("constexpr char nativeSeparator = '\\\\';", body)
        self.assertIn("*dst++ = nativeSeparator;", body)
        self.assertNotIn("*dst++ = 92;", body)
        self.assertIn("FS_ReplaceSeparators(ospath);", source)

    def test_mkdir_traversal_uses_same_native_separator(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("int __cdecl FS_CreatePath(char *OSPath)")
        end = source.index("\n}", start)
        body = source[start:end]
        self.assertIn("#if defined(__ANDROID__) || defined(IW3_FS_POSIX_PATHS_TEST)", body)
        self.assertIn("if (*ofs == nativeSeparator)", body)
        self.assertIn("Sys_Mkdir(OSPath);", body)
        self.assertIn('"int __cdecl FS_CreatePath(char *OSPath)"',
                      GENERATOR.read_text(encoding="utf-8"))
        self.assertIn("*ofs = nativeSeparator;", body)

    def test_overlong_iwd_and_localized_paths_fail_closed(self):
        source = SOURCE.read_text(encoding="utf-8")
        iwd_start = source.index(
            "void __cdecl FS_AddIwdFilesForGameDirectory(char *path, char *pszGameFolder)"
        )
        localized_start = source.index(
            "void __cdecl FS_AddGameDirectory(char *path, char *dir, int bLanguageDirectory, int iLanguage)"
        )
        iwd = source[iwd_start:source.index("\n}", iwd_start)]
        localized = source[localized_start:source.index("\n}", localized_start)]
        unsafe = "ospath[&ospath[strlen(ospath) + 1] - &ospath[1] - 1] = 0;"
        for body in (iwd, localized):
            self.assertNotIn(unsafe, body)
            self.assertIn("const size_t directoryLength = strlen(ospath);", body)
            self.assertIn("if (directoryLength < 2 ||", body)
            self.assertIn("ospath[directoryLength - 1] = '\\0';", body)
        self.assertLess(iwd.index("if (directoryLength < 2 ||"),
                        iwd.index("list = Sys_ListFiles("))
        self.assertLess(localized.index("if (directoryLength < 2 ||"),
                        localized.index("if (!Sys_DirectoryHasContents(ospath))"))
        native = NATIVE.read_text(encoding="utf-8")
        self.assertIn("FS_AddGameDirectory(overlongRoot.data(), game, 1, 0);", native)
        self.assertIn("assert(g_directory_probes == 0);", native)
        self.assertIn("assert(g_iwd_scans == 0);", native)
        self.assertIn("IW3_ORIGINAL_FS_OVERLONG_LOCALIZED_PATH_FAIL_CLOSED_PASS", native)

    def test_host_exercises_real_path_builder_not_a_fake(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        test = NATIVE.read_text(encoding="utf-8")
        self.assertIn("IW3_FS_POSIX_PATHS_TEST=1", cmake)
        self.assertIn("IW3_EXTRACTED_FS_STARTUP", cmake)
        self.assertIn('FS_BuildOSPath("/private', test)
        self.assertIn('"/private/iw3/main/english/voice"', test)
        self.assertIn('"/private/iw3/main/maps/mp/test.d3dbsp"', test)
        self.assertIn('g_probed_paths[0] == "/private/iw3/main/english"', test)
        self.assertIn("assert(FS_CreatePath(nested) == 0);", test)
        self.assertIn("assert(FS_CreatePath(traversal) == 1);", test)
        self.assertIn("g_mkdir_paths.size() == 4", test)


if __name__ == "__main__":
    unittest.main()
