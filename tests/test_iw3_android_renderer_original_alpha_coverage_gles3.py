"""Authentic IW3 D3D9 ATOC/SSAA -> GLES3 coverage regression, NOT GAME."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "third_party/KisakCOD/src/gfx_d3d"
EGL = """#pragma once
using EGLDisplay=void*;using EGLContext=void*;
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_NO_CONTEXT ((EGLContext)0)
EGLDisplay eglGetCurrentDisplay();EGLContext eglGetCurrentContext();
"""
GLES = """#pragma once
using GLenum=unsigned int;using GLint=int;using GLboolean=unsigned char;
#define GL_NO_ERROR 0
#define GL_FALSE 0
#define GL_TRUE 1
#define GL_COLOR_WRITEMASK 0x0C23
#define GL_CULL_FACE 0x0B44
#define GL_CULL_FACE_MODE 0x0B45
#define GL_FRONT_FACE 0x0B46
#define GL_CW 0x0900
#define GL_CCW 0x0901
#define GL_FRONT 0x0404
#define GL_BACK 0x0405
#define GL_SAMPLE_ALPHA_TO_COVERAGE 0x809E
#define GL_SAMPLE_BUFFERS 0x80A8
#define GL_SAMPLES 0x80A9
GLenum glGetError();GLboolean glIsEnabled(GLenum);
void glGetIntegerv(GLenum,GLint*);
void glGetBooleanv(GLenum,GLboolean*);
void glColorMask(GLboolean,GLboolean,GLboolean,GLboolean);
void glFrontFace(GLenum);void glCullFace(GLenum);
void glEnable(GLenum);void glDisable(GLenum);
"""
HARNESS = r"""
#include <cassert>
#include <cstdio>
#include "r_android_render_state.cpp"
static bool context=true, enabled=false, failQuery=false, failMutation=false;
static GLenum error=GL_NO_ERROR;
static int sampleBuffers=1, samples=4, writes=0;
EGLDisplay eglGetCurrentDisplay(){return context?(void*)1:EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return context?(void*)2:EGL_NO_CONTEXT;}
GLenum glGetError(){auto e=error;error=GL_NO_ERROR;return e;}
GLboolean glIsEnabled(GLenum e){
    assert(e==GL_SAMPLE_ALPHA_TO_COVERAGE);
    if(failQuery){error=0x502;return GL_FALSE;}
    return enabled?GL_TRUE:GL_FALSE;
}
void glGetIntegerv(GLenum e,GLint* v){
    if(failQuery){error=0x502;return;}
    if(e==GL_SAMPLE_BUFFERS)*v=sampleBuffers;
    else {assert(e==GL_SAMPLES);*v=samples;}
}
void glGetBooleanv(GLenum,GLboolean*){}
void glColorMask(GLboolean,GLboolean,GLboolean,GLboolean){}
void glFrontFace(GLenum){}
void glCullFace(GLenum){}
void glEnable(GLenum e){
    assert(e==GL_SAMPLE_ALPHA_TO_COVERAGE);++writes;
    if(failMutation){failMutation=false;error=0x502;return;}
    enabled=true;
}
void glDisable(GLenum e){
    assert(e==GL_SAMPLE_ALPHA_TO_COVERAGE);++writes;enabled=false;
}
int main(){
    static_assert(sizeof(void*)==8,"LP64");
    context=false;assert(!R_AndroidGlesSetAlphaCoverage(0,1));assert(writes==0);
    context=true;
    error=0x500;assert(!R_AndroidGlesSetAlphaCoverage(0,1));
    assert(!R_AndroidGlesSetAlphaCoverage(0,2)); // SSAA unsupported
    assert(writes==0);
    sampleBuffers=0;assert(!R_AndroidGlesSetAlphaCoverage(0,1));
    sampleBuffers=1;samples=1;assert(!R_AndroidGlesSetAlphaCoverage(0,1));
    samples=4;failQuery=true;assert(!R_AndroidGlesSetAlphaCoverage(0,1));
    failQuery=false;assert(writes==0);
    assert(R_AndroidGlesSetAlphaCoverage(0,1));assert(enabled);
    assert(R_AndroidGlesSetAlphaCoverage(0x800,2));assert(!enabled);
    failMutation=true;
    assert(!R_AndroidGlesSetAlphaCoverage(0,1));
    assert(!enabled); // failed enable and restored previous state
    assert(R_AndroidGlesSetAlphaCoverage(0,1));assert(enabled);
    std::puts("IW3_ORIGINAL_ATOC_GLES3_ASAN_UBSAN_PASS_NOT_FRAME");
}
"""

class OriginalAlphaCoverageGles3(unittest.TestCase):
    def test_original_alpha_coverage_gl_and_ssaa_rejection(self):
        original = (GFX / "r_state.cpp").read_text()
        start = original.index("void __cdecl R_SetAlphaAntiAliasingState(")
        body = original[start:]
        self.assertIn("R_AndroidGlesSetAlphaCoverage(", body)
        self.assertIn("D3DRS_ADAPTIVETESS_Y", body)
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
            self.assertIn("IW3_ORIGINAL_ATOC_GLES3_ASAN_UBSAN_PASS_NOT_FRAME",
                          run.stdout)

if __name__ == "__main__":
    unittest.main()
