"""Regression coverage for staging the original KisakCOD Cmd_Argc/Cmd_Argv bodies."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD/src/qcommon/cmd.cpp"
GENERATOR = ROOT / "tools/iw3_android/prepare_real_engine_cmd_args.py"
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"
WORKFLOW = ROOT / ".github/workflows/iw3-original-native-android.yml"


class OriginalCommandArgumentAccessorTests(unittest.TestCase):
    def test_original_upstream_bodies_are_still_the_source_of_truth(self):
        source = ENGINE.read_text(encoding="utf-8")
        self.assertIn("int32_t \tCmd_Argc(void)", source)
        self.assertIn("const char* Cmd_Argv(int32_t  arg)", source)
        self.assertIn("return cmd_args.argc[cmd_args.nesting];", source)
        self.assertIn("return (char*)(cmd_args.argv[cmd_args.nesting][arg]);", source)

    def test_extractor_keeps_only_real_accessors_and_not_a_duplicate_state_object(self):
        generator = GENERATOR.read_text(encoding="utf-8")
        self.assertIn('SOURCE = Path("src/qcommon/cmd.cpp")', generator)
        self.assertIn('"int32_t \\tCmd_Argc(void)"', generator)
        self.assertIn('"const char* Cmd_Argv(int32_t  arg)"', generator)
        self.assertIn('"cmd_args_state_definition_in_audit_archive": False', generator)
        self.assertIn('"playable_apk": False', generator)

    def test_cmake_compiles_the_original_accessor_archive_and_host_runtime_test(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        self.assertIn("add_library(iw3_sp_cmd_args STATIC", cmake)
        self.assertIn("add_executable(iw3_cmd_args_native_test cmd_args_native_test.cpp)", cmake)
        self.assertIn("iw3_original_cmd_arg_accessors_host_runtime", cmake)
        self.assertIn("target_link_libraries(iw3_cmd_args_native_test PRIVATE iw3_sp_cmd_args)", cmake)

    def test_workflow_extracts_and_passes_the_archive_to_both_abi_builds(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("prepare_real_engine_cmd_args.py", workflow)
        self.assertIn('-DIW3_EXTRACTED_CMD_ARGS="$RUNNER_TEMP/iw3-source/iw3_cmd_args.cpp"', workflow)
        self.assertIn('libiw3_sp_cmd_args.a', workflow)
        self.assertIn("IW3_ORIGINAL_CMD_ARG_ACCESSORS_AARCH64_LINK_GREEN", workflow)

    def test_combined_audit_requires_accessors_defined_but_keeps_state_visible(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Cmd_Argc()", workflow)
        self.assertIn("Cmd_Argv(int)", workflow)
        self.assertIn("cmd_args", workflow)
        self.assertIn("IW3_FS_STARTUP_RUNTIME_INVOKED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)


if __name__ == "__main__":
    unittest.main()
