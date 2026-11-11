"""Host ASan/UBSan checks of real GLES3 VBO/EBO storage for IW3 identities.
GL/EGL are mocked: no original r_buffers call-site, scene, map or frame proven.
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
#include <cstddef>
using GLenum=unsigned int; using GLuint=unsigned int;
using GLboolean=unsigned char; using GLint=int; using GLsizei=int;
using GLintptr=std::ptrdiff_t; using GLsizeiptr=std::ptrdiff_t;
#define GL_TRUE 1
#define GL_NO_ERROR 0
#define GL_ARRAY_BUFFER 0x8892
#define GL_ELEMENT_ARRAY_BUFFER 0x8893
#define GL_ARRAY_BUFFER_BINDING 0x8894
#define GL_ELEMENT_ARRAY_BUFFER_BINDING 0x8895
#define GL_BUFFER_SIZE 0x8764
#define GL_STATIC_DRAW 0x88E4
#define GL_DYNAMIC_DRAW 0x88E8
#define GL_CURRENT_PROGRAM 0x8B8D
#define GL_VERTEX_ARRAY_BINDING 0x85B5
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
void glGenBuffers(GLsizei,GLuint*);
void glBufferData(GLenum,GLsizeiptr,const void*,GLenum);
void glBufferSubData(GLenum,GLintptr,GLsizeiptr,const void*);
void glDeleteBuffers(GLsizei,const GLuint*);
"""
HARNESS = r"""
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <unordered_map>
#include <vector>
#include "r_android_buffer_storage.h"
#include "r_android_vertex_stream.h"
#include "r_android_indexed_draw.h"
#include <EGL/egl.h>
#include <GLES3/gl3.h>
static bool context=true, failData=false, failUpdate=false;
static GLenum error=GL_NO_ERROR;
static GLuint nextId=10, arrayBound=77, elementBound=88;
static std::unordered_map<GLuint,std::vector<unsigned char>> objects;
EGLDisplay eglGetCurrentDisplay(){return context?(void*)1:EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return context?(void*)2:EGL_NO_CONTEXT;}
GLenum glGetError(){auto e=error;error=GL_NO_ERROR;return e;}
GLboolean glIsBuffer(GLuint id){return objects.count(id)?GL_TRUE:0;}
void glGetIntegerv(GLenum e,GLint *v){
    if(e==GL_ARRAY_BUFFER_BINDING)*v=static_cast<GLint>(arrayBound);
    else if(e==GL_ELEMENT_ARRAY_BUFFER_BINDING)*v=static_cast<GLint>(elementBound);
    else if(e==GL_CURRENT_PROGRAM)*v=1;
    else if(e==GL_VERTEX_ARRAY_BINDING)*v=2;
    else assert(false);
}
void glBindBuffer(GLenum e,GLuint id){
    if(e==GL_ARRAY_BUFFER)arrayBound=id;
    else if(e==GL_ELEMENT_ARRAY_BUFFER)elementBound=id;
    else assert(false);
}
void glGetBufferParameteriv(GLenum e,GLenum p,GLint *v){
    assert(p==GL_BUFFER_SIZE);
    const GLuint id=e==GL_ARRAY_BUFFER?arrayBound:elementBound;
    *v=objects.count(id)?static_cast<GLint>(objects.at(id).size()):0;
}
void glGenBuffers(GLsizei n,GLuint *out){
    assert(n==1);*out=nextId++;objects[*out]={};
}
void glBufferData(GLenum e,GLsizeiptr n,const void *data,GLenum usage){
    assert(n>0 && (usage==GL_STATIC_DRAW||usage==GL_DYNAMIC_DRAW));
    if(failData){error=0x502;return;}
    const GLuint id=e==GL_ARRAY_BUFFER?arrayBound:elementBound;
    assert(objects.count(id));
    auto &v=objects.at(id);v.resize(static_cast<std::size_t>(n));
    if(data)std::memcpy(v.data(),data,static_cast<std::size_t>(n));
}
void glBufferSubData(GLenum e,GLintptr off,GLsizeiptr n,const void *data){
    if(failUpdate){error=0x502;return;}
    const GLuint id=e==GL_ARRAY_BUFFER?arrayBound:elementBound;
    assert(objects.count(id) && off>=0 && n>0);
    auto &v=objects.at(id);
    assert(static_cast<std::size_t>(off+n)<=v.size());
    std::memcpy(v.data()+off,data,static_cast<std::size_t>(n));
}
void glDeleteBuffers(GLsizei n,const GLuint *ids){
    for(int i=0;i<n;++i){objects.erase(ids[i]);
        if(arrayBound==ids[i])arrayBound=0;
        if(elementBound==ids[i])elementBound=0;
    }
}
void glGetVertexAttribiv(GLuint,GLenum e,GLint *v){
    *v=e==GL_VERTEX_ATTRIB_ARRAY_ENABLED?1:11;
}
void glDrawElements(GLenum,GLsizei,GLenum,const void*){}
int main(){
    static_assert(sizeof(void*)==8,"LP64 required");
    const void *v=(void*)0x1234, *i=(void*)0x5678, *bad=(void*)0x9999;
    unsigned char verts[64]={};unsigned short indices[16]={};
    unsigned int id=0;std::size_t off=0,stride=0;
    assert(!R_AndroidGlesCreateVertexStorage(nullptr,64,verts,false));
    assert(!R_AndroidGlesCreateVertexStorage(v,0,verts,false));
    assert(!R_AndroidGlesCreateIndexStorage(i,31,indices,false));
    assert(R_AndroidGlesCreateVertexStorage(v,64,verts,false));
    assert(arrayBound==77 && objects.size()==1);
    assert(!R_AndroidGlesCreateVertexStorage(v,64,verts,false));
    assert(R_AndroidGlesChangeStreamSource(0,v,0,16));
    assert(R_AndroidGlesGetStreamSource(0,&id,&off,&stride));
    assert(id>=10 && off==0 && stride==16 && objects.at(id).size()==64);
    const GLuint vid=id;
    assert(R_AndroidGlesCreateIndexStorage(i,32,indices,true));
    assert(elementBound==88 && objects.size()==2);
    assert(R_AndroidGlesBindIndexBuffer(i));
    const GLuint iid=elementBound;
    assert(iid!=vid && objects.at(iid).size()==32);
    unsigned char update[4]={1,2,3,4};
    assert(!R_AndroidGlesUpdateBufferStorage(bad,0,update,4));
    assert(!R_AndroidGlesUpdateBufferStorage(v,63,update,4));
    assert(!R_AndroidGlesUpdateBufferStorage(v,0,nullptr,4));
    assert(R_AndroidGlesUpdateBufferStorage(v,4,update,4));
    assert(arrayBound==77 && objects.at(vid)[4]==1 && objects.at(vid)[7]==4);
    failUpdate=true;
    assert(!R_AndroidGlesUpdateBufferStorage(v,8,update,4));
    assert(arrayBound==77);failUpdate=false;
    failData=true;
    assert(!R_AndroidGlesCreateVertexStorage(bad,16,nullptr,false));
    assert(objects.size()==2 && arrayBound==77);failData=false;
    context=false;
    assert(!R_AndroidGlesCreateVertexStorage(bad,16,nullptr,false));
    assert(!R_AndroidGlesDestroyBufferStorage(v));
    context=true;
    assert(R_AndroidGlesDestroyBufferStorage(v));
    assert(!R_AndroidGlesGetStreamSource(0,&id,&off,&stride));
    assert(!R_AndroidGlesDestroyBufferStorage(v));
    assert(R_AndroidGlesDestroyBufferStorage(i));
    assert(objects.empty());
    assert(!R_AndroidGlesBindIndexBuffer(i));
    R_AndroidGlesInvalidateBufferStorage();
    R_AndroidGlesInvalidateVertexStreams();
    R_AndroidGlesInvalidateIndexBuffers();
    assert(R_AndroidGlesCreateVertexStorage(v,16,nullptr,true));
    assert(R_AndroidGlesDestroyBufferStorage(v));
    assert(objects.empty());
    std::puts("IW3_ORIGINAL_GLES3_BUFFER_STORAGE_HOST_SANITIZER_PASS_NOT_FRAME");
}
"""

class OriginalGlesBufferStorage(unittest.TestCase):
    def test_gles3_gpu_storage_registers_original_handles(self):
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
                 str(root / "test.cpp"),
                 str(GFX / "r_android_buffer_storage.cpp"),
                 str(GFX / "r_android_vertex_stream.cpp"),
                 str(GFX / "r_android_indexed_draw.cpp"),
                 "-o", str(binary)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(binary)], capture_output=True, text=True,
                                 env=env, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_GLES3_BUFFER_STORAGE_HOST_SANITIZER_PASS_NOT_FRAME", run.stdout)

if __name__ == "__main__":
    unittest.main()
