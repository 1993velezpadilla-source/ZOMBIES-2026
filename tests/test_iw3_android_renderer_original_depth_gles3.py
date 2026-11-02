"""Authentic IW3 depth state GLES3 regression: mocked host ASan/UBSan, NOT GAME."""
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
EGLDisplay eglGetCurrentDisplay(); EGLContext eglGetCurrentContext();
"""
GLES = """#pragma once
using GLenum=unsigned int;using GLint=int;using GLboolean=unsigned char;
#define GL_NO_ERROR 0
#define GL_FALSE 0
#define GL_TRUE 1
#define GL_DEPTH_TEST 0x0B71
#define GL_DEPTH_WRITEMASK 0x0B72
#define GL_DEPTH_FUNC 0x0B74
#define GL_ALWAYS 0x0207
#define GL_LESS 0x0201
#define GL_EQUAL 0x0202
#define GL_LEQUAL 0x0203
GLenum glGetError();GLboolean glIsEnabled(GLenum);void glGetIntegerv(GLenum,GLint*);
void glGetBooleanv(GLenum,GLboolean*);void glDepthMask(GLboolean);void glDepthFunc(GLenum);
void glEnable(GLenum);void glDisable(GLenum);
"""
HARNESS = r"""
#include <cassert>
#include <cstdio>
#include "r_android_depth_state.cpp"
static bool context=true, failQuery=false, failMutation=false;
static GLenum err=GL_NO_ERROR;
static bool enabled=false;
static GLboolean write=GL_TRUE;
static GLint function=GL_LESS;
static int writes=0;
EGLDisplay eglGetCurrentDisplay(){return context?(void*)1:EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return context?(void*)2:EGL_NO_CONTEXT;}
GLenum glGetError(){auto e=err;err=GL_NO_ERROR;return e;}
void glGetBooleanv(GLenum e,GLboolean* p){assert(e==GL_DEPTH_WRITEMASK);if(failQuery){err=0x502;return;}*p=write;}
GLboolean glIsEnabled(GLenum e){assert(e==GL_DEPTH_TEST);if(failQuery){err=0x502;return 0;}return enabled;}
void glGetIntegerv(GLenum e,GLint* p){assert(e==GL_DEPTH_FUNC);if(failQuery){err=0x502;return;}*p=function;}
bool fail(){++writes;if(failMutation){failMutation=false;err=0x502;return true;}return false;}
void glDepthMask(GLboolean b){if(!fail())write=b;}
void glEnable(GLenum e){assert(e==GL_DEPTH_TEST);if(!fail())enabled=true;}
void glDisable(GLenum e){assert(e==GL_DEPTH_TEST);if(!fail())enabled=false;}
void glDepthFunc(GLenum e){if(!fail())function=e;}
int main(){
static_assert(sizeof(void*)==8,"LP64");
context=false;assert(!R_AndroidGlesSetDepthWrite(0));assert(!R_AndroidGlesSetDepthTest(0));assert(!R_AndroidGlesSetDepthFunc(0));
context=true;err=0x500;assert(!R_AndroidGlesSetDepthWrite(0));
failQuery=true;assert(!R_AndroidGlesSetDepthWrite(0));assert(!R_AndroidGlesSetDepthTest(0));assert(!R_AndroidGlesSetDepthFunc(0));failQuery=false;
assert(R_AndroidGlesSetDepthWrite(0));assert(write==GL_FALSE);
assert(R_AndroidGlesSetDepthWrite(1));assert(write==GL_TRUE);
assert(R_AndroidGlesSetDepthTest(0));assert(enabled);
assert(R_AndroidGlesSetDepthTest(2));assert(!enabled);
const GLenum expected[4]={GL_ALWAYS,GL_LESS,GL_EQUAL,GL_LEQUAL};
for(int i=0;i<4;++i){assert(R_AndroidGlesSetDepthFunc(i<<2));assert(function==expected[i]);}
failMutation=true;assert(!R_AndroidGlesSetDepthWrite(0));assert(write==GL_TRUE);
failMutation=true;assert(!R_AndroidGlesSetDepthTest(0));assert(!enabled);
failMutation=true;assert(!R_AndroidGlesSetDepthFunc(0));assert(function==GL_LEQUAL);
std::puts("IW3_ORIGINAL_DEPTH_GLES3_ASAN_UBSAN_PASS_NOT_FRAME");
}
"""

class OriginalDepthGles3(unittest.TestCase):
    def test_original_iw3_depth_gles3(self):
        original = (GFX / "r_state.cpp").read_text()
        for name in ("R_AndroidGlesSetDepthWrite", "R_AndroidGlesSetDepthTest",
                     "R_AndroidGlesSetDepthFunc"):
            self.assertIn(name + "(", original)
        for d3d in ("D3DRS_ZWRITEENABLE", "D3DRS_ZENABLE", "D3DRS_ZFUNC"):
            self.assertIn(d3d, original)  # Windows code preserved
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
            self.assertIn("IW3_ORIGINAL_DEPTH_GLES3_ASAN_UBSAN_PASS_NOT_FRAME", run.stdout)

if __name__ == "__main__":
    unittest.main()
