"""ASan/UBSan proof for the authentic IW3 2D text command LP64 allocation.

Compiles the original GfxCmdDrawText2D declaration and original byte-count
helper, extracted verbatim. This is NOT an Android frame or playable APK.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_rendercmds.cpp"
HDR = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_rendercmds.h"


class OriginalRendererTextLP64Tests(unittest.TestCase):
    def test_both_original_text_producers_use_native_payload_offset(self):
        src = SRC.read_text(encoding="utf-8")
        self.assertIn("R_DrawText2DCommandBytes(v13)", src)
        self.assertIn("R_DrawText2DCommandBytes(static_cast<size_t>(charCount))", src)
        self.assertNotIn("(v13 + 84) & 0xFFFFFFFC", src)
        self.assertNotIn("(charCount + 84) & 0xFFFFFFFC", src)
        self.assertIn("offsetof(GfxCmdDrawText2D, text)", src)

    def test_original_text_command_payload_fits_asan_ubsan(self):
        src = SRC.read_text(encoding="utf-8")
        hdr = HDR.read_text(encoding="utf-8")
        helper = function_source(src, "static int R_DrawText2DCommandBytes(size_t textLength)")
        declaration = re.search(r"struct GfxCmdDrawText2D\b[\s\S]*?\n};", hdr)
        self.assertIsNotNone(declaration)
        fixture = r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
struct GfxCmdHeader { uint16_t id; uint16_t byteCount; };
struct GfxColor { uint8_t array[4]; };
struct Font_s;
struct Material;
/* ORIGINAL_DECLARATION */
/* ORIGINAL_HELPER */
int main() {
    static_assert(sizeof(void*) == 8, "LP64 sanitizer host required");
    static_assert(offsetof(GfxCmdDrawText2D, text) > 80,
                  "Text payload must move on LP64");
    for (size_t length : {size_t(0), size_t(1), size_t(2), size_t(3),
                          size_t(4), size_t(255), size_t(4096), size_t(65535)}) {
        const int bytes = R_DrawText2DCommandBytes(length);
        if (length == 65535) { assert(bytes == 0); continue; }
        assert(bytes > 0 && bytes <= 65535 && (bytes & 3) == 0);
        const size_t offset = offsetof(GfxCmdDrawText2D, text);
        assert(static_cast<size_t>(bytes) >= offset + length + 1);
        std::vector<uint8_t> storage(static_cast<size_t>(bytes) + 16, 0xA5);
        char* text = reinterpret_cast<char*>(storage.data() + offset);
        std::memset(text, 'x', length);
        text[length] = 0;
        for (size_t i = bytes; i < storage.size(); ++i)
            assert(storage[i] == 0xA5);
    }
    for (size_t length = 65400; length <= 65535; ++length) {
        const int bytes = R_DrawText2DCommandBytes(length);
        if (bytes)
            assert(static_cast<size_t>(bytes) >=
                   offsetof(GfxCmdDrawText2D, text) + length + 1);
    }
    std::puts("IW3_ORIGINAL_RENDERER_TEXT_COMMAND_LP64_PASS");
}
"""
        fixture = fixture.replace("/* ORIGINAL_DECLARATION */", declaration.group(0))
        fixture = fixture.replace("/* ORIGINAL_HELPER */", helper)
        with tempfile.TemporaryDirectory() as temp:
            cpp = Path(temp) / "iw3_original_text_cmd.cpp"
            exe = Path(temp) / "iw3_original_text_cmd"
            cpp.write_text(fixture, encoding="utf-8")
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++20", "-O1", "-g",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(exe)], capture_output=True, text=True,
                                 timeout=30, env=env)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_RENDERER_TEXT_COMMAND_LP64_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
