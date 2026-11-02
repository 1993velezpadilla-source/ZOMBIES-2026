"""Original IW3 alpha-test/color-mask GLES3 seam regression (NOT GAME).

Host EGL/GLES mocks with ASan/UBSan. No real device/frame/map/gameplay.
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
using GLenum=unsigned int; using GLboolean=unsigned char; using GLint=int;
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
void glGetBooleanv(GLenum, GLboolean*);
void glColorMask(GLboolean, GLboolean, GLboolean, GLboolean);
GLboolean glIsEnabled(GLenum);
void glGetIntegerv(GLenum, GLint*);
void glFrontFace(GLenum);
void glCullFace(GLenum);
void glEnable(GLenum);
void glDisable(GLenum);
"""
HARNESS = r"""
#include <cassert>
#include <cstdio>
#include "r_android_render_state.cpp"
static bool context=true, failQuery=false, failMask=false;
static GLenum error=GL_NO_ERROR;
static GLboolean mask[4]={GL_TRUE,GL_FALSE,GL_TRUE,GL_FALSE};
static int queries=0, writes=0;
EGLDisplay eglGetCurrentDisplay(){return context?(void*)1:EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return context?(void*)2:EGL_NO_CONTEXT;}
GLenum glGetError(){GLenum e=error;error=GL_NO_ERROR;return e;}
void glGetBooleanv(GLenum pname,GLboolean *v){
    assert(pname==GL_COLOR_WRITEMASK); ++queries;
    if(failQuery){error=0x502;return;}
    for(int i=0;i<4;++i)v[i]=mask[i];
}
void glColorMask(GLboolean r,GLboolean g,GLboolean b,GLboolean a){
    ++writes;
    if(failMask){failMask=false;error=0x502;return;}
    mask[0]=r;mask[1]=g;mask[2]=b;mask[3]=a;
}
// Existing alpha/color regression also links the expanded cull/polygon
// provider. Stub the new GL entry points without exercising them here.
GLboolean glIsEnabled(GLenum){return GL_FALSE;}
void glGetIntegerv(GLenum,GLint *v){*v=GL_BACK;}
void glFrontFace(GLenum){}
void glCullFace(GLenum){}
void glEnable(GLenum){}
void glDisable(GLenum){}
void expect(GLboolean r,GLboolean g,GLboolean b,GLboolean a){
    assert(mask[0]==r&&mask[1]==g&&mask[2]==b&&mask[3]==a);
}
int main(){
    static_assert(sizeof(void*)==8,"LP64");
    context=false;
    assert(!R_AndroidGlesSetAlphaTestEnable(0x800));
    assert(!R_AndroidGlesSetColorMask(0x18000000));
    assert(writes==0 && queries==0);
    context=true;
    error=0x500;
    assert(!R_AndroidGlesSetAlphaTestEnable(0x800));
    assert(!R_AndroidGlesSetAlphaTestEnable(0)); // no shader discard yet
    assert(!R_AndroidGlesSetAlphaTestEnable(0x1000));
    assert(R_AndroidGlesSetAlphaTestEnable(0x800));
    error=0x501;
    assert(!R_AndroidGlesSetColorMask(0x18000000));
    assert(queries==0);
    failQuery=true;
    assert(!R_AndroidGlesSetColorMask(0x18000000));
    failQuery=false;
    expect(1,0,1,0);
    assert(R_AndroidGlesSetColorMask(0x00000000));expect(0,0,0,0);
    assert(R_AndroidGlesSetColorMask(0x08000000));expect(1,1,1,0);
    assert(R_AndroidGlesSetColorMask(0x10000000));expect(0,0,0,1);
    assert(R_AndroidGlesSetColorMask(0x18000000));expect(1,1,1,1);
    failMask=true;
    assert(!R_AndroidGlesSetColorMask(0));
    expect(1,1,1,1);
    assert(writes==6); // four successful masks, failed mutation, rollback
    std::puts("IW3_ORIGINAL_ALPHA_FAIL_CLOSED_COLOR_MASK_GLES3_SANITIZER_PASS_NOT_FRAME");
}
"""

class OriginalRenderStateGles3(unittest.TestCase):
    def test_original_alpha_test_fail_closed_and_color_mask(self):
        original = (GFX / "r_state.cpp").read_text()
        self.assertIn('#include "r_android_render_state.h"', original)
        self.assertIn("R_AndroidGlesSetAlphaTestEnable(", original)
        self.assertIn("R_AndroidGlesSetColorMask(", original)
        self.assertIn("D3DRS_ALPHATESTENABLE", original)  # Windows path retained
        self.assertIn("D3DRS_COLORWRITEENABLE", original)
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
                "IW3_ORIGINAL_ALPHA_FAIL_CLOSED_COLOR_MASK_GLES3_SANITIZER_PASS_NOT_FRAME",
                run.stdout)

if __name__ == "__main__":
    unittest.main()
