"""Guard the authentic IW3 SP client-command queue against Win32-sized copies."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/client/cl_input.cpp"
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"
WORKFLOW = ROOT / ".github/workflows/iw3-original-native-android.yml"


def function_body(source: str, signature: str) -> str:
    start = source.find(signature)
    if start < 0 or source.find(signature, start + 1) >= 0:
        raise AssertionError(f"expected exactly one function signature: {signature}")
    opening = source.find("{", start)
    if opening < 0:
        raise AssertionError("function opening brace missing")
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1:index]
    raise AssertionError("function closing brace missing")


class OriginalClientInputAbiTests(unittest.TestCase):
    def test_command_queue_copy_uses_native_usercmd_size(self):
        source = SOURCE.read_text(encoding="utf-8")
        body = function_body(source, "void CL_CreateNewCommands()")
        self.assertIn("usercmd_s command;", body)
        self.assertIn("CL_CreateCmd(&command);", body)
        self.assertIn("const unsigned int nextCommand = (++clients[0].cmdNumber) & 0x3F;", body)
        self.assertIn("memcpy(&clients[0].cmds[nextCommand], &command, sizeof(command));", body)
        self.assertNotIn("_BYTE v1[56]", body)
        self.assertNotIn("sizeof(v1)", body)
        self.assertNotIn("cmdNumber) & 0x3F], v1", body)

    def test_android_touch_hook_stays_inside_original_createcmd_path(self):
        source = SOURCE.read_text(encoding="utf-8")
        body = function_body(source, "void __cdecl CL_CreateCmd(usercmd_s *result)")
        positions = [
            body.find("CL_CmdButtons(result);"),
            body.find("CL_KeyMove(result);"),
            body.find("CL_MouseMove(result);"),
            body.find("z2026_platform_apply_touch_to_usercmd(result, clients[0].viewangles);"),
            body.find("CL_FinishMove(result);"),
        ]
        self.assertTrue(all(position >= 0 for position in positions))
        self.assertEqual(positions, sorted(positions))
        self.assertIn("#if defined(__ANDROID__)", body)

    def test_arm64_build_compiles_but_does_not_claim_runtime_link(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        self.assertIn('add_library(iw3_sp_client_input STATIC "${IW3_ENGINE_SOURCE_ROOT}/client/cl_input.cpp")', cmake)
        self.assertIn("This is an audit archive, not yet linked", cmake)
        self.assertNotIn("iw3_sp_client_input)", cmake)
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("libiw3_sp_client_input.a", workflow)
        self.assertIn("CL_CreateCmd(usercmd_s*)", workflow)
        self.assertIn("z2026_platform_apply_touch_to_usercmd", workflow)
        self.assertIn("NOT_LINKED", workflow)


if __name__ == "__main__":
    unittest.main()
