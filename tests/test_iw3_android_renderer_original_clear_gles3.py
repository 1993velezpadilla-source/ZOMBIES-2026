"""Host sanitizer regression for authentic IW3 RC_CLEAR_SCREEN -> GLES3 translation.
GL/EGL calls are mocked. This does NOT prove a rendered frame or playable APK.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_android_clear.cpp"
BACKEND = ROOT / "third_party/KisakCOD/src/gfx_d3d/rb_backend.cpp"

EGL_HEADER = r"""
#pragma once
using EGLDisplay = void *;
using EGLContext = void *;
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_NO_CONTEXT ((EGLContext)0)
EGLDisplay eglGetCurrentDisplay();
EGLContext eglGetCurrentContext();
"""

GLES_HEADER = r"""
#pragma once
using GLboolean = unsigned char;
using GLint = int;
using GLuint = unsigned int;
using GLfloat = float;
using GLenum = unsigned int;
using GLbitfield = unsigned int;
#define GL_TRUE 1
#define GL_FALSE 0
#define GL_NO_ERROR 0
#define GL_SCISSOR_TEST 1
#define GL_COLOR_WRITEMASK 2
#define GL_DEPTH_WRITEMASK 3
#define GL_STENCIL_WRITEMASK 4
#define GL_STENCIL_BACK_WRITEMASK 5
#define GL_COLOR_CLEAR_VALUE 6
#define GL_DEPTH_CLEAR_VALUE 7
#define GL_STENCIL_CLEAR_VALUE 8
#define GL_FRONT 9
#define GL_BACK 10
#define GL_COLOR_BUFFER_BIT 0x4000
#define GL_DEPTH_BUFFER_BIT 0x100
#define GL_STENCIL_BUFFER_BIT 0x400
GLboolean glIsEnabled(GLenum);
void glGetBooleanv(GLenum, GLboolean *);
void glGetFloatv(GLenum, GLfloat *);
void glGetIntegerv(GLenum, GLint *);
void glColorMask(GLboolean, GLboolean, GLboolean, GLboolean);
void glDepthMask(GLboolean);
void glStencilMaskSeparate(GLenum, GLuint);
void glClearColor(GLfloat, GLfloat, GLfloat, GLfloat);
void glClearDepthf(GLfloat);
void glClearStencil(GLint);
void glDisable(GLenum);
void glEnable(GLenum);
void glClear(GLbitfield);
GLenum glGetError();
"""

HARNESS = r"""
#include <cassert>
#include <cmath>
#include <cstdio>
#include <limits>
#include "r_android_clear.cpp"
static bool hasContext=true, scissor=true;
static GLboolean colorMask[4]={1,0,1,0}, depthMask=0;
static GLint frontMask=0x1, backMask=0x2, clearStencil=9;
static GLfloat clearColor[4]={0.2f,0.3f,0.4f,0.5f}, clearDepth=0.25f;
static GLbitfield lastBits=0;
static int clearCalls=0;
static GLenum glError=GL_NO_ERROR;
EGLDisplay eglGetCurrentDisplay() { return hasContext ? (void*)0x11 : EGL_NO_DISPLAY; }
EGLContext eglGetCurrentContext() { return hasContext ? (void*)0x12 : EGL_NO_CONTEXT; }
GLboolean glIsEnabled(GLenum x) { assert(x==GL_SCISSOR_TEST); return scissor; }
void glGetBooleanv(GLenum x, GLboolean *out) {
    if (x==GL_COLOR_WRITEMASK) for(int i=0;i<4;++i) out[i]=colorMask[i];
    else { assert(x==GL_DEPTH_WRITEMASK); *out=depthMask; }
}
void glGetFloatv(GLenum x, GLfloat *out) {
    if (x==GL_COLOR_CLEAR_VALUE) for(int i=0;i<4;++i) out[i]=clearColor[i];
    else { assert(x==GL_DEPTH_CLEAR_VALUE); *out=clearDepth; }
}
void glGetIntegerv(GLenum x, GLint *out) {
    if(x==GL_STENCIL_WRITEMASK) *out=frontMask;
    else if(x==GL_STENCIL_BACK_WRITEMASK) *out=backMask;
    else { assert(x==GL_STENCIL_CLEAR_VALUE); *out=clearStencil; }
}
void glColorMask(GLboolean a,GLboolean b,GLboolean c,GLboolean d) {
    colorMask[0]=a; colorMask[1]=b; colorMask[2]=c; colorMask[3]=d;
}
void glDepthMask(GLboolean a) { depthMask=a; }
void glStencilMaskSeparate(GLenum face, GLuint a) {
    if(face==GL_FRONT) frontMask=static_cast<GLint>(a);
    else { assert(face==GL_BACK); backMask=static_cast<GLint>(a); }
}
void glClearColor(GLfloat a,GLfloat b,GLfloat c,GLfloat d) {
    clearColor[0]=a;clearColor[1]=b;clearColor[2]=c;clearColor[3]=d;
}
void glClearDepthf(GLfloat a) { clearDepth=a; }
void glClearStencil(GLint a) { clearStencil=a; }
void glDisable(GLenum x) { assert(x==GL_SCISSOR_TEST); scissor=false; }
void glEnable(GLenum x) { assert(x==GL_SCISSOR_TEST); scissor=true; }
void glClear(GLbitfield bits) {
    assert(!scissor);
    if(bits&GL_COLOR_BUFFER_BIT) for(int i=0;i<4;++i) assert(colorMask[i]==1);
    if(bits&GL_DEPTH_BUFFER_BIT) assert(depthMask==1);
    if(bits&GL_STENCIL_BUFFER_BIT) assert(frontMask==-1 && backMask==-1);
    lastBits=bits; ++clearCalls;
}
GLenum glGetError() { GLenum e=glError; glError=GL_NO_ERROR; return e; }
int main() {
    static_assert(sizeof(void*)==8, "LP64 required");
    const float color[4]={0.9f,0.8f,0.7f,0.6f};
    assert(!R_AndroidGlesClear(0,color,0.5f,2));
    assert(!R_AndroidGlesClear(8,color,0.5f,2));
    assert(!R_AndroidGlesClear(1,nullptr,0.5f,2));
    assert(!R_AndroidGlesClear(1,color,-0.1f,2));
    assert(!R_AndroidGlesClear(1,color,1.1f,2));
    float bad[4]={0,0,std::numeric_limits<float>::quiet_NaN(),0};
    assert(!R_AndroidGlesClear(1,bad,0.5f,2));
    hasContext=false;
    assert(!R_AndroidGlesClear(7,color,0.5f,2));
    hasContext=true;
    assert(clearCalls==0);
    for(unsigned int flags=1; flags<=7; ++flags) {
        assert(R_AndroidGlesClear(flags,color,0.5f,2));
        GLbitfield expected=((flags&1)?GL_COLOR_BUFFER_BIT:0)
            |((flags&2)?GL_DEPTH_BUFFER_BIT:0)
            |((flags&4)?GL_STENCIL_BUFFER_BIT:0);
        assert(lastBits==expected);
        assert(scissor && colorMask[0]==1 && colorMask[1]==0
               && colorMask[2]==1 && colorMask[3]==0);
        assert(depthMask==0 && frontMask==1 && backMask==2);
        assert(clearStencil==9 && clearDepth==0.25f);
        assert(clearColor[0]==0.2f && clearColor[3]==0.5f);
    }
    assert(clearCalls==7);
    glError=0x0502;
    assert(!R_AndroidGlesClear(1,color,0.5f,2));
    assert(clearCalls==8);
    assert(scissor && colorMask[1]==0);
    std::puts("IW3_ORIGINAL_CLEAR_GLES3_HOST_SANITIZER_PASS_NOT_FRAME");
}
"""

class OriginalClearGles3(unittest.TestCase):
    def test_original_command_wired_and_gles_state_restored(self):
        self.assertTrue(SRC.exists())
        backend = BACKEND.read_text()
        self.assertIn("R_AndroidGlesClear(cmd->whichToClear, cmd->color", backend)
        self.assertIn('Com_Error(ERR_FATAL, "IW3 Android: original clear command GLES3 failed")', backend)
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
                 "-fno-omit-frame-pointer", "-I", str(base), "-I", str(SRC.parent),
                 str(base / "test.cpp"), "-o", str(binary)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(binary)], capture_output=True, text=True,
                                 env=env, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_CLEAR_GLES3_HOST_SANITIZER_PASS_NOT_FRAME", run.stdout)

if __name__ == "__main__":
    unittest.main()
