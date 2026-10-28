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

    def test_emulator_probe_observes_usercmd_snapshot_from_jni_touch(self):
        jni = (ROOT / "android/iw3-native/iw3_android_jni.cpp").read_text(encoding="utf-8")
        probe = (ROOT / "tools/iw3_android/run_emulator_probe.sh").read_text(encoding="utf-8")
        self.assertIn('#include "iw3_android_usercmd_compat.h"', jni)
        self.assertIn("z2026_platform_usercmd_snapshot(0, fields, 10)", jni)
        self.assertIn('"IW3_JNI_USERCMD attack=%d buttons=%d touch_result=%d"', jni)
        self.assertIn("grep -F 'IW3_JNI_USERCMD attack=1'", probe)
        self.assertIn("grep -E 'IW3_JNI_USERCMD attack=0 buttons=2 '", probe)
        self.assertIn("grep -E 'IW3_JNI_USERCMD attack=0 buttons=514 '", probe)
        self.assertIn("NOT a game engine", jni)

    def test_native_layout_guards_preserve_win32_and_lp64(self):
        bg = (ROOT / "third_party/KisakCOD/src/bgame/bg_local.h").read_text(encoding="utf-8")
        memtree = (ROOT / "third_party/KisakCOD/src/script/scr_memorytree.h").read_text(encoding="utf-8")
        stringlist = (ROOT / "third_party/KisakCOD/src/script/scr_stringlist.h").read_text(encoding="utf-8")
        ui = (ROOT / "third_party/KisakCOD/src/ui/ui_shared.h").read_text(encoding="utf-8")
        font = (ROOT / "third_party/KisakCOD/src/gfx_d3d/r_font.h").read_text(encoding="utf-8")
        self.assertIn("static_assert(sizeof(struct scr_anim_s) == 0x8);", bg)
        self.assertIn("static_assert(sizeof(struct scr_anim_s) == 0x4);", bg)
        self.assertIn("static_assert(sizeof(animScriptCommand_t) == 0x18);", bg)
        self.assertIn("static_assert(sizeof(animScriptCommand_t) == 0x10);", bg)
        self.assertIn("struct alignas(8) animation_s", bg)
        self.assertIn("struct alignas(128) scrMemTreeGlob_t", memtree)
        self.assertIn("struct alignas(128) scrStringGlob_t", stringlist)
        self.assertIn("struct alignas(16) token_s", ui)
        self.assertIn("struct alignas(16) value_s", ui)
        self.assertIn("struct alignas(16) script_s", ui)
        self.assertIn("static_assert(sizeof(Font_s) == 40);", font)
        self.assertIn("static_assert(sizeof(Font_s) == 24);", font)

    def test_d3d_bound_client_input_is_not_misreported_as_android_runtime(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        docs = (ROOT / "docs/IW3_ANDROID_NATIVE_PORT.md").read_text(encoding="utf-8")
        self.assertNotIn("add_library(iw3_sp_client_input STATIC", cmake)
        self.assertNotIn('target_sources(iw3_sp_math PRIVATE "${IW3_ENGINE_SOURCE_ROOT}/client/cl_input.cpp")', cmake)
        self.assertNotIn("libiw3_sp_client_input.a", workflow)
        self.assertIn("CL_CreateCmd", docs)
        self.assertIn("d3d9.h", docs)
        self.assertIn("not produce a playable APK", docs)


if __name__ == "__main__":
    unittest.main()
