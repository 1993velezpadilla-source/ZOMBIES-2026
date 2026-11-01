"""ARM64 LP64 regressions for genuine IW3 renderer command-buffer producers.

Uses the original TRACK_r_rendercmds body (not a fake renderer) in an ASan/UBSan
host harness. Also checks that the five original pointer-bearing command
producers reserve their native C++ type size. No GLES frame/gameplay claimed.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_rendercmds.cpp"


class OriginalRendererCommandLP64Tests(unittest.TestCase):
    def test_pointer_bearing_commands_reserve_native_abi_size(self):
        src = SOURCE.read_text(encoding="utf-8")
        pairs = (
            ("RC_FIRST_NONCRITICAL", "GfxCmdStretchPic"),
            ("RC_STRETCH_PIC_FLIP_ST", "GfxCmdStretchPic"),
            ("RC_STRETCH_PIC_ROTATE_XY", "GfxCmdStretchPicRotateXY"),
            ("RC_STRETCH_PIC_ROTATE_ST", "GfxCmdStretchPicRotateST"),
            ("RC_DRAW_QUAD_PIC", "GfxCmdDrawQuadPic"),
        )
        for command, command_type in pairs:
            expression = (
                f"({command_type} *)R_GetCommandBuffer("
                f"{command}, sizeof(*cmd))"
            )
            self.assertIn(expression, src, command)

    def test_android_render_commands_keep_original_cinematic_call_without_bink_headers(self):
        src = SOURCE.read_text(encoding="utf-8")
        android, desktop = src.split("#if defined(__ANDROID__)", 1)[1].split(
            "#else", 1
        )
        self.assertIn("void __cdecl R_Cinematic_UpdateFrame();", android)
        self.assertIn('#include "r_cinematic.h"', desktop)
        self.assertIn("R_Cinematic_UpdateFrame();", src)
        # No Bink implementation or synthetic replacement is introduced.

    def test_android_dynamic_mesh_teardown_never_fakes_d3d_release(self):
        src = SOURCE.read_text(encoding="utf-8")
        original = function_source(src, "void __cdecl R_ShutdownDynamicMesh(GfxMeshData *mesh)")
        self.assertIn("#if defined(__ANDROID__)", original)
        self.assertIn(
            "dynamic vertex buffer teardown requires real GLES resource ownership",
            original,
        )
        self.assertIn("Com_Error(ERR_FATAL", original)
        self.assertIn("#else", original)
        self.assertIn("R_ReleaseAndSetNULL<IDirect3DDevice9>", original)

    def test_original_renderer_command_globals_track_native_sizes(self):
        src = SOURCE.read_text(encoding="utf-8")
        original = function_source(src, "void __cdecl TRACK_r_rendercmds()")
        names = (
            "s_backEndData", "g_viewInfo", "g_frontEndCmds",
            "s_debugFrameGlob", "g_debugFrontEndCmds",
        )
        for name in names:
            self.assertIn(f"sizeof({name})", original)
        for old in ("2346752", "212352", "1173632"):
            self.assertNotIn(old, original)

        fixture = r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <vector>
#define __cdecl
struct BackEnd { void* pointers[9]; uint8_t bytes[13]; };
struct ViewInfo { void* pointers[7]; uint8_t bytes[21]; };
struct CommandArray { uint8_t* cmds; int usedTotal; int usedCritical; void* lastCmd; };
struct DebugFrame { void* pointers[11]; uint8_t bytes[7]; };
BackEnd s_backEndData[2]{};
ViewInfo g_viewInfo[2][4]{};
CommandArray g_frontEndCmds[2]{};
DebugFrame s_debugFrameGlob{};
CommandArray g_debugFrontEndCmds{};
struct Record { const void* addr; size_t size; const char* name; int kind; };
std::vector<Record> records;
void track_static_alloc_internal(void* addr, int size, const char* name, int kind) {
    assert(size > 0);
    records.push_back({addr, static_cast<size_t>(size), name, kind});
}
/* ORIGINAL_FUNCTION */
int main() {
    static_assert(sizeof(void*) == 8, "LP64 host required");
    TRACK_r_rendercmds();
    assert(records.size() == 5);
#define CHECK(i, var, kind_value) do { \
    assert(records[i].addr == static_cast<const void*>(&(var))); \
    assert(records[i].size == sizeof(var)); \
    assert(records[i].kind == kind_value); \
    assert(std::strcmp(records[i].name, #var) == 0); \
} while (0)
    CHECK(0, s_backEndData, 18);
    CHECK(1, g_viewInfo, 18);
    CHECK(2, g_frontEndCmds, 18);
    CHECK(3, s_debugFrameGlob, 0);
    CHECK(4, g_debugFrontEndCmds, 0);
    std::puts("IW3_ORIGINAL_RENDER_COMMAND_GLOBALS_LP64_PASS");
}
"""
        with tempfile.TemporaryDirectory() as temp:
            cpp = Path(temp) / "original_rendercmds_tracking.cpp"
            exe = Path(temp) / "original_rendercmds_tracking"
            cpp.write_text(
                fixture.replace("/* ORIGINAL_FUNCTION */", original),
                encoding="utf-8",
            )
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run(
                [str(exe)], capture_output=True, text=True,
                timeout=30, env=env,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_RENDER_COMMAND_GLOBALS_LP64_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
