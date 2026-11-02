"""Authentic IW3 R_HW_DisableSampler GLES3 regression; host GL mocked, NOT GAME."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "third_party/KisakCOD/src/gfx_d3d"
EGL = """#pragma once
using EGLContext=void*; using EGLDisplay=void*;
#define EGL_NO_CONTEXT ((EGLContext)0)
#define EGL_NO_DISPLAY ((EGLDisplay)0)
EGLContext eglGetCurrentContext(); EGLDisplay eglGetCurrentDisplay();
"""
GLES = """#pragma once
using GLenum=unsigned int;using GLuint=unsigned int;using GLint=int;
#define GL_NO_ERROR 0
#define GL_TEXTURE0 0x84C0
#define GL_ACTIVE_TEXTURE 0x84E0
#define GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS 0x8B4D
#define GL_TEXTURE_2D 0x0DE1
#define GL_TEXTURE_CUBE_MAP 0x8513
#define GL_TEXTURE_3D 0x806F
#define GL_TEXTURE_BINDING_2D 0x8069
#define GL_TEXTURE_BINDING_CUBE_MAP 0x8514
#define GL_TEXTURE_BINDING_3D 0x806A
GLenum glGetError(); void glGetIntegerv(GLenum, GLint*);
void glActiveTexture(GLenum);void glBindTexture(GLenum,GLuint);
"""
HARNESS = r"""
#include <cassert>
#include <cstdio>
#include "r_android_texture_unbind.cpp"
static bool context=true, queryFail=false, bindFail=false;
static GLenum error=0, active=GL_TEXTURE0+1;
static GLuint bound[16][3] = {};
static int mutations=0, samplerMutations=0;
EGLDisplay eglGetCurrentDisplay(){return context?(void*)1:EGL_NO_DISPLAY;}
EGLContext eglGetCurrentContext(){return context?(void*)2:EGL_NO_CONTEXT;}
GLenum glGetError(){auto result=error;error=0;return result;}
int slot(GLenum t){
  if(t==GL_TEXTURE_2D || t==GL_TEXTURE_BINDING_2D)return 0;
  if(t==GL_TEXTURE_CUBE_MAP || t==GL_TEXTURE_BINDING_CUBE_MAP)return 1;
  if(t==GL_TEXTURE_3D || t==GL_TEXTURE_BINDING_3D)return 2;
  assert(false);return -1;
}
void glGetIntegerv(GLenum p,GLint* v){
  if(queryFail && p==GL_TEXTURE_BINDING_CUBE_MAP){queryFail=false;error=0x502;return;}
  if(p==GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS)*v=16;
  else if(p==GL_ACTIVE_TEXTURE)*v=active;
  else *v=bound[active-GL_TEXTURE0][slot(p)];
}
void glActiveTexture(GLenum t){assert(t>=GL_TEXTURE0 && t<GL_TEXTURE0+16);active=t;}
void glBindTexture(GLenum t,GLuint name){
  ++mutations;
  bound[active-GL_TEXTURE0][slot(t)]=name;
  if(bindFail && t==GL_TEXTURE_CUBE_MAP){bindFail=false;error=0x502;}
}
int main(){
  static_assert(sizeof(void*)==8,"LP64 regression");
  bound[3][0]=11;bound[3][1]=12;bound[3][2]=13;
  bound[1][0]=99;
  context=false;assert(!R_AndroidGlesDisableSamplerTexture(3));context=true;
  assert(!R_AndroidGlesDisableSamplerTexture(16));
  error=0x500;assert(!R_AndroidGlesDisableSamplerTexture(3));
  assert(mutations==0);
  queryFail=true;assert(!R_AndroidGlesDisableSamplerTexture(3));
  assert(mutations==0 && active==GL_TEXTURE0+1);
  bindFail=true;assert(!R_AndroidGlesDisableSamplerTexture(3));
  assert(active==GL_TEXTURE0+1);
  assert(bound[3][0]==11 && bound[3][1]==12 && bound[3][2]==13);
  assert(R_AndroidGlesDisableSamplerTexture(3));
  assert(bound[3][0]==0 && bound[3][1]==0 && bound[3][2]==0);
  assert(bound[1][0]==99 && active==GL_TEXTURE0+1);
  assert(samplerMutations==0);
  std::puts("IW3_ORIGINAL_TEXTURE_UNBIND_GLES3_ASAN_UBSAN_PASS_NOT_FRAME");
}
"""

class TestOriginalTextureUnbindGles3(unittest.TestCase):
    def test_original_iw3_texture_unbind(self):
        original = (GFX / "r_state.cpp").read_text()
        self.assertIn("R_AndroidGlesDisableSamplerTexture(samplerIndex)", original)
        self.assertIn("device->SetTexture(samplerIndex,0)", original)  # Windows retained
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
                str(root / "test.cpp"), "-o", str(binary)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(binary)], capture_output=True, text=True,
                                 env=env, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_TEXTURE_UNBIND_GLES3_ASAN_UBSAN_PASS_NOT_FRAME", run.stdout)

if __name__ == "__main__":
    unittest.main()
