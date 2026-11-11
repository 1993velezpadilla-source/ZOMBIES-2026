"""Host ASan/UBSan tests for genuine IW3 GLES3 sampler-object bridge; NOT a game."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "third_party/KisakCOD/src/gfx_d3d"
EGL = """#pragma once
using EGLContext=void*; using EGLDisplay=void*;
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_NO_CONTEXT ((EGLContext)0)
EGLContext eglGetCurrentContext(); EGLDisplay eglGetCurrentDisplay();
"""
GLES = """#pragma once
using GLenum=unsigned int; using GLuint=unsigned int;
using GLint=int; using GLfloat=float; using GLsizei=int;
using GLubyte=unsigned char;
#define GL_NO_ERROR 0
#define GL_TEXTURE0 0x84C0
#define GL_ACTIVE_TEXTURE 0x84E0
#define GL_SAMPLER_BINDING 0x8919
#define GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS 0x8B4D
#define GL_NUM_EXTENSIONS 0x821D
#define GL_EXTENSIONS 0x1F03
#define GL_TEXTURE_MIN_FILTER 0x2801
#define GL_TEXTURE_MAG_FILTER 0x2800
#define GL_TEXTURE_WRAP_S 0x2802
#define GL_TEXTURE_WRAP_T 0x2803
#define GL_TEXTURE_WRAP_R 0x8072
#define GL_REPEAT 0x2901
#define GL_MIRRORED_REPEAT 0x8370
#define GL_CLAMP_TO_EDGE 0x812F
#define GL_LINEAR 0x2601
#define GL_NEAREST 0x2600
#define GL_LINEAR_MIPMAP_NEAREST 0x2701
#define GL_NEAREST_MIPMAP_NEAREST 0x2700
#define GL_LINEAR_MIPMAP_LINEAR 0x2703
#define GL_NEAREST_MIPMAP_LINEAR 0x2702
GLenum glGetError(); void glGetIntegerv(GLenum, GLint*);
void glGetFloatv(GLenum, GLfloat*); const GLubyte* glGetStringi(GLenum, GLuint);
void glActiveTexture(GLenum); void glGenSamplers(GLsizei, GLuint*);
void glSamplerParameteri(GLuint, GLenum, GLint);
void glSamplerParameterf(GLuint, GLenum, GLfloat);
void glBindSampler(GLuint, GLuint); void glDeleteSamplers(GLsizei, const GLuint*);
"""
HARNESS = r"""
#include <cassert>
#include <map>
#include <cstdio>
#include "r_android_sampler_state.cpp"
static bool hasContext=true, injectFailure=false;
static GLenum err=0, active=GL_TEXTURE0;
static GLuint nextName=10, bound[16]={};
static int deleted=0;
static std::map<GLuint,std::map<GLenum,GLint>> params;
EGLDisplay eglGetCurrentDisplay(){return hasContext ? (void*)1 : EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return hasContext ? (void*)2 : EGL_NO_CONTEXT;}
GLenum glGetError(){GLenum e=err;err=0;return e;}
void glGetIntegerv(GLenum p, GLint* v){
  if(p==GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS)*v=16;
  else if(p==GL_ACTIVE_TEXTURE)*v=active;
  else if(p==GL_SAMPLER_BINDING)*v=bound[active-GL_TEXTURE0];
  else if(p==GL_NUM_EXTENSIONS)*v=0;
  else err=0x500;
}
void glGetFloatv(GLenum, GLfloat* v){*v=1;}
const GLubyte* glGetStringi(GLenum, GLuint){return nullptr;}
void glActiveTexture(GLenum t){active=t;}
void glGenSamplers(GLsizei n, GLuint* p){assert(n==1);*p=nextName++;}
void glSamplerParameteri(GLuint s, GLenum p, GLint v){
  params[s][p]=v;
  if(injectFailure && p==GL_TEXTURE_WRAP_T){err=0x500;injectFailure=false;}
}
void glSamplerParameterf(GLuint, GLenum, GLfloat){}
void glBindSampler(GLuint unit, GLuint name){bound[unit]=name;}
void glDeleteSamplers(GLsizei n, const GLuint*){assert(n==1);++deleted;}
int main(){
  uint32_t applied=0;
  const uint32_t state=(1u<<24)|(1u<<22)|(1u<<20)|(2u<<16)|(2u<<12)|(2u<<8)|1u;
  assert(R_AndroidGlesSetSamplerState(3,state,0,&applied));
  assert(applied==(state&~255u));
  assert(active==GL_TEXTURE0);
  const GLuint first=bound[3];
  assert(first!=0 && params[first][GL_TEXTURE_MIN_FILTER]==GL_LINEAR_MIPMAP_LINEAR);
  assert(params[first][GL_TEXTURE_MAG_FILTER]==GL_LINEAR);
  assert(params[first][GL_TEXTURE_WRAP_R]==GL_REPEAT);
  // Reject invalid D3D9 addressing and unsupported anisotropy without touching binding.
  assert(!R_AndroidGlesSetSamplerState(3,(state&~(3u<<20))|(0u<<20),state,&applied));
  assert(!R_AndroidGlesSetSamplerState(3,(state&~255u)|4u,state,&applied));
  assert(bound[3]==first);
  assert(!R_AndroidGlesSetSamplerState(16,state,state,&applied));
  injectFailure=true;
  assert(!R_AndroidGlesSetSamplerState(3,state,state,&applied));
  assert(bound[3]==first);
  assert(deleted==1);
  assert(R_AndroidGlesSetSamplerState(3,state,state,&applied));
  assert(bound[3]!=first && deleted==2);
  hasContext=false;
  assert(!R_AndroidGlesSetSamplerState(3,state,state,&applied));
  hasContext=true;
  R_AndroidGlesReleaseSamplerStates();
  assert(deleted==3);
  puts("IW3_ORIGINAL_SAMPLER_GLES3_ASAN_UBSAN_PASS_NOT_FRAME");
}
"""
class TestOriginalSamplerGles3(unittest.TestCase):
    def test_sampler_state_provider(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "EGL").mkdir()
            (root / "GLES3").mkdir()
            (root / "EGL/egl.h").write_text(EGL)
            (root / "GLES3/gl3.h").write_text(GLES)
            (root / "test.cpp").write_text(HARNESS)
            binary = root / "test"
            build = subprocess.run([
                os.environ.get("CXX", "g++"), "-std=c++17", "-D__ANDROID__",
                "-O1", "-g", "-UNDEBUG", "-fsanitize=address,undefined",
                "-fno-omit-frame-pointer", "-I", str(root), "-I", str(GFX),
                str(root / "test.cpp"), "-o", str(binary)
            ], capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(binary)], capture_output=True, text=True,
                                 env=env, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_SAMPLER_GLES3_ASAN_UBSAN_PASS_NOT_FRAME", run.stdout)

if __name__ == "__main__":
    unittest.main()
