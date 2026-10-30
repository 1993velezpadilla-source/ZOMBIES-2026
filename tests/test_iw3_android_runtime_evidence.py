from pathlib import Path
import unittest

from tools.iw3_android.verify_runtime_evidence import REQUIRED, verify


ROOT = Path(__file__).resolve().parents[1]
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"
TABLE = ROOT / "third_party/KisakCOD/src/universal/com_files_handle_table.cpp"
COMPAT = ROOT / "android/iw3-native/iw3_android_fs_read_compat.h"
JNI = ROOT / "android/iw3-native/iw3_android_jni.cpp"


def real_format_fixture():
    # Parser regression fixture only; never device or gameplay evidence.
    return "\n".join(REQUIRED) + "\n" + "\n".join((
        "IW3_JNI_LIFECYCLE_2",
        "IW3_JNI_TOUCH id=1 pressed=1 coords=0.08,0.88",
        "IW3_JNI_USERCMD attack=0 buttons=2 forward=0 right=0 pitch=0 yaw=0",
        "IW3_JNI_TOUCH id=1 pressed=0 coords=0.08,0.88",
        "IW3_JNI_TOUCH id=2 pressed=1 coords=0.27,0.88",
        "IW3_JNI_USERCMD attack=0 buttons=514 forward=0 right=0 pitch=0 yaw=0",
        "IW3_JNI_TOUCH id=2 pressed=0 coords=0.27,0.88",
        "IW3_JNI_TOUCH id=0 pressed=1 coords=0.90,0.85",
        "IW3_JNI_USERCMD attack=1 buttons=1 forward=0 right=0 pitch=0 yaw=0",
        "IW3_JNI_TOUCH id=0 pressed=0 coords=0.90,0.85",
        "IW3_JNI_LIFECYCLE_3", "IW3_JNI_LIFECYCLE_2"))


class NativeRuntimeEvidenceTests(unittest.TestCase):
    def test_diagnostic_links_and_executes_original_shared_fsh_table(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        start = cmake.index("add_library(iw3_sp_math SHARED")
        end = cmake.index("target_include_directories(iw3_sp_math", start)
        shared_target = cmake[start:end]
        self.assertIn("com_files_handle_table.cpp", shared_target)
        self.assertIn("EXTRACTED_FS_READ", shared_target)
        self.assertIn("fileHandleData_t fsh[65] = {};", TABLE.read_text(encoding="utf-8"))
        self.assertIn("extern fileHandleData_t fsh[65];", COMPAT.read_text(encoding="utf-8"))
        jni = JNI.read_text(encoding="utf-8")
        self.assertIn("IW3_JNI_FSH_TABLE_SHARED_%s", jni)
        self.assertIn('iwd_fs_read_ok ? "PASS" : "FAIL"', jni)

    def test_complete_diagnostic_has_explicit_limits(self):
        result = verify(real_format_fixture())
        self.assertTrue(result["touch_down_and_up_read_back_from_native"])
        self.assertTrue(result["sprint_touch_reached_diagnostic_usercmd_s_adapter"])
        self.assertTrue(result["slide_chord_touch_reached_diagnostic_usercmd_s_adapter"])
        self.assertTrue(result["original_fs_addsearchpath_inserted_fixture_executed"])
        self.assertTrue(result["original_fs_addiwdfiles_directory_scan_executed"])
        self.assertTrue(result["original_fs_add_game_directory_registered_fixture_executed"])
        self.assertTrue(result["original_fs_fopenfileread_searchpath_lookup_branch_executed"])
        self.assertTrue(result["original_fs_read_iwd_zip_branch_executed"])
        self.assertTrue(result["original_fs_read_handle_path_executed"])
        self.assertTrue(result["original_fs_open_read_close_lifecycle_executed"])
        self.assertTrue(result["original_fs_iwd_clone_handle_path_executed"])
        self.assertTrue(result["original_fs_directory_open_read_close_lifecycle_executed"])
        self.assertTrue(result["original_fs_directory_fallback_read_executed"])
        self.assertTrue(result["original_upstream_fsh_table_integrated"])
        self.assertFalse(result["full_original_com_files_translation_unit_linked"])
        self.assertFalse(result["arm64_device_execution_proven"])
        self.assertFalse(result["gameplay_proven"])
        self.assertFalse(result["original_cl_createcmd_touch_consumption_proven"])
        self.assertFalse(result["original_client_runtime_linked"])
        self.assertFalse(result["real_map_loaded"])
        self.assertFalse(result["renderer_frame_proven"])
        self.assertFalse(result["playable_apk"])
        self.assertNotIn("touch_translated_to_original_iw3_usercmd_s", result)
        self.assertNotIn("sprint_touch_reached_original_usercmd_s", result)
        self.assertNotIn("slide_chord_touch_reached_original_usercmd_s", result)

    def test_every_required_native_marker_is_necessary(self):
        for marker in REQUIRED:
            with self.subTest(marker=marker), self.assertRaises(ValueError):
                verify(real_format_fixture().replace(marker, ""))

    def test_any_runtime_failure_overrides_passing_markers(self):
        for failure in ("TOUCH_NATIVE_REJECTED", "JNI_RESUME_FAILED",
                        "Fatal signal", "IW3_JNI_UNZIP_PARSER_FAIL",
                        "IW3_JNI_IWD_MOUNT_FAIL", "IW3_JNI_IWD_LOOKUP_FAIL",
                        "IW3_JNI_IWD_FS_READ_FAIL",
                        "IW3_JNI_IWD_FS_OPEN_READ_CLOSE_FAIL",
                        "IW3_JNI_IWD_FS_CLONE_FAIL",
                        "IW3_JNI_FS_DIRECTORY_OPEN_READ_CLOSE_FAIL",
                        "JNI_NATIVE_ENGINE_PROBE_FAIL"):
            with self.subTest(failure=failure), self.assertRaises(ValueError):
                verify(real_format_fixture() + "\n" + failure)

    def test_sprint_and_slide_chord_must_reach_original_usercmd_bits(self):
        sprint = "IW3_JNI_USERCMD attack=0 buttons=2 forward=0 right=0 pitch=0 yaw=0"
        slide = "IW3_JNI_USERCMD attack=0 buttons=514 forward=0 right=0 pitch=0 yaw=0"
        for line in (
            "IW3_JNI_USERCMD attack=0 buttons=0 forward=0 right=0 pitch=0 yaw=0",
            "IW3_JNI_USERCMD attack=0 buttons=512 forward=0 right=0 pitch=0 yaw=0",
        ):
            with self.subTest(line=line), self.assertRaises(ValueError):
                verify(real_format_fixture().replace(sprint, line))
        with self.assertRaises(ValueError):
            verify(real_format_fixture().replace(slide,
                "IW3_JNI_USERCMD attack=0 buttons=2 forward=0 right=0 pitch=0 yaw=0"))

    def test_touch_must_reach_original_usercmd_attack_bit(self):
        valid = "IW3_JNI_USERCMD attack=1 buttons=1 forward=0 right=0 pitch=0 yaw=0"
        for line in (
            "IW3_JNI_USERCMD attack=0 buttons=0 forward=0 right=0 pitch=0 yaw=0",
            "IW3_JNI_USERCMD attack=1 buttons=0 forward=0 right=0 pitch=0 yaw=0",
        ):
            with self.subTest(line=line), self.assertRaises(ValueError):
                verify(real_format_fixture().replace(valid, line))

    def test_missing_release_is_not_working_touch(self):
        with self.assertRaises(ValueError):
            verify(real_format_fixture().replace("pressed=0", "pressed=1"))

    def test_wrong_pointer_or_failed_native_readback_is_rejected(self):
        for substitution in ("id=1 pressed=0", "id=0 pressed=-1"):
            with self.subTest(substitution=substitution), self.assertRaises(ValueError):
                verify(real_format_fixture().replace("id=0 pressed=0", substitution))

    def test_sparse_android_pointer_id_31_is_valid_but_32_is_rejected(self):
        base = real_format_fixture()
        marker = "IW3_JNI_LIFECYCLE_3"
        valid_sparse = base.replace(
            marker,
            "IW3_JNI_TOUCH id=31 pressed=1 coords=0.50,0.50\n"
            "IW3_JNI_TOUCH id=31 pressed=0 coords=0.50,0.50\n" + marker)
        self.assertTrue(verify(valid_sparse)["touch_down_and_up_read_back_from_native"])

        invalid_sparse = valid_sparse.replace("id=31 pressed=1", "id=32 pressed=1")
        with self.assertRaisesRegex(ValueError, "pointer ID must be 0..31"):
            verify(invalid_sparse)

    def test_invalid_coordinate_is_rejected(self):
        for coord in ("nan", "inf", "-0.1", "1.1"):
            with self.subTest(coord=coord), self.assertRaises(ValueError):
                verify(real_format_fixture().replace("coords=0.08,", "coords=" + coord + ","))

    def test_background_and_return_are_both_required(self):
        with self.assertRaises(ValueError):
            verify(real_format_fixture().replace("IW3_JNI_LIFECYCLE_3", ""))
        with self.assertRaises(ValueError):
            verify(real_format_fixture().rsplit("IW3_JNI_LIFECYCLE_2", 1)[0])

    def test_initial_landscape_recreation_uses_current_activity(self):
        initial = "\n".join(REQUIRED) + "\nIW3_JNI_LIFECYCLE_2\n"
        initial += "IW3_JNI_LIFECYCLE_3\nIW3_JNI_LIFECYCLE_4\n"
        self.assertTrue(verify(initial + real_format_fixture())[
            "touch_down_and_up_read_back_from_native"])

    def test_previous_activity_touch_cannot_validate_new_instance(self):
        fresh_without_touch = "\n".join(REQUIRED) + "\n" + "\n".join((
            "IW3_JNI_LIFECYCLE_2", "IW3_JNI_LIFECYCLE_3", "IW3_JNI_LIFECYCLE_2"))
        with self.assertRaises(ValueError):
            verify(real_format_fixture() + "\nIW3_JNI_LIFECYCLE_4\n" + fresh_without_touch)


if __name__ == "__main__":
    unittest.main()
