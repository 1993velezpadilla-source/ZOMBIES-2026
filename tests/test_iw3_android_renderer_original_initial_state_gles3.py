"""Host sanitizer regression of original IW3 initial render-state GLES3 seam.

Mocked EGL/GLES only: no real context, map, frame, or playable APK.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "third_party/KisakCOD/src/gfx_d3d"
EGL = """#pragma once
using EGLDisplay=void*; using EGLContext=void*;
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_NO_CONTEXT ((EGLContext)0)
EGLDisplay eglGetCurrentDisplay();
EGLContext eglGetCurrentContext();
"""
GLES = """#pragma once
using GLenum=unsigned int;
#define GL_NO_ERROR 0
#define GL_DEPTH_TEST 0x0B71
GLenum glGetError();
void glDisable(GLenum);
"""
HARNESS = r"""
#include <cassert>
#include <cstdio>
#include "r_android_initial_state.cpp"
static bool context=true, failDisable=false;
static GLenum error=GL_NO_ERROR;
static int disableCalls=0;
EGLDisplay eglGetCurrentDisplay(){return context?(void*)1:EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return context?(void*)2:EGL_NO_CONTEXT;}
GLenum glGetError(){GLenum e=error;error=GL_NO_ERROR;return e;}
void glDisable(GLenum cap){
    assert(cap==GL_DEPTH_TEST);
    ++disableCalls;
    if(failDisable) error=0x502;
}
int main(){
    static_assert(sizeof(void*)==8,"LP64 test");
    context=false;
    assert(!R_AndroidGlesSetInitialContextState());
    assert(disableCalls==0);
    context=true;
    error=0x500;
    assert(!R_AndroidGlesSetInitialContextState());
    assert(disableCalls==0);
    failDisable=true;
    assert(!R_AndroidGlesSetInitialContextState());
    assert(disableCalls==1);
    failDisable=false;
    assert(R_AndroidGlesSetInitialContextState());
    assert(disableCalls==2);
    std::puts("IW3_ORIGINAL_INITIAL_RENDER_STATE_GLES3_HOST_SANITIZER_PASS_NOT_FRAME");
}
"""

class OriginalInitialStateGles3(unittest.TestCase):
    def test_original_initial_state_uses_gles3_not_d3d9(self):
        original = (GFX / "r_state.cpp").read_text()
        self.assertIn('#include "r_android_initial_state.h"', original)
        self.assertIn("R_AndroidGlesSetInitialContextState()", original)
        self.assertIn("device->SetRenderState(D3DRS_SEPARATEALPHABLENDENABLE, 1)", original)
        self.assertIn("device->SetRenderState(D3DRS_ZENABLE, 0)", original)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "EGL").mkdir()
            (root / "GLES3").mkdir()
            (root / "EGL/egl.h").write_text(EGL)
            (root / "GLES3/gl3.h").write_text(GLES)
            (root / "test.cpp").write_text(HARNESS)
            binary = root / "test"
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-D__ANDROID__",
                 "-O1", "-g", "-UNDEBUG", "-fsanitize=address,undefined",
                 "-fno-omit-frame-pointer", "-I", str(root), "-I", str(GFX),
                 str(root / "test.cpp"), "-o", str(binary)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(binary)], capture_output=True, text=True,
                                 env=env, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_INITIAL_RENDER_STATE_GLES3_HOST_SANITIZER_PASS_NOT_FRAME", run.stdout)

if __name__ == "__main__":
    unittest.main()
