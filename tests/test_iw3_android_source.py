"""Checks that ARM64 port consumes genuine KisakCOD source unchanged."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_math import (
    ENGINE_FILE, ORIGINAL_PROLOGUE, REQUIRED_FUNCTIONS, prepare,
    SURFACE_FILE, SURFACE_PROLOGUE, prepare_surface,
    CONSTANT_FILE, CONSTANT_PROLOGUE, prepare_constants
)

from tools.iw3_android.prepare_g_runframe_prereqs import (
    COM_SHARED, G_FRAME, MEMCPY_SIGNATURE, FRAME_SIGNATURE,
    FRAME_LEGACY_ASSUMPTIONS, FRAME_TYPED_PORTABILITY_MARKERS, IMPORTANT_CALLS,
    function_source, prepare as prepare_frame_prereq,
)

from tools.iw3_android.prepare_real_engine_pool import (
    ENGINE_POOL, PROLOGUE as POOL_PROLOGUE, REQUIRED as POOL_REQUIRED,
    NOT_ALLOWED as UNSAFE_POOL_POINTERS, PORTABLE as PORTABLE_POOL_MARKERS,
    prepare as prepare_pool,
)

from tools.iw3_android.prepare_real_engine_hitloc import (
    SOURCE as HITLOC_SOURCE, SIGNATURE as HITLOC_SIGNATURE,
    REQUIRED as HITLOC_REQUIRED, UNSAFE as HITLOC_UNSAFE,
    prepare as prepare_hitloc,
)

from tools.iw3_android.prepare_real_engine_iwd_names import (
    FILES as IWD_SOURCE, SHARED as IWD_SHARED,
    FUNCTIONS as IWD_FUNCTIONS, HEADER as IWD_HEADER,
    prepare as prepare_iwd_names,
)

from tools.iw3_android.prepare_real_engine_iwd_mount import (
    SOURCE as IWD_MOUNT_SOURCE, SIGNATURE as IWD_MOUNT_SIGNATURE,
    REQUIRED as IWD_MOUNT_REQUIRED, prepare as prepare_iwd_mount,
)

from tools.iw3_android.prepare_real_engine_iwd_services import (
    FUNCTIONS as IWD_SERVICE_FUNCTIONS, REQUIRED as IWD_SERVICE_REQUIRED,
    prepare as prepare_iwd_services,
)

from tools.iw3_android.prepare_real_engine_iwd_directory import (
    REQUIRED as IWD_DIRECTORY_REQUIRED,
    prepare as prepare_iwd_directory,
)

from tools.iw3_android.prepare_real_engine_iwd_searchpath import (
    SOURCE as IWD_SEARCHPATH_SOURCE, SIGNATURE as IWD_SEARCHPATH_SIGNATURE,
    REQUIRED as IWD_SEARCHPATH_REQUIRED, prepare as prepare_iwd_searchpath,
)
from tools.iw3_android.prepare_real_engine_iwd_lookup import (
    OPEN_SIGNATURE as IWD_LOOKUP_OPEN_SIGNATURE,
    PREFIX_START as IWD_LOOKUP_PREFIX_START,
    PREFIX_END as IWD_LOOKUP_PREFIX_END,
    REQUIRED as IWD_LOOKUP_REQUIRED,
    prepare as prepare_iwd_lookup,
)

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class NativeIW3SourceBridgeTests(unittest.TestCase):
    def test_real_aim_math_preserved(self):
        source = (ENGINE / ENGINE_FILE).read_bytes()
        self.assertTrue(source.decode("utf-8").startswith(ORIGINAL_PROLOGUE))
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "generated" / "com_math_anglevectors.cpp"
            report = prepare(ENGINE, output)
            patched = output.read_text(encoding="utf-8")
            self.assertTrue(report["original_function_bodies_preserved"])
            self.assertFalse(report["android_iw3_apk_exists"])
            self.assertFalse(report["godot_used"])
            self.assertFalse(report["renderer_gles_ported"])
            self.assertEqual(report["source_sha256"], hashlib.sha256(source).hexdigest())
            self.assertEqual(report["original_iw3_math_functions"], list(REQUIRED_FUNCTIONS))
            original = source.decode("utf-8")[len(ORIGINAL_PROLOGUE):]
            original = original.replace('#include "q_shared.h"', "", 1)
            self.assertEqual(
                patched, '#include "iw3_android_math_compat.h"\n' + original)
        self.assertEqual((ENGINE / ENGINE_FILE).read_bytes(), source)

    def test_original_engine_surface_table_and_functions_are_unchanged(self):
        original = (ENGINE / SURFACE_FILE).read_bytes()
        self.assertTrue(original.decode("utf-8").startswith(SURFACE_PROLOGUE))
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "generated" / "surfaceflags.cpp"
            result = prepare_surface(ENGINE, out)
            self.assertEqual(result["source_sha256"], hashlib.sha256(original).hexdigest())
            self.assertTrue(result["function_bodies_preserved"])
            self.assertGreaterEqual(result["data_table_entries_preserved"], 50)
            expected = '#include "iw3_android_surface_compat.h"\n#include "surfaceflags.h"\n'
            self.assertEqual(out.read_text(encoding="utf-8"),
                             expected + original.decode("utf-8")[len(SURFACE_PROLOGUE):])
        self.assertEqual((ENGINE / SURFACE_FILE).read_bytes(), original)

    def test_original_engine_config_registry_unchanged(self):
        original = (ENGINE / CONSTANT_FILE).read_bytes()
        self.assertTrue(original.decode("utf-8").startswith(CONSTANT_PROLOGUE))
        self.assertIn(b'constantConfigStrings[833]', original)
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "generated" / "com_constantconfigstrings.cpp"
            evidence = prepare_constants(ENGINE, out)
            self.assertTrue(evidence["function_bodies_preserved"])
            self.assertEqual(evidence["original_registry_rows"], 833)
            self.assertEqual(evidence["source_sha256"], hashlib.sha256(original).hexdigest())
            patched = out.read_text(encoding="utf-8")
            expected = ('#include "iw3_android_surface_compat.h"\n'
                        '#include "com_constantconfigstrings.h"\n')
            original_body = original.decode("utf-8")[len(CONSTANT_PROLOGUE):]
            original_body = original_body.replace('#include "q_shared.h"', '', 1)
            self.assertEqual(patched, expected + original_body)
            with self.assertRaisesRegex(ValueError, "Refusing"):
                prepare_constants(ENGINE, ENGINE / CONSTANT_FILE)
        self.assertEqual((ENGINE / CONSTANT_FILE).read_bytes(), original)

    def test_original_sp_runframe_prereq_and_32bit_blockers(self):
        com_original = (ENGINE / COM_SHARED).read_bytes()
        sp_original = (ENGINE / G_FRAME).read_bytes()
        frame = function_source(sp_original.decode("utf-8"), FRAME_SIGNATURE)
        self.assertGreater(frame.count("\n"), 200)
        for marker in FRAME_LEGACY_ASSUMPTIONS:
            self.assertNotIn(marker, frame)
        for marker in FRAME_TYPED_PORTABILITY_MARKERS:
            self.assertIn(marker, frame)
        for call in IMPORTANT_CALLS:
            self.assertIn(call, frame)
        with TemporaryDirectory() as temp:
            out = Path(temp) / "stage" / "iw3_frame_memcpy.cpp"
            report_path = Path(temp) / "evidence.json"
            report = prepare_frame_prereq(ENGINE, out, report_path)
            self.assertIsNone(report["g_runframe_compiled_on_android"])
            self.assertFalse(report["iw3_game_apk_available"])
            self.assertTrue(report["original_memcpy_function_preserved_exactly"])
            self.assertTrue(report["frame_animation_loop_uses_typed_entity_fields"])
            self.assertTrue(report["other_sp_engine_abi_assumptions_unverified"])
            self.assertTrue(all(n == 0 for n in report["known_32bit_entity_pointer_hazards_remaining"].values()))
            body = function_source(com_original.decode("utf-8"), MEMCPY_SIGNATURE)
            self.assertEqual(out.read_text(encoding="utf-8"),
                             '#include "iw3_android_frame_compat.h"\n' + body + "\n")
            self.assertEqual(report["original_memcpy_source_sha256"],
                             hashlib.sha256(body.encode("utf-8")).hexdigest())
            self.assertTrue(report_path.is_file())
            with self.assertRaisesRegex(ValueError, "Never overwrite"):
                prepare_frame_prereq(ENGINE, ENGINE / COM_SHARED, report_path)
        self.assertEqual((ENGINE / COM_SHARED).read_bytes(), com_original)
        self.assertEqual((ENGINE / G_FRAME).read_bytes(), sp_original)

    def test_complete_original_frame_is_a_real_portable_engine_module(self):
        source = (ENGINE / G_FRAME).read_text(encoding='utf-8')
        frame = function_source(source, FRAME_SIGNATURE)
        # The moved algorithm is the accepted original frame at 5197a09,
        # with only the two invalid classname-ID casts corrected to the
        # engine's real string lookup. No shortened or stand-in frame.
        original = frame.replace('SL_ConvertToString(i->classname)', '(const char *)i->classname')
        original = original.replace('SL_ConvertToString(m->classname)', '(const char *)m->classname')
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(),
                         '4574a36a187560c11b394564c9be97608befe4923d9f85ef2287ffa8bcefe9bb')
        bootstrap = (ENGINE / 'src/game/g_main.cpp').read_text(encoding='utf-8')
        self.assertNotIn(FRAME_SIGNATURE, bootstrap)
        self.assertIn('${SRC_DIR}/game/g_runframe.cpp',
                      (ENGINE / 'scripts/sp/sp_files.cmake').read_text(encoding='utf-8'))

    def test_original_engine_pool_has_native_width_pointer_links(self):
        path = ENGINE / ENGINE_POOL
        source = path.read_bytes()
        text = source.decode("utf-8")
        self.assertTrue(text.startswith(POOL_PROLOGUE))
        for marker in POOL_REQUIRED:
            self.assertEqual(text.count(marker), 1)
        for marker in PORTABLE_POOL_MARKERS:
            self.assertIn(marker, text)
        for unsafe in UNSAFE_POOL_POINTERS:
            self.assertNotIn(unsafe, text)
        with TemporaryDirectory() as temp:
            out = Path(temp) / "port" / "pool_allocator.cpp"
            evidence = prepare_pool(ENGINE, out)
            self.assertEqual(evidence["source_sha256"], hashlib.sha256(source).hexdigest())
            self.assertTrue(evidence["pointer_truncation_removed_from_actual_iw3_engine"])
            self.assertFalse(evidence["sp_gameplay_frame_operational"])
            expected = '#include "iw3_android_pool_compat.h"\n#include "pool_allocator.h"\n'
            self.assertEqual(out.read_text(encoding="utf-8"), expected + text[len(POOL_PROLOGUE):])
            with self.assertRaisesRegex(ValueError, "Cannot overwrite"):
                prepare_pool(ENGINE, path)
        self.assertEqual(path.read_bytes(), source)

    def test_authentic_sp_hitloc_pointer_width_fix(self):
        path = ENGINE / HITLOC_SOURCE
        original = path.read_bytes()
        source = original.decode("utf-8")
        self.assertEqual(source.count(HITLOC_SIGNATURE), 1)
        with TemporaryDirectory() as temp:
            out = Path(temp) / "stage" / "iw3_g_combat_hitloc.cpp"
            evidence = prepare_hitloc(ENGINE, out)
            self.assertTrue(evidence["function_body_preserved"])
            self.assertTrue(evidence["win32_pointer_delta_removed_from_real_engine"])
            self.assertFalse(evidence["full_hitloc_damage_system_ported"])
            self.assertEqual(evidence["source_sha256"], hashlib.sha256(original).hexdigest())
            staged = out.read_text(encoding="utf-8")
            self.assertTrue(staged.startswith('#include "iw3_android_hitloc_compat.h"\n'))
            for marker in HITLOC_REQUIRED:
                self.assertIn(marker, staged)
            for marker in HITLOC_UNSAFE:
                self.assertNotIn(marker, staged)
            with self.assertRaisesRegex(ValueError, "Never overwrite"):
                prepare_hitloc(ENGINE, path)
        self.assertEqual(path.read_bytes(), original)

    def test_verbatim_original_iwd_filename_lookup_source(self):
        original_files = {
            IWD_SOURCE: (ENGINE / IWD_SOURCE).read_bytes(),
            IWD_SHARED: (ENGINE / IWD_SHARED).read_bytes(),
        }
        with TemporaryDirectory() as temp:
            out = Path(temp) / "stage" / "iw3_iwd_names.cpp"
            report = prepare_iwd_names(ENGINE, out)
            self.assertTrue(report["source_bodies_preserved"])
            self.assertTrue(report["iwd_filename_hash_and_compare_ported"])
            self.assertFalse(report["iwd_zip_archive_mount_ported"])
            self.assertFalse(report["fastfile_map_loading_ported"])
            self.assertFalse(report["playable_apk"])
            expected_bodies = [
                function_source(original_files[path].decode("utf-8"), signature)
                for signature, path in IWD_FUNCTIONS
            ]
            self.assertEqual(out.read_text(encoding="utf-8"),
                             IWD_HEADER + "\n\n".join(expected_bodies) + "\n")
            self.assertEqual(
                report["function_sha256"],
                [hashlib.sha256(body.encode("utf-8")).hexdigest()
                 for body in expected_bodies])
            with self.assertRaisesRegex(ValueError, "Never overwrite"):
                prepare_iwd_names(ENGINE, ENGINE / IWD_SOURCE)
        for path, raw in original_files.items():
            self.assertEqual((ENGINE / path).read_bytes(), raw)

    def test_android_touch_is_consumed_inside_original_cl_createcmd(self):
        source = (ENGINE / "src/client/cl_input.cpp").read_text(encoding="utf-8")
        self.assertIn(
            'extern "C" void z2026_platform_apply_touch_to_usercmd(usercmd_s *cmd, float *viewangles);',
            source)
        body = function_source(source, "void __cdecl CL_CreateCmd(usercmd_s *result)")
        call = "z2026_platform_apply_touch_to_usercmd(result, clients[0].viewangles);"
        self.assertIn("#if defined(__ANDROID__)\n        " + call + "\n#endif", body)
        self.assertLess(body.index(call), body.index("CL_FinishMove(result);"))
        platform = (ROOT / "android/iw3-native/iw3_android_platform.cpp").read_text(encoding="utf-8")
        bridge = function_source(platform, "extern \"C\" IW3_ANDROID_EXPORT void z2026_platform_apply_touch_to_usercmd(")
        self.assertIn("command->buttons |= BUTTON_ATTACK", bridge)
        self.assertIn("command->forwardmove", bridge)
        self.assertIn("viewangles[0]", bridge)
        self.assertIn("viewangles[1]", bridge)
        self.assertIn("g_pending_pitch_degrees = 0.0f;", bridge)
        self.assertIn("g_pending_yaw_degrees = 0.0f;", bridge)

    def test_original_iwd_mount_is_safe_for_native_pointer_width(self):
        source_path = ENGINE / "src/universal/com_files.cpp"
        source = source_path.read_text(encoding="utf-8")
        load_zip = function_source(
            source, "iwd_t *__cdecl FS_LoadZipFile(char *zipfile, char *basename)")
        # Invalid paths and names that cannot fit the real iwd_t fields must
        # be rejected before opening, rather than silently truncated.
        self.assertIn("if (!zipfile || !*zipfile || !basename || !*basename)", load_zip)
        self.assertIn("strlen(zipfile) >= sizeof(((iwd_t *)0)->iwdFilename)", load_zip)
        self.assertIn("strlen(basename) >= sizeof(((iwd_t *)0)->iwdBasename)", load_zip)
        # Invalid/unreadable archives must not pass a null handle into the
        # authentic ZIP parser; partially indexed archives must not be published.
        self.assertIn("uf = unzOpen(zipfile);", load_zip)
        self.assertIn("if (!uf)\n        return 0;", load_zip)
        self.assertIn("if (unzGetGlobalInfo(uf, &gi))", load_zip)
        self.assertIn("unzClose(uf);", load_zip)
        self.assertIn("if (!gi.number_entry || unzGoToFirstFile(uf) != UNZ_OK)", load_zip)
        self.assertIn("if (unzGetCurrentFileInfoPosition(uf, &buildBuffer[i].pos) != UNZ_OK)", load_zip)
        self.assertIn("if (i + 1 < gi.number_entry && unzGoToNextFile(uf) != UNZ_OK)", load_zip)
        self.assertIn("if (i != gi.number_entry)", load_zip)
        self.assertLess(load_zip.rindex("if (i != gi.number_entry)"),
                        load_zip.index("fs_iwdFileCount += gi.number_entry"))
        self.assertIn("Z_Free(iwd, 3);", load_zip)
        self.assertIn("Z_Free(buildBuffer, 3);", load_zip)
        # Preserve the full path: unzReOpen() passes iwdFilename directly to ZIP_fopen.
        # Trimming ".iwd" silently breaks cloned handles even when the archive indexed.
        self.assertIn('Keep the complete archive path, including ".iwd".', load_zip)
        self.assertIn("I_strncpyz(iwd->iwdFilename, zipfile, 256);", load_zip)
        self.assertNotIn("iwd->iwdFilename[iwdFilenameLength - 4] = 0;", load_zip)
        self.assertNotIn("strlen(iwd->iwdBasename) + 252", load_zip)

        # searchpath_s contains three pointers plus four integers. Its
        # historical 28-byte allocation is only valid for the original Win32 ABI.
        add_iwd = function_source(
            source, "void __cdecl FS_AddIwdFilesForGameDirectory(char *path, char *pszGameFolder)")
        add_dir = function_source(source, "void __cdecl FS_AddGameDirectory(")
        self.assertIn("Z_Malloc(sizeof(searchpath_s),", add_iwd)
        self.assertIn("Z_Malloc(sizeof(searchpath_s),", add_dir)
        self.assertIn("qsort(s0, numfiles, sizeof(s0[0]),", add_iwd)
        self.assertNotIn("qsort(s0, numfiles, 4u,", add_iwd)
        self.assertNotIn('Z_Malloc(28, "FS_AddIwdFilesForGameDirectory"', source)
        self.assertNotIn('Z_Malloc(28, "FS_AddGameDirectory"', source)
        add_search = function_source(source, "void __cdecl FS_AddSearchPath(searchpath_s *search)")
        self.assertIn("pSearch = &(*pSearch)->next;", add_search)
        self.assertNotIn("pSearch = (searchpath_s **)*pSearch;", add_search)

        header = (ENGINE / "src/universal/com_files.h").read_text(encoding="utf-8")
        self.assertIn("searchpath_s *next;", header)
        self.assertIn("iwd_t *iwd;", header)
        self.assertIn("directory_t *dir;", header)
        # This is source portability hardening only; com_files.cpp and the
        # complete search-path/gameplay runtime are not yet linked into Android.
        self.assertTrue(source_path.is_file())

    def test_original_fs_loadzipfile_staged_verbatim_and_native_width_safe(self):
        source_path = ENGINE / IWD_MOUNT_SOURCE
        original = source_path.read_bytes()
        original_text = original.decode("utf-8")
        body = function_source(original_text, IWD_MOUNT_SIGNATURE)
        with TemporaryDirectory() as temp:
            out = Path(temp) / "stage" / "fs_load_zip.cpp"
            report = prepare_iwd_mount(ENGINE, out)
            staged = out.read_text(encoding="utf-8")
            self.assertEqual(
                staged,
                '#include "iw3_android_iwd_mount_compat.h"\n' + body + "\n")
            self.assertTrue(report["function_body_preserved_verbatim"])
            self.assertTrue(report["native_width_index_allocation_guards"])
            self.assertTrue(report["null_allocation_cleanup_guards"])
            self.assertTrue(report["compiles_as_original_engine_static_module"])
            self.assertTrue(report["source_staged_for_android_diagnostic_link"])
            self.assertFalse(report["linkage_verified_by_build_ci"])
            self.assertFalse(report["runtime_execution_proven"])
            self.assertFalse(report["real_iwd_searchpath_mount_proven"])
            self.assertFalse(report["playable_apk"])
            for marker in IWD_MOUNT_REQUIRED:
                self.assertIn(marker, staged)
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                prepare_iwd_mount(ENGINE, source_path)
        self.assertEqual(source_path.read_bytes(), original)
        self.assertIn("file_info.size_filename >= sizeof(filename_inzip)", body)
        nul_name_guard = "if (!file_info.size_filename || strlen(filename_inzip) != file_info.size_filename)"
        self.assertEqual(body.count(nul_name_guard), 2)
        sizing_guard = body.index(nul_name_guard)
        sizing_length = body.index("const uint32_t nameBytes", sizing_guard)
        self.assertLess(sizing_guard, sizing_length)
        second_pass = body.index("if (unzGoToFirstFile(uf) != UNZ_OK)")
        second_guard = body.index(nul_name_guard, second_pass)
        crc_record = body.index("if (file_info.uncompressed_size)", second_pass)
        self.assertLess(second_guard, crc_record)
        self.assertIn("len > (uint32_t)INT_MAX - gi.number_entry * sizeof(fileInIwd_s)", body)
        self.assertIn("if (!buildBuffer)", body)
        self.assertIn("if (!fs_headerLongs)", body)
        self.assertIn("if (!iwd)", body)
        self.assertLess(body.index("if (!buildBuffer)"), body.index("namePtr ="))
        self.assertLess(body.index("if (!fs_headerLongs)"), body.index("for (i = 1;"))
        self.assertLess(body.index("if (!iwd)"), body.index("iwd->hashSize = i"))


    def test_original_iwd_searchpath_source_is_staged_and_exercised(self):
        source_path = ENGINE / IWD_SEARCHPATH_SOURCE
        original = source_path.read_bytes()
        body = function_source(original.decode("utf-8"), IWD_SEARCHPATH_SIGNATURE)
        for marker in IWD_SEARCHPATH_REQUIRED:
            self.assertIn(marker, body)
        self.assertNotIn("pSearch = (searchpath_s **)*pSearch;", body)
        with TemporaryDirectory() as temp:
            out = Path(temp) / "stage" / "iw3_iwd_searchpath.cpp"
            report = prepare_iwd_searchpath(ENGINE, out)
            staged = out.read_text(encoding="utf-8")
            expected = ('#include "iw3_android_iwd_mount_compat.h"\n'
                        'searchpath_s *fs_searchpaths = nullptr;\n\n' + body + "\n")
            self.assertEqual(staged, expected)
            self.assertTrue(report["function_body_preserved_verbatim_from_vendored_source"])
            self.assertTrue(report["pointer_traversal_uses_next_member_address"])
            self.assertTrue(report["original_localized_insertion_order_preserved"])
            self.assertFalse(report["real_game_iwd_mounted"])
            self.assertFalse(report["playable_apk"])
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                prepare_iwd_searchpath(ENGINE, source_path)
        self.assertEqual(source_path.read_bytes(), original)
        smoke = (ROOT / "android/iw3-native/iw3_unzip_native_smoke.cpp").read_text(encoding="utf-8")
        self.assertIn("FS_AddSearchPath(search);", smoke)
        self.assertIn("fs_searchpaths == search", smoke)
        self.assertIn("search->iwd = iwd;", smoke)
        self.assertIn("cursor->iwd == iwd", smoke)
        jni = (ROOT / "android/iw3-native/iw3_android_jni.cpp").read_text(encoding="utf-8")
        self.assertIn("IW3_JNI_IWD_SEARCHPATH_%s", jni)

    def test_original_iwd_directory_scanner_is_staged_and_fails_closed(self):
        source = (ENGINE / "src/universal/com_files.cpp").read_text(encoding="utf-8")
        scanner = function_source(
            source,
            "void __cdecl FS_AddIwdFilesForGameDirectory(char *path, char *pszGameFolder)",
        )
        self.assertLess(scanner.index("numfiles = 0;"),
                        scanner.index('list = Sys_ListFiles(ospath, "iwd", 0, &numfiles, 0);'))
        self.assertIn("if (!list || numfiles <= 0)", scanner)
        self.assertIn("qsort(s0, numfiles, sizeof(s0[0]),", scanner)
        self.assertNotIn("qsort(s0, numfiles, 4u,", scanner)
        game_directory = function_source(
            source,
            "void __cdecl FS_AddGameDirectory(char *path, char *dir, int bLanguageDirectory, int iLanguage)",
        )
        self.assertIn("I_strncpyz(fs_gamedir, szGameFolder, 256);", game_directory)
        self.assertIn("FS_AddSearchPath(search);", game_directory)
        self.assertIn("FS_AddIwdFilesForGameDirectory(path, szGameFolder);", game_directory)
        self.assertIn("Z_Malloc(sizeof(searchpath_s), \"FS_AddGameDirectory\", 3)", game_directory)
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "iw3_iwd_directory.cpp"
            evidence = prepare_iwd_directory(ENGINE, output)
            staged = output.read_text(encoding="utf-8")
            self.assertTrue(evidence["original_directory_scanner_preserved_from_vendored_source"])
            self.assertTrue(evidence["null_or_failed_directory_listing_fails_closed"])
            self.assertTrue(evidence["native_pointer_width_qsort"])
            self.assertTrue(evidence["original_game_directory_registration_preserved_from_vendored_source"])
            self.assertTrue(evidence["game_directory_source_staged_for_android_diagnostic"])
            self.assertFalse(evidence["real_game_iwd_mounted"])
            self.assertIn("void __cdecl FS_AddGameDirectory", staged)
            for marker in IWD_DIRECTORY_REQUIRED:
                self.assertIn(marker, staged)
        smoke = (ROOT / "android/iw3-native/iw3_unzip_native_smoke.cpp").read_text(encoding="utf-8")
        self.assertIn("FS_AddGameDirectory(root_copy, game_copy, 0, 0);", smoke)
        self.assertIn("directory_node->dir->path, root_copy", smoke)
        self.assertIn("std::memcpy(fs_gamedir, previous_gamedir", smoke)
        platform = (ROOT / "android/iw3-native/iw3_android_platform.cpp").read_text(encoding="utf-8")
        self.assertIn("z2026_platform_directory_has_contents", platform)
        self.assertIn("AT_SYMLINK_NOFOLLOW", platform)
        self.assertEqual((ENGINE / "src/universal/com_files.cpp").read_text(encoding="utf-8"),
                         source)

    def test_iwd_localized_prefix_clear_is_arm64_safe(self):
        source = (ENGINE / "src/universal/com_files.cpp").read_text(encoding="utf-8")
        scan = function_source(
            source,
            "void __cdecl FS_AddIwdFilesForGameDirectory(char *path, char *pszGameFolder)",
        )
        self.assertIn('qmemcpy(v2, "          ", 10);', scan)
        self.assertIn("same 10-byte result on ARM64", scan)
        self.assertNotIn("*(_DWORD *)v2", scan)
        self.assertNotIn("*((_DWORD *)v2 + 1)", scan)
        self.assertNotIn("*((_WORD *)v2 + 4)", scan)
        self.assertIn("qsort(s0, numfiles, sizeof(s0[0]),", scan)

    def test_no_vendor_overwrite(self):
        with self.assertRaisesRegex(ValueError, "Refusing"):
            prepare(ENGINE, ENGINE / ENGINE_FILE)

    def test_real_physics_pool_caller_tracks_native_payload_size(self):
        source = (ENGINE / 'src/physics/phys_ode.cpp').read_text(encoding='utf-8')
        init = function_source(source, 'void __cdecl Phys_Init()')
        self.assertIn('INIT_STATIC_POOL(physGlob.userData, &physGlob.userDataPool);', init)
        self.assertNotIn('0x70u', init)
        local = (ENGINE / 'src/physics/phys_local.h').read_text(encoding='utf-8')
        self.assertIn('#include "phys_userdata.h"', local)
        self.assertIn('PhysObjUserData userData[512]', local)


    def test_original_iwd_runtime_services_are_verbatim_and_safe_to_stage(self):
        source_paths = {path for _, path in IWD_SERVICE_FUNCTIONS}
        source_paths.add(IWD_MOUNT_SOURCE)
        original_files = {path: (ENGINE / path).read_bytes() for path in source_paths}
        with TemporaryDirectory() as temp:
            out = Path(temp) / "stage" / "iw3_iwd_services.cpp"
            report = prepare_iwd_services(ENGINE, out)
            staged = out.read_text(encoding="utf-8")
            self.assertTrue(report["function_bodies_preserved_verbatim"])
            self.assertTrue(report["original_allocator_and_free_staged"])
            self.assertTrue(report["original_checksum_algorithm_staged"])
            self.assertTrue(report["original_string_helpers_staged"])
            self.assertTrue(report["iwd_state_globals_from_original_source"])
            self.assertFalse(report["playable_apk"])
            for marker in IWD_SERVICE_REQUIRED:
                self.assertIn(marker, staged)
            for signature, path in IWD_SERVICE_FUNCTIONS:
                body = function_source(original_files[path].decode("utf-8"), signature)
                self.assertIn(body, staged)
            self.assertIn("int fs_iwdFileCount;", staged)
            self.assertIn("int fs_checksumFeed;", staged)
            self.assertIn("#define iassert(expr) assert(expr)", staged)
            with self.assertRaisesRegex(ValueError, "Never overwrite"):
                prepare_iwd_services(ENGINE, ENGINE / Path("src/universal/com_files.cpp"))
        for path, raw in original_files.items():
            self.assertEqual((ENGINE / path).read_bytes(), raw)

    def test_original_file_lookup_branch_is_preserved_without_claiming_fs_read(self):
        source_path = ENGINE / "src/universal/com_files.cpp"
        original = source_path.read_bytes()
        original_text = original.decode("utf-8")
        full_open = function_source(original_text, IWD_LOOKUP_OPEN_SIGNATURE)
        start = full_open.index(IWD_LOOKUP_PREFIX_START)
        end = full_open.index(IWD_LOOKUP_PREFIX_END, start)
        expected_prefix = full_open[start:end]
        with TemporaryDirectory() as temp:
            output = Path(temp) / "stage" / "iw3_iwd_lookup.cpp"
            evidence = prepare_iwd_lookup(ENGINE, output)
            staged = output.read_text(encoding="utf-8")
            self.assertTrue(evidence["original_searchpath_lookup_prefix_preserved_verbatim"])
            self.assertTrue(evidence["original_filename_sanitizer_preserved"])
            self.assertTrue(evidence["original_iwd_hash_and_filename_compare_used"])
            self.assertFalse(evidence["file_handle_allocation_ported"])
            self.assertFalse(evidence["original_FS_Read_ported"])
            self.assertFalse(evidence["playable_apk"])
            self.assertIn(expected_prefix, staged)
            self.assertIn("void __cdecl FS_ReplaceSeparators(char *path)", staged)
            self.assertIn("FS_ReplaceSeparators(ospath);", staged)
            self.assertIn("z2026_iw3_original_searchpath_lookup", staged)
            self.assertNotIn("FS_HandleForFile(thread)", staged)
            for marker in IWD_LOOKUP_REQUIRED:
                self.assertIn(marker, staged)
        self.assertEqual(source_path.read_bytes(), original)

    def test_lookup_probe_is_wired_to_ci_but_keeps_read_path_explicitly_pending(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        smoke = (ROOT / "android/iw3-native/iw3_unzip_native_smoke.cpp").read_text(encoding="utf-8")
        jni = (ROOT / "android/iw3-native/iw3_android_jni.cpp").read_text(encoding="utf-8")
        validator = (ROOT / "tools/iw3_android/verify_runtime_evidence.py").read_text(encoding="utf-8")
        self.assertIn("IW3_EXTRACTED_IWD_LOOKUP", cmake)
        self.assertIn("iw3_android_iwd_lookup_io.cpp", cmake)
        self.assertIn("z2026_iw3_original_searchpath_lookup", smoke)
        self.assertIn("iwd->iwdFilename, reinterpret_cast<unzFile>(iwd->handle)", smoke)
        self.assertIn("cloned_handle_reopen_read_ok", smoke)
        self.assertIn("std::strcmp(iwd->iwdFilename, path) == 0", smoke)
        self.assertIn("maps/iw3_android_missing.txt", smoke)
        self.assertIn("../maps/iw3_android_probe.txt", smoke)
        self.assertIn("IW3_JNI_IWD_LOOKUP_%s", jni)
        self.assertIn("IW3_JNI_IWD_LOOKUP_PASS", validator)
        self.assertIn("original_fs_read_handle_path_executed", validator)
        for workflow in (
            ".github/workflows/iw3-original-android-jni.yml",
            ".github/workflows/iw3-original-android-emulator-jni.yml",
            ".github/workflows/iw3-original-native-android.yml",
        ):
            content = (ROOT / workflow).read_text(encoding="utf-8")
            self.assertIn("prepare_real_engine_iwd_lookup.py", content)
            self.assertIn("iw3_iwd_lookup.cpp", content)

if __name__ == "__main__":
    unittest.main()
