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
        # The original decompilation indexed a 256-byte path with
        # basenameLength + 252, which is out of bounds for ordinary *.iwd names.
        self.assertIn("const size_t iwdFilenameLength = strlen(iwd->iwdFilename);", load_zip)
        self.assertIn("iwd->iwdFilename + iwdFilenameLength - 4", load_zip)
        self.assertIn("iwd->iwdFilename[iwdFilenameLength - 4] = 0;", load_zip)
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
            self.assertFalse(report["linked_to_android_diagnostic_apk"])
            self.assertFalse(report["real_iwd_searchpath_mount_proven"])
            self.assertFalse(report["playable_apk"])
            for marker in IWD_MOUNT_REQUIRED:
                self.assertIn(marker, staged)
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                prepare_iwd_mount(ENGINE, source_path)
        self.assertEqual(source_path.read_bytes(), original)
        self.assertIn("file_info.size_filename >= sizeof(filename_inzip)", body)
        self.assertIn("len > (uint32_t)INT_MAX - gi.number_entry * sizeof(fileInIwd_s)", body)
        self.assertIn("if (!buildBuffer)", body)
        self.assertIn("if (!fs_headerLongs)", body)
        self.assertIn("if (!iwd)", body)
        self.assertLess(body.index("if (!buildBuffer)"), body.index("namePtr ="))
        self.assertLess(body.index("if (!fs_headerLongs)"), body.index("for (i = 1;"))
        self.assertLess(body.index("if (!iwd)"), body.index("iwd->hashSize = i"))

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


if __name__ == "__main__":
    unittest.main()
