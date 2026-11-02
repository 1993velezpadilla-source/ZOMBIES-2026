"""Host ASan/UBSan regression for original IW3 R_HW_SetRenderTarget -> GLES3 FBO.
Mocked GL/EGL does NOT prove a rendered IW3 frame or playable APK.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_android_target.cpp"
ORIGINAL = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_state.cpp"

EGL_HEADER = """
#pragma once
using EGLDisplay = void*;
using EGLContext = void*;
using EGLSurface = void*;
using EGLint = int;
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_NO_CONTEXT ((EGLContext)0)
#define EGL_NO_SURFACE ((EGLSurface)0)
#define EGL_DRAW 0x3059
#define EGL_WIDTH 0x3057
#define EGL_HEIGHT 0x3056
#define EGL_TRUE 1
EGLDisplay eglGetCurrentDisplay();
EGLContext eglGetCurrentContext();
EGLSurface eglGetCurrentSurface(int);
EGLint eglQuerySurface(EGLDisplay,EGLSurface,EGLint,EGLint*);
"""

GLES_HEADER = """
#pragma once
using GLuint = unsigned int;
using GLenum = unsigned int;
using GLint = int;
using GLsizei = int;
#define GL_NO_ERROR 0
#define GL_NONE 0
#define GL_FRAMEBUFFER 0x8D40
#define GL_FRAMEBUFFER_BINDING 0x8CA6
#define GL_VIEWPORT 0x0BA2
#define GL_COLOR_ATTACHMENT0 0x8CE0
#define GL_TEXTURE_2D 0x0DE1
#define GL_DEPTH_STENCIL_ATTACHMENT 0x821A
#define GL_RENDERBUFFER 0x8D41
#define GL_FRAMEBUFFER_COMPLETE 0x8CD5
GLenum glGetError();
void glGetIntegerv(GLenum, GLint*);
void glGenFramebuffers(GLsizei,GLuint*);
void glBindFramebuffer(GLenum,GLuint);
void glFramebufferTexture2D(GLenum,GLenum,GLenum,GLuint,GLint);
void glDrawBuffers(GLsizei,const GLenum*);
void glReadBuffer(GLenum);
void glFramebufferRenderbuffer(GLenum,GLenum,GLenum,GLuint);
GLenum glCheckFramebufferStatus(GLenum);
void glDeleteFramebuffers(GLsizei,const GLuint*);
void glViewport(GLint,GLint,GLsizei,GLsizei);
"""

HARNESS = r"""
#include <cassert>
#include <cstdio>
#include "r_android_target.cpp"
static bool hasContext = true, badFbo = false, badGl = false;
static GLuint bound = 0, nextId = 10, deleted = 0;
static GLint vp[4] = {4,5,20,30};
static unsigned int generated = 0, binds = 0;
EGLDisplay eglGetCurrentDisplay(){return hasContext ? (void*)1 : EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return hasContext ? (void*)2 : EGL_NO_CONTEXT;}
EGLSurface eglGetCurrentSurface(int){return hasContext ? (void*)3 : EGL_NO_SURFACE;}
EGLint eglQuerySurface(EGLDisplay,EGLSurface,EGLint key,EGLint* val){
    *val=key==EGL_WIDTH?640:480;return EGL_TRUE;
}
GLenum glGetError(){if(badGl){badGl=false;return 0x501;}return GL_NO_ERROR;}
void glGetIntegerv(GLenum p,GLint* v){
    if(p==GL_FRAMEBUFFER_BINDING)*v=bound;
    else if(p==GL_VIEWPORT)for(int i=0;i<4;i++)v[i]=vp[i];
}
void glGenFramebuffers(GLsizei,GLuint* f){*f=nextId++;generated++;}
void glBindFramebuffer(GLenum,GLuint f){bound=f;binds++;}
void glFramebufferTexture2D(GLenum,GLenum,GLenum,GLuint,GLint){}
void glDrawBuffers(GLsizei,const GLenum*){}
void glReadBuffer(GLenum){}
void glFramebufferRenderbuffer(GLenum,GLenum,GLenum,GLuint){}
GLenum glCheckFramebufferStatus(GLenum){
    return badFbo?0x8CD6:GL_FRAMEBUFFER_COMPLETE;
}
void glDeleteFramebuffers(GLsizei,const GLuint* f){deleted=*f;}
void glViewport(GLint x,GLint y,GLsizei w,GLsizei h){
    vp[0]=x;vp[1]=y;vp[2]=w;vp[3]=h;
}
int main(){
    static_assert(sizeof(void*)==8, "LP64 regression required");
    assert(!R_AndroidGlesBindTarget(1,800,480)); // stale EGL dimensions
    assert(R_AndroidGlesBindTarget(1,640,480));
    assert(bound==0 && vp[2]==640 && vp[3]==480);
    assert(!R_AndroidGlesBindTarget(2,64,64)); // no invented offscreen image
    assert(!R_AndroidGlesRegisterTarget(1,22,0,64,64));
    assert(!R_AndroidGlesRegisterTarget(2,0,0,64,64));
    badFbo=true;
    assert(!R_AndroidGlesRegisterTarget(2,22,0,64,64));
    assert(deleted==10 && bound==0);
    badFbo=false;
    assert(R_AndroidGlesRegisterTarget(2,22,0,64,64));
    assert(!R_AndroidGlesRegisterTarget(2,22,0,64,64));
    assert(!R_AndroidGlesBindTarget(2,32,64));
    assert(R_AndroidGlesBindTarget(2,64,64));
    assert(bound==11 && vp[2]==64);
    hasContext=false;
    assert(!R_AndroidGlesReleaseTargets());
    hasContext=true;
    assert(R_AndroidGlesReleaseTargets());
    assert(deleted==11 && bound==0);
    assert(!R_AndroidGlesBindTarget(2,64,64));
    assert(R_AndroidGlesBindTarget(1,640,480));
    assert(R_AndroidGlesReleaseTargets());
    puts("IW3_ORIGINAL_RENDER_TARGET_GLES3_HOST_SANITIZER_PASS_NOT_FRAME");
}
"""

class OriginalRenderTargetGles3(unittest.TestCase):
    def test_original_target_binding_and_fbo(self):
        original = ORIGINAL.read_text()
        self.assertIn('#include "r_android_target.h"', original)
        self.assertIn("void __cdecl R_HW_SetRenderTarget(", original)
        self.assertIn("R_AndroidGlesBindTarget(static_cast<int>(newTargetId)", original)
        self.assertIn("IW3 Android: original R_HW_SetRenderTarget GLES3 binding failed", original)
        self.assertIn("device->SetRenderTarget(0, gfxRenderTargets[newTargetId].surface.color)", original)
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
            self.assertIn("IW3_ORIGINAL_RENDER_TARGET_GLES3_HOST_SANITIZER_PASS_NOT_FRAME",
                          run.stdout)

if __name__ == "__main__":
    unittest.main()
