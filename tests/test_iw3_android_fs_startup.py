"""Regression tests for the authentic IW3 filesystem-startup source slice."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_fs_startup import (
    SOURCE, CMD_SOURCE, FUNCTIONS, COMMAND_FUNCTIONS, COMMAND_FS_FUNCTIONS,
    FS_COMMAND_STATE, CMD_REGISTRY_STATE, REQUIRED, FORBIDDEN, prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source
from tools.iw3_android.prepare_real_engine_iwd_services import prepare as prepare_iwd_services

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalFilesystemStartupTests(unittest.TestCase):
    def test_startup_functions_are_exact_original_bodies_and_not_claimed_as_runtime(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        bodies = [function_source(source, signature) for signature in FUNCTIONS]
        command_source_path = ENGINE / CMD_SOURCE
        command_original = command_source_path.read_bytes()
        command_source = command_original.decode("utf-8")
        command_bodies = [function_source(command_source, signature) for signature in COMMAND_FUNCTIONS]
        self.assertIn(FS_COMMAND_STATE, source)
        self.assertIn(CMD_REGISTRY_STATE, command_source)
        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "iw3_fs_startup.cpp"
            report_path = Path(temp) / "evidence.json"
            report = prepare(ENGINE, output, report_path)
            staged = output.read_text(encoding="utf-8")
            cdkey_body = function_source(source, "void __cdecl Com_ReadCDKey()")
            self.assertIn(
                "#if !defined(IW3_FS_STARTUP_HOST_TEST)\n" + cdkey_body + "\n#endif",
                staged,
            )
            for body in bodies:
                self.assertIn(body, staged)
            for body in command_bodies:
                self.assertIn(body, staged)
            self.assertIn(
                "#if !defined(IW3_FS_STARTUP_HOST_TEST)\n" + FS_COMMAND_STATE + "\n#endif",
                staged,
            )
            self.assertIn(
                "#if !defined(IW3_FS_STARTUP_HOST_TEST)\n" + CMD_REGISTRY_STATE,
                staged,
            )
            self.assertEqual(report["source_sha256"],
                             hashlib.sha256(original).hexdigest())
            self.assertEqual(report["command_source_sha256"],
                             hashlib.sha256(command_original).hexdigest())
            self.assertTrue(report["original_FS_command_handlers_staged_verbatim"])
            self.assertTrue(report["original_FS_AddCommands_body_staged_verbatim"])
            self.assertTrue(report["original_command_registry_functions_staged_verbatim"])
            self.assertTrue(report["original_command_registry_state_staged_verbatim"])
            self.assertFalse(report["command_registry_runtime_invoked"])
            self.assertFalse(report["command_registry_linked_to_android_runtime"])
            self.assertTrue(report["original_FS_AddSearchPath_body_staged_verbatim"])
            self.assertTrue(report["original_FS_AddGameDirectory_body_staged_verbatim"])
            self.assertTrue(report["original_FS_AddLocalizedGameDirectory_body_staged_verbatim"])
            self.assertTrue(report["original_FS_AddIwdFilesForGameDirectory_body_staged_verbatim"])
            self.assertTrue(report["original_FS_IsBackupSubStr_body_staged_verbatim"])
            self.assertTrue(report["original_FS_SanitizeFilename_body_staged_verbatim"])
            self.assertTrue(report["original_FS_UseSearchPath_body_staged_verbatim"])
            self.assertTrue(report["original_FS_AddFileToList_body_staged_verbatim"])
            self.assertTrue(report["original_FS_ReturnPath_body_staged_verbatim"])
            self.assertTrue(report["original_FS_ListFiles_body_staged_verbatim"])
            self.assertTrue(report["original_FS_CheckLocation_body_staged_verbatim"])
            self.assertTrue(report["original_iwd_directory_enumeration_in_startup_archive"])
            self.assertTrue(report["iwd_directory_scan_fails_closed_on_missing_listing"])
            self.assertTrue(report["iwd_sort_uses_native_pointer_width"])
            self.assertTrue(report["original_FS_ReplaceSeparators_body_staged_verbatim"])
            self.assertTrue(report["original_FS_BuildOSPath_body_staged_verbatim"])
            self.assertTrue(report["original_FS_BuildOSPathForThread_body_staged_verbatim"])
            self.assertTrue(report["path_builder_uses_bounded_native_size_lengths"])
            self.assertTrue(report["path_builder_fails_closed_on_overflow"])
            self.assertTrue(report["directory_allocation_uses_native_sizeof"])
            self.assertTrue(report["unsupported_localized_language_fails_closed"])
            self.assertTrue(report["original_Com_ReadCDKey_body_preserved_verbatim"])
            self.assertIn("void __cdecl Com_ReadCDKey()", staged)
            self.assertTrue(report["original_FS_RegisterDvars_body_preserved_verbatim"])
            self.assertTrue(report["original_FS_Startup_body_preserved_verbatim"])
            self.assertTrue(report["original_FS_SetRestrictions_body_preserved_verbatim"])
            self.assertTrue(report["original_FS_IsBasePathValid_body_preserved_verbatim"])
            self.assertTrue(report["original_FS_InitFilesystem_body_preserved_verbatim"])
            self.assertTrue(report["string_dvars_use_native_pointer_members"])
            self.assertIn("homePath = nullptr;", staged)
            self.assertNotIn("homePath = (char *)RETURN_ZERO32();", staged)
            self.assertFalse(report["dvar_registry_linked"])
            self.assertFalse(report["startup_runtime_invoked"])
            self.assertFalse(report["licensed_fastfile_or_map_loaded"])
            self.assertFalse(report["renderer_or_gameplay_proven"])
            self.assertTrue(report["empty_homepath_search_registration_skipped"])
            self.assertFalse(report["playable_apk"])
            for marker in REQUIRED:
                self.assertIn(marker, staged)
            for marker in FORBIDDEN:
                self.assertNotIn(marker, staged)
            saved_report = report_path.read_text(encoding="utf-8")
            self.assertIn('"startup_runtime_invoked": false', saved_report)
        self.assertEqual(source_path.read_bytes(), original)
        self.assertEqual(command_source_path.read_bytes(), command_original)

    def test_startup_never_registers_an_empty_homepath_as_a_relative_search_root(self):
        source = (ENGINE / SOURCE).read_text(encoding="utf-8")
        startup = function_source(source, "void __cdecl FS_Startup(char *gameName)")
        guarded_homepath = (
            "if (fs_homepath->current.string[0] != '\\0')\n"
            "            FS_AddLocalizedGameDirectory((char *)fs_homepath->current.string, gameName);"
        )
        self.assertIn(guarded_homepath, startup)

        generator = (ROOT / "tools/iw3_android/prepare_real_engine_fs_startup.py").read_text(encoding="utf-8")
        native_test = (ROOT / "android/iw3-native/fs_localized_path_native_test.cpp").read_text(encoding="utf-8")
        self.assertIn('"empty_homepath_search_registration_skipped": True', generator)
        self.assertIn("FS_Startup(main_game);", native_test)
        self.assertIn("assert(entry->dir->path[0] != '\\0');", native_test)
        self.assertIn("IW3_ORIGINAL_FS_STARTUP_EMPTY_HOMEPATH_PASS", native_test)
    def test_original_game_directory_setup_uses_native_allocation_size(self):
        source = (ENGINE / SOURCE).read_text(encoding="utf-8")
        add_searchpath = function_source(
            source,
            "void __cdecl FS_AddSearchPath(searchpath_s *search)",
        )
        self.assertIn("pSearch = &fs_searchpaths;", add_searchpath)
        self.assertIn("*pSearch = search;", add_searchpath)
        add_directory = function_source(
            source,
            "void __cdecl FS_AddGameDirectory(char *path, char *dir, int bLanguageDirectory, int iLanguage)",
        )
        add_localized = function_source(
            source,
            "void __cdecl FS_AddLocalizedGameDirectory(char *path, char *dir)",
        )
        self.assertIn(
            'search->dir = (directory_t *)Z_Malloc(sizeof(directory_t), "FS_AddGameDirectory", 3);',
            add_directory,
        )
        self.assertNotIn("Z_Malloc(512", add_directory)
        self.assertNotIn("uint32_t *v4", add_directory)
        language_guard = "if (!pszLanguage || !pszLanguage[0])\n            return;"
        self.assertIn(language_guard, add_directory)
        self.assertLess(add_directory.index(language_guard),
                        add_directory.index('Com_sprintf(szGameFolder, 0x40u, "%s/%s", dir, pszLanguage);'))
        self.assertIn("FS_AddIwdFilesForGameDirectory(path, szGameFolder);", add_directory)
        add_iwd_files = function_source(
            source,
            "void __cdecl FS_AddIwdFilesForGameDirectory(char *path, char *pszGameFolder)",
        )
        self.assertIn("numfiles = 0;", add_iwd_files)
        self.assertIn("if (!list || numfiles <= 0)", add_iwd_files)
        self.assertIn("qsort(s0, numfiles, sizeof(s0[0]),", add_iwd_files)
        self.assertIn("ZipFile = FS_LoadZipFile(ospath, s0[i]);", add_iwd_files)
        self.assertIn("FS_FreeFileList((const char **)list);", add_iwd_files)

        path_builder = function_source(
            source,
            "void __cdecl FS_BuildOSPathForThread(const char *base, const char *game, const char *qpath, char *ospath, FsThread thread)",
        )
        self.assertIn("size_t baseLength", path_builder)
        self.assertIn("size_t gameLength", path_builder)
        self.assertIn("size_t qpathLength", path_builder)
        self.assertIn("baseLength >= 256 || gameLength >= 256 || qpathLength >= 256", path_builder)
        self.assertIn("FS_ReplaceSeparators(ospath);", path_builder)
        self.assertNotIn("uint32_t v5;", path_builder)
        self.assertNotIn("uint32_t v6;", path_builder)
        self.assertNotIn("uint32_t v7;", path_builder)

        build_path = function_source(
            source,
            "void __cdecl FS_BuildOSPath(const char *base, const char *game, const char *qpath, char *ospath)",
        )
        self.assertIn("FS_BuildOSPathForThread(base, game, qpath, ospath, FS_THREAD_MAIN);", build_path)
        self.assertIn("FS_AddGameDirectory(path, dir, 1, i);", add_localized)
        self.assertIn("FS_AddGameDirectory(path, dir, 0, 0);", add_localized)

    def test_workflow_audits_original_path_builder_as_resolved(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("FS_BuildOSPathForThread(", workflow)
        self.assertIn("IW3_ORIGINAL_FS_BUILD_OS_PATH_AARCH64_RESOLVED", workflow)
        self.assertIn("FS_BuildOSPath(", workflow)
        self.assertIn("libiw3_sp_filtered_files.a", workflow)
        self.assertIn("FS_ListFiles FS_CheckLocation FS_ListFilteredFiles FS_ListFilteredFilesInLocation", workflow)
        self.assertIn("IW3_ORIGINAL_FS_LISTFILES_FILTERED_CHAIN_AARCH64_LINK_GREEN", workflow)
        compat = (ROOT / "android/iw3-native/iw3_android_fs_startup_compat.h").read_text(encoding="utf-8")
        self.assertIn("const char **__cdecl FS_ListFilteredFiles(", compat)
        self.assertIn("int __cdecl FS_IwdIsPure(iwd_t *iwd);", compat)
        self.assertIn("searchpath_s *searchPath, const char *path, const char *extension,", compat)
        self.assertIn("for symbol in MyAssertHandler I_strnicmp; do", workflow)
        self.assertIn("for symbol in 'Com_Filter(' 'Com_FilterPath('; do", workflow)
        self.assertIn("IW3_ORIGINAL_FILTER_PATH_PROVIDER_AARCH64_LINK_GREEN", workflow)
        self.assertNotIn('grep -F "FS_BuildOSPath" "$RUNNER_TEMP/iw3-fs-startup-undefined.txt"', workflow)
        self.assertIn("IW3_ORIGINAL_FS_COMMAND_REGISTRATION_AARCH64_LINK_GREEN", workflow)
        self.assertIn("Cmd_AddCommandInternal", workflow)
        self.assertIn("Cmd_FindCommand", workflow)

    def test_combined_audit_keeps_single_original_providers(self):
        startup = (ROOT / "tools/iw3_android/prepare_real_engine_fs_startup.py").read_text(encoding="utf-8")
        fs_read = (ROOT / "tools/iw3_android/prepare_real_engine_fs_read.py").read_text(encoding="utf-8")
        lookup_io = (ROOT / "android/iw3-native/iw3_android_iwd_lookup_io.cpp").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertNotIn('"int __cdecl FS_IwdIsPure(iwd_t *iwd)', startup)
        self.assertIn("FS_IwdIsPure", fs_read)
        self.assertIn("#if !defined(IW3_IWD_DIRECTORY_LINK_AUDIT)", lookup_io)
        self.assertIn("int __cdecl SEH_GetCurrentLanguage()", lookup_io)
        self.assertIn("Hunk_UserCreate Hunk_UserAlloc Hunk_UserAllocAlignStrict Hunk_UserSetPos Hunk_UserReset Hunk_UserDestroy Hunk_CopyString Z_VirtualReserve Z_VirtualCommit Z_VirtualDecommit Z_VirtualFree", workflow)
        self.assertIn("for symbol in MyAssertHandler I_strnicmp; do", workflow)
        self.assertIn("for symbol in 'Com_Filter(' 'Com_FilterPath('; do", workflow)
        self.assertIn("IW3_ORIGINAL_FILTER_PATH_PROVIDER_AARCH64_LINK_GREEN", workflow)
        self.assertIn('grep -F "$symbol" "$RUNNER_TEMP/iw3-fs-dvar-iwd-defined.txt"', workflow)

    def test_full_original_dvar_registry_resolves_fs_startup_registration_edges(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn('startup_archive="$RUNNER_TEMP/iw3-build-arm64/libiw3_sp_fs_startup.a"', workflow)
        self.assertIn('dvar_full_archive="$RUNNER_TEMP/iw3-build-arm64/libiw3_sp_dvar_android.a"', workflow)
        self.assertIn('"$startup_archive" "$print_warning_archive" "$print_printf_archive" "$dvar_full_archive" "$cmd_args_archive" --no-whole-archive', workflow)
        self.assertIn("IW3_ORIGINAL_FS_STARTUP_DVAR_REGISTRATION_AARCH64_COMBINED_LINK_GREEN", workflow)
        self.assertIn("IW3_ORIGINAL_FS_STARTUP_CDKEY_PROVIDER_AARCH64_LINK_GREEN", workflow)
        self.assertIn("if grep -F 'Com_ReadCDKey()' \"$RUNNER_TEMP/iw3-fs-dvar-startup-undefined.txt\"; then", workflow)
        self.assertIn("IW3_ORIGINAL_FS_STARTUP_IWD_ENUMERATION_AARCH64_RESOLVED", workflow)
        self.assertIn("FS_AddIwdFilesForGameDirectory", workflow)
        self.assertIn("Dvar_RegisterInt Dvar_RegisterString Dvar_RegisterBool Z_Malloc SEH_GetLanguageName FS_ReadFile SEH_InitLanguage FS_LoadZipFile Sys_ListFiles FS_FreeFileList IwdFileLanguage iwdsort I_strncmp SEH_GetLanguageIndexForName", workflow)
        self.assertIn("IW3_ORIGINAL_COM_PRINT_WARNING_AARCH64_RESOLVED", workflow)
        self.assertIn('echo "IW3_FS_STARTUP_RUNTIME_INVOKED=false"', workflow)
        self.assertIn('echo "IW3_PLAYABLE_APK=false"', workflow)

    def test_original_iwd_allocator_language_and_zip_helpers_join_startup_audit(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_iwd_services.cpp"
            report = prepare_iwd_services(ENGINE, output)
            staged = output.read_text(encoding="utf-8")

        for symbol in ("Z_Malloc", "Z_Free", "Com_BlockChecksumKey32", "I_stricmp"):
            self.assertIn(symbol, staged)
        self.assertTrue(report["original_allocator_and_free_staged"])
        self.assertTrue(report["original_checksum_algorithm_staged"])
        self.assertFalse(report["playable_apk"])

        names_generator = (ROOT / "tools/iw3_android/prepare_real_engine_iwd_names.py").read_text(encoding="utf-8")
        self.assertIn('("char *__cdecl IwdFileLanguage(const char *pszIwdFileName)", FILES)', names_generator)
        self.assertIn('GLOBALS = "char szIwdLanguageName[2][64];', names_generator)
        directory_generator = (ROOT / "tools/iw3_android/prepare_real_engine_iwd_directory.py").read_text(encoding="utf-8")
        for symbol in ("FS_PathCmp", "iwdsort", "I_strncmp"):
            self.assertIn(symbol, directory_generator)

        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn("add_library(iw3_sp_iwd_services STATIC", cmake)
        self.assertIn("IW3_EXTRACTED_IWD_SERVICES", cmake)
        self.assertIn("IW3_EXTRACTED_IWD_NAMES", cmake)
        self.assertIn("add_library(iw3_sp_unzip STATIC", cmake)
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn('"$startup_archive" "$parser_archive" "$print_warning_archive" "$print_printf_archive" "$cmd_args_archive" "$q_shared_strings_archive" "$dvar_full_archive" "$iwd_services_archive"', workflow)
        self.assertIn('"$iwd_mount_archive" "$unzip_archive" "$iwd_directory_archive"', workflow)
        self.assertIn("libiw3_sp_iwd_directory_services.a", workflow)
        self.assertIn("IW3_ORIGINAL_FS_STARTUP_IWD_DIRECTORY_READFILE_HUNK_AARCH64_LINK_GREEN", workflow)
        self.assertIn("for symbol in Cmd_Argc Cmd_Argv IwdFileLanguage FS_PathCmp iwdsort I_strncmp Z_Malloc FS_LoadZipFile unzOpen", workflow)
        self.assertIn("FS_ReadFile FS_FOpenFileRead FS_CheckFileSystemStarted FS_AllocMem", workflow)
        self.assertIn("for symbol in SEH_InitLanguage SEH_UpdateCurrentLanguage; do", workflow)
        self.assertIn("IW3_ORIGINAL_FS_STARTUP_LANGUAGE_INIT_AARCH64_LINK_GREEN", workflow)
        self.assertIn("FS_FileOpenReadBinary FS_FileClose FS_FileRead FS_FileSeek FS_FileGetFileSize", workflow)
        self.assertIn("IW3_ORIGINAL_FS_STARTUP_IWD_DIRECTORY_READFILE_HUNK_AARCH64_LINK_GREEN", workflow)
        self.assertIn('echo "IW3_PLAYABLE_APK=false"', workflow)

    def test_iwd_enumerator_is_in_startup_archive_but_not_the_narrow_host_probe(self):
        generator = (ROOT / "tools/iw3_android/prepare_real_engine_fs_startup.py").read_text(encoding="utf-8")
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("#if !defined(IW3_FS_STARTUP_HOST_TEST)", generator)
        self.assertIn("IW3_FS_STARTUP_HOST_TEST=1", cmake)
        self.assertIn("FS_AddIwdFilesForGameDirectory", workflow)
        self.assertIn("IW3_ORIGINAL_FS_STARTUP_IWD_ENUMERATION_AARCH64_RESOLVED", workflow)
        self.assertNotIn("Dvar_RegisterInt Dvar_RegisterString Dvar_RegisterBool FS_AddIwdFilesForGameDirectory Z_Malloc", workflow)

    def test_original_path_builder_uses_the_single_existing_iwd_lookup_provider(self):
        lookup_generator = (ROOT / "tools/iw3_android/prepare_real_engine_iwd_lookup.py").read_text(encoding="utf-8")
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        directory_io = (ROOT / "android/iw3-native/iw3_android_iwd_directory_io.cpp").read_text(encoding="utf-8")
        lookup_io = (ROOT / "android/iw3-native/iw3_android_iwd_lookup_io.cpp").read_text(encoding="utf-8")
        self.assertIn('("void __cdecl FS_BuildOSPath(const char *base, const char *game, const char *qpath, char *ospath)", SOURCE)', lookup_generator)
        self.assertIn("FS_BuildOSPathForThread(base, game, qpath, ospath, FS_THREAD_MAIN);", lookup_generator)
        self.assertIn('"' + '$' + '{IW3_EXTRACTED_IWD_LOOKUP}' + '"', cmake)
        self.assertNotIn("iw3_sp_fs_startup_runtime", cmake)
        self.assertNotIn("void __cdecl FS_BuildOSPath(const char *base, const char *game,", directory_io)
        self.assertNotIn("void __cdecl Com_Error(errorParm_t code, const char *format, ...)", directory_io)
        self.assertIn("void QDECL Com_Error(errorParm_t code, const char *format, ...)", lookup_io)

    def test_iwd_lookup_generator_stages_original_fs_build_os_path_body(self):
        from tools.iw3_android.prepare_real_engine_iwd_lookup import prepare as prepare_iwd_lookup
        with TemporaryDirectory() as temp:
            output = Path(temp) / "iw3_iwd_lookup.cpp"
            report = prepare_iwd_lookup(ENGINE, output)
            staged = output.read_text(encoding="utf-8")
            self.assertIn("void __cdecl FS_BuildOSPath(const char *base, const char *game, const char *qpath, char *ospath)", staged)
            self.assertIn("FS_BuildOSPathForThread(base, game, qpath, ospath, FS_THREAD_MAIN);", staged)
            self.assertTrue(report["original_FS_BuildOSPath_body_staged_verbatim"])
            self.assertTrue(report["original_path_builder_helper_bodies_staged_verbatim"])

    def test_android_path_service_uses_configured_private_root_not_process_cwd(self):
        platform = (ROOT / "android/iw3-native/iw3_android_platform.cpp").read_text(encoding="utf-8")
        header = (ROOT / "android/iw3-native/iw3_android_platform.h").read_text(encoding="utf-8")
        adapter = (ROOT / "android/iw3-native/iw3_android_fs_startup_io.cpp").read_text(encoding="utf-8")
        directory_io = (ROOT / "android/iw3-native/iw3_android_iwd_directory_io.cpp").read_text(encoding="utf-8")
        directory_adapter = (ROOT / "android/iw3-native/iw3_android_directory_has_contents.cpp").read_text(encoding="utf-8")
        compat = (ROOT / "android/iw3-native/iw3_android_fs_startup_compat.h").read_text(encoding="utf-8")
        native_test = (ROOT / "android/iw3-native/platform_native_test.cpp").read_text(encoding="utf-8")
        jni = (ROOT / "android/iw3-native/iw3_android_jni.cpp").read_text(encoding="utf-8")
        self.assertIn("z2026_platform_copy_data_root", platform)
        self.assertIn("z2026_platform_copy_data_root", header)
        self.assertIn("char *Sys_Cwd()", adapter)
        self.assertIn("z2026_platform_copy_data_root", adapter)
        self.assertIn("Sys_DefaultCDPath()", adapter)
        self.assertIn('return language == 0 ? "english" : "";', directory_io)
        self.assertIn("int Sys_DirectoryHasContents(const char *directory)", directory_adapter)
        self.assertNotIn("__cdecl Sys_DirectoryHasContents", directory_adapter)
        self.assertIn("z2026_platform_directory_has_contents(relative)", directory_adapter)
        self.assertIn("return result > 0 ? 1 : 0;", directory_adapter)
        self.assertNotIn("Sys_DirectoryHasContents", directory_io)
        self.assertIn("int Sys_DirectoryHasContents(const char *directory);", compat)
        self.assertIn("typedef int BOOL;", compat)
        self.assertIn("FS_GameDirDomainFunc", compat)
        self.assertIn("z2026_platform_copy_data_root", native_test)
        self.assertIn("IW3_JNI_FS_STARTUP_PATH_%s", jni)


if __name__ == "__main__":
    unittest.main()


class OriginalFsReadfileProviderIntegrationTests(unittest.TestCase):
    def test_logfile_and_writer_lock_providers_are_required_by_the_combined_audit(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("IW3_EXTRACTED_COM_LOGFILE_OPEN", cmake)
        self.assertIn("iw3_android_fs_lock_io.cpp", cmake)
        self.assertIn("IW3_ORIGINAL_FS_READFILE_LOGFILE_AND_WRITE_LOCK_AARCH64_LINK_GREEN", workflow)
        self.assertIn("Sys_LockWrite(FastCriticalSection*)", workflow)
        self.assertIn("Sys_UnlockWrite(FastCriticalSection*)", workflow)
