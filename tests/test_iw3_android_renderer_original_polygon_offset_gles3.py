"""Original KisakCOD IW3 polygon depth offset: host GLES mocks + ASan/UBSan, NOT GAME."""
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
using GLenum=unsigned int; using GLint=int; using GLfloat=float;
using GLboolean=unsigned char;
#define GL_NO_ERROR 0
#define GL_FALSE 0
#define GL_TRUE 1
#define GL_DEPTH_TEST 0x0B71
#define GL_DEPTH_WRITEMASK 0x0B72
#define GL_DEPTH_FUNC 0x0B74
#define GL_DEPTH_BITS 0x0D56
#define GL_POLYGON_OFFSET_FACTOR 0x8038
#define GL_POLYGON_OFFSET_UNITS 0x2A00
#define GL_POLYGON_OFFSET_FILL 0x8037
#define GL_ALWAYS 0x0207
#define GL_LESS 0x0201
#define GL_EQUAL 0x0202
#define GL_LEQUAL 0x0203
GLenum glGetError(); GLboolean glIsEnabled(GLenum);
void glGetIntegerv(GLenum,GLint*); void glGetFloatv(GLenum,GLfloat*);
void glGetBooleanv(GLenum,GLboolean*);
void glDepthMask(GLboolean); void glDepthFunc(GLenum);
void glEnable(GLenum); void glDisable(GLenum);
void glPolygonOffset(GLfloat,GLfloat);
"""
HARNESS = r"""
#include <cassert>
#include <cmath>
#include <cstdio>
#include <limits>
#include "r_android_depth_state.cpp"
static bool context=true, failQuery=false, failPolygon=false, failEnable=false;
static GLenum error=GL_NO_ERROR;
static GLint depthBits=24, depthFunc=GL_LESS;
static GLfloat factor=0.25f, units=3.0f;
static GLboolean depthWrite=GL_TRUE;
static bool enabled=false, depthEnabled=false;
static int mutations=0;
EGLDisplay eglGetCurrentDisplay(){return context?(void*)1:EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return context?(void*)2:EGL_NO_CONTEXT;}
GLenum glGetError(){auto e=error;error=GL_NO_ERROR;return e;}
GLboolean glIsEnabled(GLenum e){
    if(failQuery){error=0x502;return GL_FALSE;}
    if(e==GL_POLYGON_OFFSET_FILL)return enabled;
    assert(e==GL_DEPTH_TEST);return depthEnabled;
}
void glGetIntegerv(GLenum e,GLint* p){
    if(failQuery){error=0x502;return;}
    if(e==GL_DEPTH_BITS)*p=depthBits;
    else {assert(e==GL_DEPTH_FUNC);*p=depthFunc;}
}
void glGetFloatv(GLenum e,GLfloat* p){
    if(failQuery){error=0x502;return;}
    assert(e==GL_POLYGON_OFFSET_FACTOR || e==GL_POLYGON_OFFSET_UNITS);
    *p=(e==GL_POLYGON_OFFSET_FACTOR)?factor:units;
}
void glGetBooleanv(GLenum e,GLboolean* p){assert(e==GL_DEPTH_WRITEMASK);*p=depthWrite;}
void glDepthMask(GLboolean b){depthWrite=b;}
void glDepthFunc(GLenum e){depthFunc=e;}
void glEnable(GLenum e){
    ++mutations;
    if(failEnable){failEnable=false;error=0x502;return;}
    if(e==GL_POLYGON_OFFSET_FILL)enabled=true;
    else {assert(e==GL_DEPTH_TEST);depthEnabled=true;}
}
void glDisable(GLenum e){
    ++mutations;
    if(e==GL_POLYGON_OFFSET_FILL)enabled=false;
    else {assert(e==GL_DEPTH_TEST);depthEnabled=false;}
}
void glPolygonOffset(GLfloat a,GLfloat b){
    ++mutations;factor=a;units=b;
    if(failPolygon){failPolygon=false;error=0x502;}
}
int main(){
    static_assert(sizeof(void*)==8,"LP64");
    context=false;assert(!R_AndroidGlesSetPolygonOffset(1.0f,1.0f/65536.0f));
    context=true;
    const int before=mutations;
    assert(!R_AndroidGlesSetPolygonOffset(std::numeric_limits<float>::quiet_NaN(),0));
    assert(!R_AndroidGlesSetPolygonOffset(0,std::numeric_limits<float>::infinity()));
    assert(!R_AndroidGlesSetPolygonOffset(0,1.5f));
    assert(mutations==before);
    error=0x500;assert(!R_AndroidGlesSetPolygonOffset(1,0));
    depthBits=0;assert(!R_AndroidGlesSetPolygonOffset(1,0));
    depthBits=32;assert(!R_AndroidGlesSetPolygonOffset(1,0));
    depthBits=24;
    failQuery=true;assert(!R_AndroidGlesSetPolygonOffset(1,0));failQuery=false;
    assert(mutations==before);
    assert(R_AndroidGlesSetPolygonOffset(2.0f,1.0f/65536.0f));
    assert(enabled && factor==2.0f && units==256.0f);
    assert(R_AndroidGlesSetPolygonOffset(-3.0f,-1.0f/65536.0f));
    assert(enabled && factor==-3.0f && units==-256.0f);
    depthBits=16;
    assert(R_AndroidGlesSetPolygonOffset(1.0f,1.0f/65536.0f));
    assert(units==1.0f);
    assert(R_AndroidGlesSetPolygonOffset(0,0));
    assert(!enabled && factor==0 && units==0);
    factor=0.5f;units=4.0f;enabled=false;
    failPolygon=true;
    assert(!R_AndroidGlesSetPolygonOffset(1,0));
    assert(!enabled && factor==0.5f && units==4.0f);
    failEnable=true;
    assert(!R_AndroidGlesSetPolygonOffset(1,0));
    assert(!enabled && factor==0.5f && units==4.0f);
    std::puts("IW3_ORIGINAL_POLYGON_OFFSET_GLES3_ASAN_UBSAN_PASS_NOT_FRAME");
}
"""

class OriginalPolygonOffsetGles3(unittest.TestCase):
    def test_authentic_callsite_and_guarded_gles3_provider(self):
        original = (GFX / "r_state.cpp").read_text()
        start = original.index("void __cdecl R_HW_SetPolygonOffset(")
        end = original.index("void __cdecl R_SetMeshStream(", start)
        body = original[start:end]
        self.assertIn("R_AndroidGlesSetPolygonOffset(scale, bias)", body)
        self.assertIn("D3DRS_SLOPESCALEDEPTHBIAS", body)
        self.assertIn("D3DRS_DEPTHBIAS", body)
        self.assertIn("#else", body)
        self.assertIn("++g_disableRendering", body)
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
                "IW3_ORIGINAL_POLYGON_OFFSET_GLES3_ASAN_UBSAN_PASS_NOT_FRAME",
                run.stdout)

if __name__ == "__main__":
    unittest.main()
