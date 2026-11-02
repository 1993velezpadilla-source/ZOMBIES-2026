"""Original KisakCOD IW3 cull and polygon state GLES3 regression (NOT GAME).

Host ASan/UBSan and mocked EGL/GLES; this is not an Android frame proof.
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
using GLenum=unsigned int; using GLint=int; using GLboolean=unsigned char;
#define GL_NO_ERROR 0
#define GL_FALSE 0
#define GL_TRUE 1
#define GL_COLOR_WRITEMASK 0x0C23
#define GL_SAMPLE_ALPHA_TO_COVERAGE 0x809E
#define GL_SAMPLE_BUFFERS 0x80A8
#define GL_SAMPLES 0x80A9
#define GL_CULL_FACE 0x0B44
#define GL_CULL_FACE_MODE 0x0B45
#define GL_FRONT_FACE 0x0B46
#define GL_CW 0x0900
#define GL_CCW 0x0901
#define GL_FRONT 0x0404
#define GL_BACK 0x0405
GLenum glGetError();
void glGetBooleanv(GLenum,GLboolean*);
void glColorMask(GLboolean,GLboolean,GLboolean,GLboolean);
GLboolean glIsEnabled(GLenum);
void glGetIntegerv(GLenum,GLint*);
void glFrontFace(GLenum);
void glCullFace(GLenum);
void glEnable(GLenum);
void glDisable(GLenum);
"""
HARNESS = r"""
#include <cassert>
#include <cstdio>
#include "r_android_render_state.cpp"
static bool context=true, failQuery=false, failChange=false;
static GLenum error=GL_NO_ERROR, face=GL_CCW, cull=GL_FRONT;
static bool enabled=false;
static int changes=0;
EGLDisplay eglGetCurrentDisplay(){return context?(void*)1:EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return context?(void*)2:EGL_NO_CONTEXT;}
GLenum glGetError(){GLenum e=error;error=GL_NO_ERROR;return e;}
void glGetBooleanv(GLenum,GLboolean *v){for(int i=0;i<4;++i)v[i]=GL_TRUE;}
void glColorMask(GLboolean,GLboolean,GLboolean,GLboolean){}
GLboolean glIsEnabled(GLenum e){assert(e==GL_CULL_FACE);return enabled?GL_TRUE:GL_FALSE;}
void glGetIntegerv(GLenum e,GLint *v){
    if(failQuery){error=0x502;return;}
    assert(e==GL_FRONT_FACE || e==GL_CULL_FACE_MODE);
    *v=(e==GL_FRONT_FACE)?face:cull;
}
bool failMutation(){++changes;if(failChange){failChange=false;error=0x502;return true;}return false;}
void glFrontFace(GLenum v){if(!failMutation())face=v;}
void glCullFace(GLenum v){if(!failMutation())cull=v;}
void glEnable(GLenum v){assert(v==GL_CULL_FACE);if(!failMutation())enabled=true;}
void glDisable(GLenum v){assert(v==GL_CULL_FACE);if(!failMutation())enabled=false;}
int main(){
    static_assert(sizeof(void*)==8,"LP64");
    context=false;
    assert(!R_AndroidGlesSetCullFace(0x8000));
    assert(!R_AndroidGlesSetPolygonMode(0));
    assert(changes==0);
    context=true;
    assert(!R_AndroidGlesSetCullFace(0)); // invalid original bits
    assert(changes==0);
    error=0x500;
    assert(!R_AndroidGlesSetCullFace(0x8000));
    assert(changes==0);
    failQuery=true;
    assert(!R_AndroidGlesSetCullFace(0x8000));
    failQuery=false;
    assert(changes==0);
    assert(R_AndroidGlesSetCullFace(0x8000)); // IW3 BACK / D3DCULL_CCW
    assert(enabled && face==GL_CW && cull==GL_BACK);
    assert(R_AndroidGlesSetCullFace(0xC000)); // IW3 FRONT / D3DCULL_CW
    assert(enabled && face==GL_CW && cull==GL_FRONT);
    assert(R_AndroidGlesSetCullFace(0x4000)); // IW3 NONE
    assert(!enabled);
    face=GL_CCW;cull=GL_FRONT;enabled=false;
    failChange=true;
    assert(!R_AndroidGlesSetCullFace(0x8000));
    assert(!enabled && face==GL_CCW && cull==GL_FRONT);
    assert(R_AndroidGlesSetPolygonMode(0)); // solid
    assert(!R_AndroidGlesSetPolygonMode(0x80000000u)); // wireframe fails closed
    error=0x500;
    assert(!R_AndroidGlesSetPolygonMode(0));
    std::puts("IW3_ORIGINAL_CULL_POLYGON_GLES3_SANITIZER_PASS_NOT_FRAME");
}
"""

class OriginalCullPolygonGles3(unittest.TestCase):
    def test_original_cull_and_polygon_fail_closed(self):
        original = (GFX / "r_state.cpp").read_text()
        self.assertIn("R_AndroidGlesSetCullFace(", original)
        self.assertIn("R_AndroidGlesSetPolygonMode(", original)
        self.assertIn("D3DRS_CULLMODE", original)  # Windows path retained
        self.assertIn("D3DRS_FILLMODE", original)
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
            self.assertIn(
                "IW3_ORIGINAL_CULL_POLYGON_GLES3_SANITIZER_PASS_NOT_FRAME",
                run.stdout)

if __name__ == "__main__":
    unittest.main()
