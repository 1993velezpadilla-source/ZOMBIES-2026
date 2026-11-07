"""Host ASan/UBSan regression for original IW3 RC_SET_VIEWPORT -> GLES3.
Mocked EGL/GLES calls do NOT prove device rendering or a playable APK.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_android_viewport.cpp"
BACKEND = ROOT / "third_party/KisakCOD/src/gfx_d3d/rb_backend.cpp"

EGL_HEADER = """
#pragma once
using EGLDisplay = void *;
using EGLContext = void *;
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_NO_CONTEXT ((EGLContext)0)
EGLDisplay eglGetCurrentDisplay();
EGLContext eglGetCurrentContext();
"""

GLES_HEADER = """
#pragma once
using GLint = int;
using GLenum = unsigned int;
#define GL_NO_ERROR 0
void glViewport(GLint, GLint, GLint, GLint);
GLenum glGetError();
"""

HARNESS = r"""
#include <cassert>
#include <cstdint>
#include <climits>
#include <cstdio>
#include "r_android_viewport.cpp"
static bool context = true;
static int calls = 0, px = -1, py = -1, pw = -1, ph = -1;
static GLenum error = GL_NO_ERROR;
static bool failViewport = false;
EGLDisplay eglGetCurrentDisplay() { return context ? (void*)0x1 : EGL_NO_DISPLAY; }
EGLContext eglGetCurrentContext() { return context ? (void*)0x2 : EGL_NO_CONTEXT; }
void glViewport(GLint x, GLint y, GLint w, GLint h) {
    ++calls; px=x; py=y; pw=w; ph=h;
    if (failViewport) error=0x0501;
}
GLenum glGetError() { GLenum e=error; error=GL_NO_ERROR; return e; }
int main() {
    static_assert(sizeof(void*) == 8, "LP64 host regression required");
    assert(R_AndroidGlesSetViewport(0,0,1920,1080,1920,1080));
    assert(calls==1 && px==0 && py==0 && pw==1920 && ph==1080);
    assert(R_AndroidGlesSetViewport(100,50,300,200,1920,1080));
    assert(calls==2 && px==100 && py==830 && pw==300 && ph==200);
    // Offscreen render target: use IW3 target height, NOT EGL window height.
    assert(R_AndroidGlesSetViewport(8,16,32,64,256,256));
    assert(calls==3 && px==8 && py==176 && pw==32 && ph==64);
    assert(!R_AndroidGlesSetViewport(-1,0,1,1,256,256));
    assert(!R_AndroidGlesSetViewport(0,-1,1,1,256,256));
    assert(!R_AndroidGlesSetViewport(0,0,0,1,256,256));
    assert(!R_AndroidGlesSetViewport(0,0,1,0,256,256));
    assert(!R_AndroidGlesSetViewport(0,0,1,1,0,256));
    assert(!R_AndroidGlesSetViewport(0,0,1,1,256,0));
    assert(!R_AndroidGlesSetViewport(250,0,10,1,256,256));
    assert(!R_AndroidGlesSetViewport(0,250,1,10,256,256));
    assert(!R_AndroidGlesSetViewport(INT_MAX,0,INT_MAX,1,256,256));
    assert(!R_AndroidGlesSetViewport(0,INT_MAX,1,INT_MAX,256,256));
    assert(calls==3);
    context=false;
    assert(!R_AndroidGlesSetViewport(0,0,1,1,256,256));
    context=true;
    assert(calls==3);
    error=0x0500;
    assert(!R_AndroidGlesSetViewport(0,0,1,1,256,256));
    assert(calls==3);
    failViewport=true;
    assert(!R_AndroidGlesSetViewport(0,0,1,1,256,256));
    assert(calls==4);
    failViewport=false;
    assert(R_AndroidGlesSetViewport(0,0,1,1,256,256));
    assert(calls==5 && py==255);
    std::puts("IW3_ORIGINAL_VIEWPORT_GLES3_HOST_SANITIZER_PASS_NOT_FRAME");
}
"""

class OriginalViewportGles3(unittest.TestCase):
    def test_original_viewport_command_and_gles_mapping(self):
        backend = BACKEND.read_text()
        self.assertIn("R_SetViewportStruct(&gfxCmdBufSourceState, &cmd->viewport);", backend)
        self.assertIn("R_AndroidGlesSetViewport(cmd->viewport.x, cmd->viewport.y,", backend)
        self.assertIn("gfxCmdBufSourceState.renderTargetHeight", backend)
        self.assertIn("IW3 Android: original viewport command GLES3 failed", backend)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "EGL").mkdir()
            (base / "GLES3").mkdir()
            (base / "EGL/egl.h").write_text(EGL_HEADER)
            (base / "GLES3/gl3.h").write_text(GLES_HEADER)
            (base / "test.cpp").write_text(HARNESS)
            binary = base / "test"
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-D__ANDROID__",
                 "-O1", "-g", "-UNDEBUG", "-fsanitize=address,undefined",
                 "-fno-omit-frame-pointer", "-I", str(base),
                 "-I", str(SOURCE.parent), str(base / "test.cpp"),
                 "-o", str(binary)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(binary)], capture_output=True, text=True,
                                 env=env, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_VIEWPORT_GLES3_HOST_SANITIZER_PASS_NOT_FRAME", run.stdout)

if __name__ == "__main__":
    unittest.main()
