"""Original KisakCOD GPU-fence call sites with actual GLES3 provider code.
Host GL/EGL entry points are mocks: NOT an Android frame or gameplay.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "third_party/KisakCOD/src/gfx_d3d"
EGL = """#pragma once
using EGLDisplay=void*; using EGLContext=void*;
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_NO_CONTEXT ((EGLContext)0)
EGLDisplay eglGetCurrentDisplay(); EGLContext eglGetCurrentContext();
"""
GLES = """#pragma once
#include <cstdint>
using GLenum=unsigned int; using GLbitfield=unsigned int;
using GLuint64=uint64_t; using GLsync=void*;
#define GL_SYNC_GPU_COMMANDS_COMPLETE 0x9117
#define GL_SYNC_FLUSH_COMMANDS_BIT 0x00000001
#define GL_ALREADY_SIGNALED 0x911A
#define GL_TIMEOUT_EXPIRED 0x911B
#define GL_CONDITION_SATISFIED 0x911C
#define GL_WAIT_FAILED 0x911D
GLsync glFenceSync(GLenum, GLbitfield); void glFlush();
GLenum glClientWaitSync(GLsync, GLbitfield, GLuint64); void glDeleteSync(GLsync);
"""
HARNESS = r"""
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#define __cdecl
#define __ANDROID__ 1
#include "r_android_gpu_fence.cpp"
static EGLDisplay display=reinterpret_cast<void*>(0x10);
static EGLContext context=reinterpret_cast<void*>(0x20);
static GLenum waitResult=GL_TIMEOUT_EXPIRED;
static int inserts=0, flushes=0, deletes=0, waits=0;
EGLDisplay eglGetCurrentDisplay(){return display;}
EGLContext eglGetCurrentContext(){return context;}
GLsync glFenceSync(GLenum,GLbitfield){++inserts;return reinterpret_cast<void*>(0x40);}
void glFlush(){++flushes;}
GLenum glClientWaitSync(GLsync s,GLbitfield,GLuint64 t){assert(s==reinterpret_cast<void*>(0x40)&&t<=50000000ULL);++waits;return waitResult;}
void glDeleteSync(GLsync s){assert(s==reinterpret_cast<void*>(0x40));++deletes;}
enum { ERR_FATAL=1 };
void Com_Error(int k,const char *msg,...){assert(k==ERR_FATAL&&msg&&*msg);throw std::runtime_error(msg);}
/* ORIGINAL */
template<typename F>void mustFail(F f){try{f();}catch(const std::runtime_error&){return;}std::abort();}
int main(){
 mustFail([]{(void)RB_IsGpuFenceFinished();});
 mustFail([]{R_InsertGpuFence();});
 assert(R_AndroidGpuFenceBindOriginal(display,context));
 assert(!R_AndroidGpuFenceBindOriginal(display,context));
 assert(RB_IsGpuFenceFinished());
 mustFail([]{(void)RB_IsGpuFinished();});
 R_InsertGpuFence(); assert(inserts==1&&flushes==1);
 assert(!RB_IsGpuFenceFinished());
 mustFail([]{R_InsertGpuFence();});
 waitResult=GL_ALREADY_SIGNALED; assert(RB_IsGpuFinished());
 assert(deletes==1&&RB_IsGpuFenceFinished());
 R_InsertGpuFence(); waitResult=GL_TIMEOUT_EXPIRED;
 mustFail([]{R_FinishGpuFence();}); assert(waits>=6&&deletes==1);
 waitResult=GL_CONDITION_SATISFIED; R_FinishGpuFence(); assert(deletes==2);
 R_InsertGpuFence(); RB_AbandonGpuFence(); assert(deletes==3);
 mustFail([]{RB_AbandonGpuFence();});
 R_InsertGpuFence(); context=reinterpret_cast<void*>(0x99);
 mustFail([]{(void)RB_IsGpuFenceFinished();});
 mustFail([]{RB_AbandonGpuFence();});
 assert(!R_AndroidGpuFenceReleaseOriginal());
 context=reinterpret_cast<void*>(0x20);
 assert(R_AndroidGpuFenceReleaseOriginal()); assert(deletes==4);
 mustFail([]{(void)RB_IsGpuFenceFinished();});
 std::puts("IW3_ORIGINAL_GPU_GLES3_CALLSITES_HOST_SANITIZER_PASS_NOT_GAME");
}
"""

class OriginalGpuGles3IntegrationTests(unittest.TestCase):
    def test_original_callsites_with_gles3_provider_under_sanitizers(self):
        query=(GFX/"r_setstate_d3d.cpp").read_text(encoding="utf-8")
        backend=(GFX/"rb_backend.cpp").read_text(encoding="utf-8")
        funcs=[(query,"bool __cdecl RB_IsGpuFinished()"),
               (query,"bool __cdecl RB_IsGpuFenceFinished()"),
               (backend,"void __cdecl R_FinishGpuFence()"),
               (backend,"void __cdecl R_InsertGpuFence()"),
               (backend,"void RB_AbandonGpuFence()")]
        originals="\n".join(function_source(s,sig) for s,sig in funcs)
        for name in ("R_AndroidGpuFenceOriginalPoll","R_AndroidGpuFenceOriginalWait",
                     "R_AndroidGpuFenceOriginalInsert","R_AndroidGpuFenceOriginalAbandon"):
            self.assertIn(name,originals)
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            (tmp/"EGL").mkdir();(tmp/"GLES3").mkdir()
            (tmp/"EGL/egl.h").write_text(EGL,encoding="utf-8")
            (tmp/"GLES3/gl3.h").write_text(GLES,encoding="utf-8")
            source=tmp/"original_gpu_sync.cpp"
            source.write_text(HARNESS.replace("/* ORIGINAL */",originals),encoding="utf-8")
            exe=tmp/"original_gpu_sync"
            built=subprocess.run([os.environ.get("CXX","g++"),"-std=c++20","-O1","-g",
              "-fsanitize=address,undefined","-fno-omit-frame-pointer","-pthread",
              "-I",str(tmp),"-I",str(GFX),str(source),"-o",str(exe)],
              capture_output=True,text=True,timeout=90)
            self.assertEqual(built.returncode,0,built.stdout+built.stderr)
            env=os.environ.copy();env["ASAN_OPTIONS"]="detect_leaks=1"
            run=subprocess.run([str(exe)],capture_output=True,text=True,env=env,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn("IW3_ORIGINAL_GPU_GLES3_CALLSITES_HOST_SANITIZER_PASS_NOT_GAME",run.stdout)

if __name__=="__main__": unittest.main()
