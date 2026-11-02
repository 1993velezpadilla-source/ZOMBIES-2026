"""Authentic IW3 blend state -> GLES3: mocked host ASan/UBSan, NOT GAME."""
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
#define GL_BLEND 0x0BE2
#define GL_BLEND_EQUATION_RGB 0x8009
#define GL_BLEND_EQUATION_ALPHA 0x883D
#define GL_BLEND_SRC_RGB 0x80C9
#define GL_BLEND_DST_RGB 0x80C8
#define GL_BLEND_SRC_ALPHA 0x80CB
#define GL_BLEND_DST_ALPHA 0x80CA
#define GL_ZERO 0
#define GL_ONE 1
#define GL_SRC_COLOR 0x0300
#define GL_ONE_MINUS_SRC_COLOR 0x0301
#define GL_SRC_ALPHA 0x0302
#define GL_ONE_MINUS_SRC_ALPHA 0x0303
#define GL_DST_ALPHA 0x0304
#define GL_ONE_MINUS_DST_ALPHA 0x0305
#define GL_DST_COLOR 0x0306
#define GL_ONE_MINUS_DST_COLOR 0x0307
#define GL_FUNC_ADD 0x8006
#define GL_FUNC_SUBTRACT 0x800A
#define GL_FUNC_REVERSE_SUBTRACT 0x800B
#define GL_MIN 0x8007
#define GL_MAX 0x8008
GLenum glGetError(); GLboolean glIsEnabled(GLenum); void glGetIntegerv(GLenum,GLint*);
void glBlendEquationSeparate(GLenum,GLenum);void glBlendFuncSeparate(GLenum,GLenum,GLenum,GLenum);
void glEnable(GLenum);void glDisable(GLenum);
"""
HARNESS = r"""
#include <cassert>
#include <cstdio>
#include "r_android_blend.cpp"
static bool context=true, failQuery=false, failMutation=false;
static GLenum err=0;
static bool enabled=false;
static GLint eqrgb=GL_FUNC_ADD, eqalpha=GL_FUNC_ADD;
static GLint sr=GL_ONE,dr=GL_ZERO,sa=GL_ONE,da=GL_ZERO;
static int writes=0;
EGLDisplay eglGetCurrentDisplay(){return context?(void*)1:EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return context?(void*)2:EGL_NO_CONTEXT;}
GLenum glGetError(){auto e=err;err=0;return e;}
GLboolean glIsEnabled(GLenum e){assert(e==GL_BLEND);return enabled;}
void glGetIntegerv(GLenum e,GLint* v){if(failQuery){err=0x502;return;} switch(e){
case GL_BLEND_EQUATION_RGB:*v=eqrgb;break;case GL_BLEND_EQUATION_ALPHA:*v=eqalpha;break;
case GL_BLEND_SRC_RGB:*v=sr;break;case GL_BLEND_DST_RGB:*v=dr;break;
case GL_BLEND_SRC_ALPHA:*v=sa;break;case GL_BLEND_DST_ALPHA:*v=da;break;
default: assert(false);}}
bool fail(){++writes;if(failMutation){failMutation=false;err=0x502;return true;}return false;}
void glBlendEquationSeparate(GLenum a,GLenum b){if(!fail()){eqrgb=a;eqalpha=b;}}
void glBlendFuncSeparate(GLenum a,GLenum b,GLenum c,GLenum d){if(!fail()){sr=a;dr=b;sa=c;da=d;}}
void glEnable(GLenum e){assert(e==GL_BLEND);if(!fail())enabled=true;}
void glDisable(GLenum e){assert(e==GL_BLEND);if(!fail())enabled=false;}
int main(){
static_assert(sizeof(void*)==8,"LP64");
const unsigned alphaBlend=(1u<<8)|(5u)|(6u<<4)|(1u<<24)|(2u<<16)|(1u<<20);
context=false;assert(!R_AndroidGlesSetBlend(alphaBlend));assert(!R_AndroidGlesDisableBlend());
context=true;assert(!R_AndroidGlesSetBlend(0));
assert(!R_AndroidGlesSetBlend((6u<<8)|1u|2u<<4|1u<<24|2u<<16|1u<<20));
assert(!R_AndroidGlesSetBlend((1u<<8)|11u|2u<<4|1u<<24|2u<<16|1u<<20));
err=0x502;assert(!R_AndroidGlesSetBlend(alphaBlend));
failQuery=true;assert(!R_AndroidGlesSetBlend(alphaBlend));failQuery=false;
assert(R_AndroidGlesSetBlend(alphaBlend));
assert(enabled && eqrgb==GL_FUNC_ADD && eqalpha==GL_FUNC_ADD);
assert(sr==GL_SRC_ALPHA && dr==GL_ONE_MINUS_SRC_ALPHA && sa==GL_ONE && da==GL_ZERO);
const unsigned sub=(2u<<8)|3u|(9u<<4)|(3u<<24)|(7u<<16)|(8u<<20);
assert(R_AndroidGlesSetBlend(sub));
assert(eqrgb==GL_FUNC_SUBTRACT && eqalpha==GL_FUNC_REVERSE_SUBTRACT);
assert(sr==GL_SRC_COLOR && dr==GL_DST_COLOR && sa==GL_DST_ALPHA && da==GL_ONE_MINUS_DST_ALPHA);
const unsigned minmax=(4u<<8)|1u|(2u<<4)|(5u<<24)|(1u<<16)|(2u<<20);
assert(R_AndroidGlesSetBlend(minmax));assert(eqrgb==GL_MIN && eqalpha==GL_MAX);
GLint saved[6]={eqrgb,eqalpha,sr,dr,sa,da};
failMutation=true;assert(!R_AndroidGlesSetBlend(alphaBlend));
assert(enabled && eqrgb==saved[0] && eqalpha==saved[1] && sr==saved[2] && dr==saved[3] && sa==saved[4] && da==saved[5]);
assert(R_AndroidGlesDisableBlend());assert(!enabled);
assert(R_AndroidGlesSetBlend(alphaBlend));assert(enabled);
failMutation=true;assert(!R_AndroidGlesDisableBlend());assert(enabled);
std::puts("IW3_ORIGINAL_BLEND_GLES3_ASAN_UBSAN_PASS_NOT_FRAME");
}
"""

class OriginalBlendGles3(unittest.TestCase):
    def test_original_iw3_blend_gles3(self):
        original = (GFX / "r_state.cpp").read_text()
        self.assertIn("R_AndroidGlesDisableBlend(", original)
        self.assertIn("R_AndroidGlesSetBlend(", original)
        self.assertIn("D3DRS_ALPHABLENDENABLE", original)  # Windows D3D9 retained
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
            self.assertIn("IW3_ORIGINAL_BLEND_GLES3_ASAN_UBSAN_PASS_NOT_FRAME", run.stdout)

if __name__ == "__main__":
    unittest.main()
