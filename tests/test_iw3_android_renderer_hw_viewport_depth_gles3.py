"""Original IW3 hardware viewport + depth-range bridge host ASan/UBSan regression.
EGL/GLES are MOCKED: no GPU frame, map, or playable APK is proven.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "third_party/KisakCOD/src/gfx_d3d"
EGL_HEADER = r"""
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
GLES_HEADER = r"""
#pragma once
using GLuint = unsigned int;
using GLenum = unsigned int;
using GLint = int;
using GLsizei = int;
using GLfloat = float;
#define GL_NO_ERROR 0
#define GL_NONE 0
#define GL_FRAMEBUFFER 0x8D40
#define GL_FRAMEBUFFER_BINDING 0x8CA6
#define GL_VIEWPORT 0x0BA2
#define GL_DEPTH_RANGE 0x0B70
#define GL_COLOR_ATTACHMENT0 0x8CE0
#define GL_TEXTURE_2D 0x0DE1
#define GL_DEPTH_STENCIL_ATTACHMENT 0x821A
#define GL_RENDERBUFFER 0x8D41
#define GL_FRAMEBUFFER_COMPLETE 0x8CD5
GLenum glGetError();
void glGetIntegerv(GLenum, GLint*);
void glGetFloatv(GLenum, GLfloat*);
void glGenFramebuffers(GLsizei,GLuint*);
void glBindFramebuffer(GLenum,GLuint);
void glFramebufferTexture2D(GLenum,GLenum,GLenum,GLuint,GLint);
void glDrawBuffers(GLsizei,const GLenum*);
void glReadBuffer(GLenum);
void glFramebufferRenderbuffer(GLenum,GLenum,GLenum,GLuint);
GLenum glCheckFramebufferStatus(GLenum);
void glDeleteFramebuffers(GLsizei,const GLuint*);
void glViewport(GLint,GLint,GLsizei,GLsizei);
void glDepthRangef(GLfloat,GLfloat);
"""
HARNESS = r"""
#include <cassert>
#include <cmath>
#include <cstdio>
#include <limits>
#include "r_android_target.cpp"
#include "r_android_viewport.cpp"
#include "r_android_hw_viewport.cpp"
static bool context = true, failDepth = false;
static GLuint bound = 0, nextFbo = 10;
static GLenum error = GL_NO_ERROR;
static GLint viewport[4] = {1,2,3,4};
static GLfloat depthRange[2] = {0.0f,1.0f};
EGLDisplay eglGetCurrentDisplay(){return context?(void*)1:EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return context?(void*)2:EGL_NO_CONTEXT;}
EGLSurface eglGetCurrentSurface(int){return context?(void*)3:EGL_NO_SURFACE;}
EGLint eglQuerySurface(EGLDisplay,EGLSurface,EGLint k,EGLint* v){
    *v=k==EGL_WIDTH?640:480;return EGL_TRUE;
}
GLenum glGetError(){GLenum e=error;error=GL_NO_ERROR;return e;}
void glGetIntegerv(GLenum p,GLint* v){
    if(p==GL_FRAMEBUFFER_BINDING)*v=bound;
    else if(p==GL_VIEWPORT)for(int i=0;i<4;++i)v[i]=viewport[i];
}
void glGetFloatv(GLenum p,GLfloat* v){
    if(p==GL_DEPTH_RANGE){v[0]=depthRange[0];v[1]=depthRange[1];}
}
void glGenFramebuffers(GLsizei,GLuint* v){*v=nextFbo++;}
void glBindFramebuffer(GLenum,GLuint v){bound=v;}
void glFramebufferTexture2D(GLenum,GLenum,GLenum,GLuint,GLint){}
void glDrawBuffers(GLsizei,const GLenum*){}
void glReadBuffer(GLenum){}
void glFramebufferRenderbuffer(GLenum,GLenum,GLenum,GLuint){}
GLenum glCheckFramebufferStatus(GLenum){return GL_FRAMEBUFFER_COMPLETE;}
void glDeleteFramebuffers(GLsizei,const GLuint*){}
void glViewport(GLint x,GLint y,GLsizei w,GLsizei h){
    viewport[0]=x;viewport[1]=y;viewport[2]=w;viewport[3]=h;
}
void glDepthRangef(GLfloat n,GLfloat f){
    depthRange[0]=n;depthRange[1]=f;
    if(failDepth)error=0x502;
}
int main(){
    static_assert(sizeof(void*)==8, "LP64 test required");
    int w=-1,h=-1;
    assert(!R_AndroidGlesGetBoundTargetDimensions(&w,&h));
    assert(!R_AndroidGlesHardwareViewport(0,0,1,1,0.0f,1.0f));
    assert(R_AndroidGlesBindTarget(1,640,480));
    assert(R_AndroidGlesGetBoundTargetDimensions(&w,&h) && w==640 && h==480);
    assert(!R_AndroidGlesGetBoundTargetDimensions(nullptr,&h));
    assert(R_AndroidGlesHardwareViewport(10,20,100,50,0.015625f,1.0f));
    assert(viewport[0]==10 && viewport[1]==410 && viewport[2]==100 && viewport[3]==50);
    assert(depthRange[0]==0.015625f && depthRange[1]==1.0f);
    assert(!R_AndroidGlesHardwareViewport(0,0,1000,50,0.0f,1.0f));
    assert(!R_AndroidGlesHardwareViewport(0,0,10,10,1.0f,0.0f));
    assert(!R_AndroidGlesHardwareViewport(0,0,10,10,-0.1f,1.0f));
    assert(!R_AndroidGlesHardwareViewport(0,0,10,10,0.0f,1.1f));
    assert(!R_AndroidGlesHardwareViewport(0,0,10,10,
        std::numeric_limits<float>::quiet_NaN(),1.0f));
    assert(viewport[0]==10 && viewport[1]==410);
    context=false;
    assert(!R_AndroidGlesGetBoundTargetDimensions(&w,&h));
    assert(!R_AndroidGlesHardwareViewport(0,0,10,10,0.0f,1.0f));
    context=true;
    failDepth=true;
    assert(!R_AndroidGlesHardwareViewport(20,30,60,70,0.2f,0.8f));
    failDepth=false;
    assert(viewport[0]==10 && viewport[1]==410);
    assert(depthRange[0]==0.015625f && depthRange[1]==1.0f);
    assert(R_AndroidGlesRegisterTarget(2,22,0,256,256));
    assert(R_AndroidGlesBindTarget(2,256,256));
    assert(R_AndroidGlesGetBoundTargetDimensions(&w,&h) && w==256 && h==256);
    assert(R_AndroidGlesHardwareViewport(8,16,32,64,0.0f,1.0f));
    assert(viewport[0]==8 && viewport[1]==176);
    assert(R_AndroidGlesReleaseTargets());
    assert(!R_AndroidGlesGetBoundTargetDimensions(&w,&h));
    std::puts("IW3_ORIGINAL_HW_VIEWPORT_DEPTH_GLES3_HOST_SANITIZER_PASS_NOT_FRAME");
}
"""

class OriginalHardwareViewportDepthGles3(unittest.TestCase):
    def test_original_hardware_viewport_depth_and_context(self):
        state = (GFX / "r_state.cpp").read_text()
        self.assertIn("void __cdecl R_HW_SetViewport(", state)
        self.assertIn("R_AndroidGlesHardwareViewport(", state)
        self.assertIn("device->SetViewport(&d3dViewport)", state)
        self.assertIn("Vec4Add(outMatrix[3], worldOffset, outMatrix[3]);", state)
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "EGL").mkdir()
            (base / "GLES3").mkdir()
            (base / "EGL/egl.h").write_text(EGL_HEADER)
            (base / "GLES3/gl3.h").write_text(GLES_HEADER)
            (base / "test.cpp").write_text(HARNESS)
            binary = base / "test"
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-D__ANDROID__",
                 "-O1", "-g", "-UNDEBUG", "-fsanitize=address,undefined",
                 "-fno-omit-frame-pointer", "-I", str(base), "-I", str(GFX),
                 str(base / "test.cpp"), "-o", str(binary)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(binary)], capture_output=True, text=True,
                                 env=env, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_HW_VIEWPORT_DEPTH_GLES3_HOST_SANITIZER_PASS_NOT_FRAME",
                          run.stdout)

if __name__ == "__main__":
    unittest.main()
