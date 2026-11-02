"""ASan/UBSan host regression of original IW3 R_ChangeStreamSource GLES3 seam.
EGL/GLES are mocked: no scene, map, frame, or gameplay is proven.
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
using GLenum=unsigned int; using GLuint=unsigned int;
using GLboolean=unsigned char; using GLint=int;
#define GL_TRUE 1
#define GL_NO_ERROR 0
#define GL_ARRAY_BUFFER 0x8892
#define GL_ARRAY_BUFFER_BINDING 0x8894
#define GL_BUFFER_SIZE 0x8764
GLenum glGetError();
GLboolean glIsBuffer(GLuint);
void glBindBuffer(GLenum,GLuint);
void glGetIntegerv(GLenum,GLint*);
void glGetBufferParameteriv(GLenum,GLenum,GLint*);
"""
HARNESS = r"""
#include <cassert>
#include <cstdint>
#include <cstdio>
#include "r_android_vertex_stream.cpp"
static bool context=true, badBind=false, badSize=false;
static GLenum error=GL_NO_ERROR;
static GLint bound=99;
static int attribCalls=0;
EGLDisplay eglGetCurrentDisplay(){return context?(void*)1:EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return context?(void*)2:EGL_NO_CONTEXT;}
GLenum glGetError(){GLenum e=error;error=GL_NO_ERROR;return e;}
GLboolean glIsBuffer(GLuint id){return (id==7||id==8)?GL_TRUE:0;}
void glBindBuffer(GLenum target,GLuint id){
    assert(target==GL_ARRAY_BUFFER);
    if(badBind && id==7){error=0x502;return;}
    bound=static_cast<GLint>(id);
}
void glGetIntegerv(GLenum target,GLint *v){
    assert(target==GL_ARRAY_BUFFER_BINDING);*v=bound;
}
void glGetBufferParameteriv(GLenum target,GLenum name,GLint *v){
    assert(target==GL_ARRAY_BUFFER && name==GL_BUFFER_SIZE);
    *v=badSize?8:256;
}
int main(){
    static_assert(sizeof(void*)==8,"LP64 test");
    const void *a=(void*)0x1234, *b=(void*)0x5678;
    unsigned int id=0;std::size_t offset=0,stride=0;
    assert(!R_AndroidGlesRegisterVertexBuffer(nullptr,7,256));
    assert(!R_AndroidGlesRegisterVertexBuffer(a,0,256));
    assert(!R_AndroidGlesRegisterVertexBuffer(a,9,256));
    assert(!R_AndroidGlesRegisterVertexBuffer(a,7,0));
    assert(R_AndroidGlesRegisterVertexBuffer(a,7,256));
    assert(bound==99);
    assert(!R_AndroidGlesRegisterVertexBuffer(a,8,256));
    assert(R_AndroidGlesRegisterVertexBuffer(b,8,256));
    assert(!R_AndroidGlesChangeStreamSource(2,a,0,16));
    assert(!R_AndroidGlesChangeStreamSource(0,b,0,0));
    assert(!R_AndroidGlesChangeStreamSource(0,a,255,2));
    assert(!R_AndroidGlesChangeStreamSource(0,a,256,1));
    assert(!R_AndroidGlesChangeStreamSource(0,nullptr,1,0));
    assert(!R_AndroidGlesChangeStreamSource(0,(void*)0x9999,0,16));
    assert(R_AndroidGlesChangeStreamSource(0,a,32,16));
    assert(R_AndroidGlesChangeStreamSource(1,b,0,32));
    assert(bound==99);
    assert(R_AndroidGlesGetStreamSource(0,&id,&offset,&stride));
    assert(id==7 && offset==32 && stride==16);
    assert(R_AndroidGlesGetStreamSource(1,&id,&offset,&stride));
    assert(id==8 && offset==0 && stride==32);
    assert(!R_AndroidGlesGetStreamSource(2,&id,&offset,&stride));
    assert(!R_AndroidGlesGetStreamSource(0,nullptr,&offset,&stride));
    badSize=true;
    assert(!R_AndroidGlesChangeStreamSource(0,a,32,16));
    assert(!R_AndroidGlesGetStreamSource(0,&id,&offset,&stride));
    badSize=false;
    badBind=true;
    assert(!R_AndroidGlesChangeStreamSource(0,a,32,16));
    assert(bound==99);
    badBind=false;
    context=false;
    assert(!R_AndroidGlesGetStreamSource(0,&id,&offset,&stride));
    assert(!R_AndroidGlesChangeStreamSource(0,nullptr,0,0));
    context=true;
    assert(R_AndroidGlesUnregisterVertexBuffer(a));
    assert(!R_AndroidGlesGetStreamSource(0,&id,&offset,&stride));
    assert(R_AndroidGlesGetStreamSource(1,&id,&offset,&stride));
    assert(R_AndroidGlesChangeStreamSource(1,nullptr,0,0));
    assert(!R_AndroidGlesGetStreamSource(1,&id,&offset,&stride));
    R_AndroidGlesInvalidateVertexStreams();
    assert(!R_AndroidGlesChangeStreamSource(0,b,0,16));
    assert(R_AndroidGlesRegisterVertexBuffer(a,7,256));
    std::puts("IW3_ORIGINAL_VERTEX_STREAM_GLES3_HOST_SANITIZER_PASS_NOT_FRAME");
}
"""

class OriginalVertexStreamGles3(unittest.TestCase):
    def test_original_stream_source_requires_real_vbo(self):
        original = (GFX / "r_state.cpp").read_text()
        self.assertIn('#include "r_android_vertex_stream.h"', original)
        self.assertIn("R_AndroidGlesChangeStreamSource(streamIndex, vb, vertexOffset, vertexStride)", original)
        self.assertIn("device->SetStreamSource(streamIndex, vb, vertexOffset, vertexStride)", original)
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
            self.assertIn("IW3_ORIGINAL_VERTEX_STREAM_GLES3_HOST_SANITIZER_PASS_NOT_FRAME", run.stdout)

if __name__ == "__main__":
    unittest.main()
