"""Host ASan/UBSan regression for the ORIGINAL IW3 indexed draw GLES3 seam.
All GL/EGL calls are mocked; this is NOT a rendered frame or playable APK.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "third_party/KisakCOD/src/gfx_d3d"
EGL = r"""
#pragma once
using EGLDisplay=void*; using EGLContext=void*;
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_NO_CONTEXT ((EGLContext)0)
EGLDisplay eglGetCurrentDisplay();
EGLContext eglGetCurrentContext();
"""
GLES = r"""
#pragma once
using GLenum=unsigned int; using GLuint=unsigned int;
using GLboolean=unsigned char; using GLint=int; using GLsizei=int;
#define GL_TRUE 1
#define GL_NO_ERROR 0
#define GL_ELEMENT_ARRAY_BUFFER 0x8893
#define GL_ELEMENT_ARRAY_BUFFER_BINDING 0x8895
#define GL_CURRENT_PROGRAM 0x8B8D
#define GL_VERTEX_ARRAY_BINDING 0x85B5
#define GL_BUFFER_SIZE 0x8764
#define GL_VERTEX_ATTRIB_ARRAY_ENABLED 0x8622
#define GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING 0x889F
#define GL_TRIANGLES 0x0004
#define GL_UNSIGNED_SHORT 0x1403
GLenum glGetError();
GLboolean glIsBuffer(GLuint);
void glBindBuffer(GLenum,GLuint);
void glGetIntegerv(GLenum,GLint*);
void glGetBufferParameteriv(GLenum,GLenum,GLint*);
void glGetVertexAttribiv(GLuint,GLenum,GLint*);
void glDrawElements(GLenum,GLsizei,GLenum,const void*);
"""
HARNESS = r"""
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <limits>
#include "r_android_indexed_draw.cpp"
static bool context=true, failBind=false, failDraw=false;
static GLenum error=GL_NO_ERROR;
static GLint bound=0, program=1, vao=2, attrib=1, vertexBuffer=11, bufferSize=128;
static int calls=0, count=0;
static std::uintptr_t offset=9999;
EGLDisplay eglGetCurrentDisplay(){return context?(void*)1:EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return context?(void*)2:EGL_NO_CONTEXT;}
GLenum glGetError(){GLenum e=error;error=GL_NO_ERROR;return e;}
GLboolean glIsBuffer(GLuint id){return (id==7||id==8)?GL_TRUE:0;}
void glBindBuffer(GLenum e,GLuint id){
    assert(e==GL_ELEMENT_ARRAY_BUFFER);
    if(failBind){error=0x502;return;}
    bound=static_cast<GLint>(id);
}
void glGetIntegerv(GLenum e,GLint *v){
    if(e==GL_ELEMENT_ARRAY_BUFFER_BINDING)*v=bound;
    else if(e==GL_CURRENT_PROGRAM)*v=program;
    else if(e==GL_VERTEX_ARRAY_BINDING)*v=vao;
    else assert(false);
}
void glGetBufferParameteriv(GLenum a,GLenum p,GLint *v){
    assert(a==GL_ELEMENT_ARRAY_BUFFER && p==GL_BUFFER_SIZE);
    *v=bufferSize;
}
void glGetVertexAttribiv(GLuint i,GLenum p,GLint *v){
    assert(i==0);
    if(p==GL_VERTEX_ATTRIB_ARRAY_ENABLED)*v=attrib;
    else if(p==GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING)*v=vertexBuffer;
    else assert(false);
}
void glDrawElements(GLenum mode,GLsizei n,GLenum type,const void *ptr){
    assert(mode==GL_TRIANGLES && type==GL_UNSIGNED_SHORT);
    ++calls;count=n;offset=reinterpret_cast<std::uintptr_t>(ptr);
    if(failDraw)error=0x502;
}
int main(){
    static_assert(sizeof(void*)==8, "LP64 regression");
    const void *original=reinterpret_cast<void*>(0x1234);
    const void *other=reinterpret_cast<void*>(0x5678);
    assert(!R_AndroidGlesBindIndexBuffer(original));
    assert(!R_AndroidGlesRegisterIndexBuffer(nullptr,7,64));
    assert(!R_AndroidGlesRegisterIndexBuffer(original,0,64));
    assert(!R_AndroidGlesRegisterIndexBuffer(original,7,0));
    assert(!R_AndroidGlesRegisterIndexBuffer(original,9,64));
    assert(R_AndroidGlesRegisterIndexBuffer(original,7,64));
    assert(!R_AndroidGlesRegisterIndexBuffer(original,8,64));
    assert(!R_AndroidGlesBindIndexBuffer(other));
    assert(R_AndroidGlesBindIndexBuffer(original) && bound==7);
    assert(!R_AndroidGlesDrawIndexed(-1,1,3));
    assert(!R_AndroidGlesDrawIndexed(0,0,3));
    assert(!R_AndroidGlesDrawIndexed(0,1,0));
    assert(!R_AndroidGlesDrawIndexed(63,1,3));
    assert(!R_AndroidGlesDrawIndexed(0,std::numeric_limits<int>::max(),3));
    program=0; assert(!R_AndroidGlesDrawIndexed(0,1,3));program=1;
    vao=0; assert(!R_AndroidGlesDrawIndexed(0,1,3));vao=2;
    attrib=0; assert(!R_AndroidGlesDrawIndexed(0,1,3));attrib=1;
    vertexBuffer=0;assert(!R_AndroidGlesDrawIndexed(0,1,3));vertexBuffer=11;
    bufferSize=4;assert(!R_AndroidGlesDrawIndexed(0,2,4));bufferSize=128;
    assert(R_AndroidGlesDrawIndexed(2,3,4));
    assert(calls==1 && count==9 && offset==4);
    failDraw=true;assert(!R_AndroidGlesDrawIndexed(0,1,3));failDraw=false;
    bound=8;assert(!R_AndroidGlesDrawIndexed(0,1,3));bound=7;
    context=false;assert(!R_AndroidGlesDrawIndexed(0,1,3));
    assert(!R_AndroidGlesRegisterIndexBuffer(other,8,64));
    context=true;
    assert(R_AndroidGlesUnregisterIndexBuffer(original));
    assert(!R_AndroidGlesDrawIndexed(0,1,3));
    assert(!R_AndroidGlesUnregisterIndexBuffer(original));
    assert(R_AndroidGlesRegisterIndexBuffer(other,8,64));
    failBind=true;assert(!R_AndroidGlesBindIndexBuffer(other));failBind=false;
    assert(R_AndroidGlesBindIndexBuffer(other));
    R_AndroidGlesInvalidateIndexBuffers();
    assert(!R_AndroidGlesBindIndexBuffer(other));
    assert(R_AndroidGlesRegisterIndexBuffer(original,7,64));
    std::puts("IW3_ORIGINAL_INDEXED_DRAW_GLES3_HOST_SANITIZER_PASS_NOT_FRAME");
}
"""

class OriginalIndexedDrawGles3(unittest.TestCase):
    def test_original_indexed_draw_requires_real_resources(self):
        state = (GFX / "r_state.cpp").read_text()
        self.assertIn('#include "r_android_indexed_draw.h"', state)
        self.assertIn("R_AndroidGlesBindIndexBuffer(ib)", state)
        self.assertIn("R_AndroidGlesDrawIndexed(args->baseIndex, triCount, args->vertexCount)", state)
        self.assertIn("device->SetIndices(ib)", state)
        self.assertIn("device->DrawIndexedPrimitive(D3DPT_TRIANGLELIST", state)
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
            self.assertIn("IW3_ORIGINAL_INDEXED_DRAW_GLES3_HOST_SANITIZER_PASS_NOT_FRAME", run.stdout)

if __name__ == "__main__":
    unittest.main()
