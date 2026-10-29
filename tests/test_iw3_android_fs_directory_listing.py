from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AndroidFilesystemDirectoryListingTests(unittest.TestCase):
    def test_generic_platform_enumerator_is_rooted_and_no_follow(self):
        header = (ROOT / "android/iw3-native/iw3_android_platform.h").read_text()
        source = (ROOT / "android/iw3-native/iw3_android_platform.cpp").read_text()
        self.assertIn("z2026_platform_list_directory_entries", header)
        start = source.index("z2026_platform_list_directory_entries(")
        end = source.index("z2026_platform_directory_has_contents(", start)
        body = source[start:end]
        self.assertIn("normalize_engine_path(directory, relative, true)", body)
        self.assertIn("open_directory_beneath_root(g_data_root_fd, relative)", body)
        self.assertIn("AT_SYMLINK_NOFOLLOW", body)
        self.assertIn("S_ISREG(st.st_mode)", body)
        self.assertIn("S_ISDIR(st.st_mode)", body)
        self.assertIn("needed > output_capacity", body)
        self.assertIn("*entry_count = names.size()", body)

    def test_sys_list_files_keeps_iwd_cap_and_supports_real_queries(self):
        source = (ROOT / "android/iw3-native/iw3_android_iwd_directory_io.cpp").read_text()
        start = source.index("char **Sys_ListFiles(const char *directory, const char *extension,")
        end = source.index("void __cdecl FS_FreeFileList", start)
        body = source[start:end]
        self.assertIn("z2026_platform_list_iwd_files", body)
        self.assertIn("z2026_platform_list_directory_entries", body)
        self.assertIn("Com_FilterPath(filter, name, 0)", body)
        self.assertIn("directory_only = wantsubs != 0", body)
        self.assertIn("raw_count > 1024", body)
        self.assertNotIn("(filter && *filter) || wantsubs != 0", body)
        self.assertNotIn('(extension && *extension && I_stricmp(extension, "iwd")) ||', body)

    def test_shared_runtime_links_the_existing_id_tech_3_filter_provider(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text()
        self.assertIn('"\u0024{CMAKE_CURRENT_SOURCE_DIR}/iw3_android_filter.cpp"', cmake)

    def test_host_runtime_covers_files_directories_symlinks_and_capacity(self):
        test = (ROOT / "android/iw3-native/platform_native_test.cpp").read_text()
        self.assertIn('generic_dir + "/config.cfg"', test)
        self.assertIn('generic_dir + "/localized.str"', test)
        self.assertIn('generic_dir + "/.hidden.cfg"', test)
        self.assertIn('generic_dir + "/linked.cfg"', test)
        self.assertIn('z2026_platform_list_directory_entries(\n        "generic", 1', test)
        self.assertIn('z2026_platform_list_directory_entries(\n        "../", 0', test)


if __name__ == "__main__":
    unittest.main()
