"""Run genuine KisakCOD Android GLES3 GLsync provider under host ASan/UBSan.

The GL/EGL entry points in this test are mocks; an ARM64 NDK compile is a
separate CI gate. Neither gate demonstrates a rendered frame or gameplay.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "third_party/KisakCOD/src/gfx_d3d"
SOURCE = GFX / "r_android_gpu_fence.cpp"

EGL = r"""
#pragma once
using EGLDisplay = void*;
using EGLContext = void*;
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_NO_CONTEXT ((EGLContext)0)
EGLDisplay eglGetCurrentDisplay();
EGLContext eglGetCurrentContext();
"""
GLES = r"""
#pragma once
#include <cstdint>
using GLenum = unsigned int;
using GLbitfield = unsigned int;
using GLuint64 = uint64_t;
using GLsync = void*;
#define GL_SYNC_GPU_COMMANDS_COMPLETE 0x9117
#define GL_SYNC_FLUSH_COMMANDS_BIT 0x00000001
#define GL_ALREADY_SIGNALED 0x911A
#define GL_TIMEOUT_EXPIRED 0x911B
#define GL_CONDITION_SATISFIED 0x911C
#define GL_WAIT_FAILED 0x911D
GLsync glFenceSync(GLenum, GLbitfield);
void glFlush();
GLenum glClientWaitSync(GLsync, GLbitfield, GLuint64);
void glDeleteSync(GLsync);
"""
HARNESS = r"""
#include <cassert>
#include <cstdio>
#include <thread>
#define __ANDROID__ 1
#include "r_android_gpu_fence.cpp"
static EGLDisplay display = reinterpret_cast<void*>(0x10);
static EGLContext context = reinterpret_cast<void*>(0x20);
static GLenum nextWait = GL_TIMEOUT_EXPIRED;
static bool failInsert = false;
static int inserts = 0, flushes = 0, deletes = 0, waits = 0;
static GLuint64 lastTimeout = 0;
static GLbitfield lastFlags = 0;
EGLDisplay eglGetCurrentDisplay() { return display; }
EGLContext eglGetCurrentContext() { return context; }
GLsync glFenceSync(GLenum condition, GLbitfield flags) {
    assert(condition == GL_SYNC_GPU_COMMANDS_COMPLETE && flags == 0);
    ++inserts;
    return failInsert ? nullptr : reinterpret_cast<void*>(0x40);
}
void glFlush() { ++flushes; }
GLenum glClientWaitSync(GLsync sync, GLbitfield flags, GLuint64 timeout) {
    assert(sync == reinterpret_cast<void*>(0x40));
    ++waits; lastFlags = flags; lastTimeout = timeout;
    return nextWait;
}
void glDeleteSync(GLsync sync) {
    assert(sync == reinterpret_cast<void*>(0x40)); ++deletes;
}
int main() {
    static_assert(sizeof(void*) == 8, "LP64 test required");
    IW3AndroidGpuFence fence;
    assert(R_AndroidGpuFencePoll(&fence) == IW3AndroidGpuFenceResult::Invalid);
    assert(!R_AndroidGpuFenceBind(&fence, nullptr, context));
    assert(!R_AndroidGpuFenceBind(&fence, display, nullptr));
    assert(!R_AndroidGpuFenceBind(nullptr, display, context));
    assert(R_AndroidGpuFenceBind(&fence, display, context));
    assert(!R_AndroidGpuFenceBind(&fence, display, context));
    assert(R_AndroidGpuFencePoll(&fence) == IW3AndroidGpuFenceResult::Idle);
    assert(R_AndroidGpuFenceInsert(&fence));
    assert(inserts == 1 && flushes == 1);
    assert(!R_AndroidGpuFenceInsert(&fence)); // no overwrite/leak
    assert(R_AndroidGpuFencePoll(&fence) == IW3AndroidGpuFenceResult::Pending);
    assert(lastTimeout == 0 && lastFlags == 0);
    assert(R_AndroidGpuFenceWait(&fence, UINT64_MAX) == IW3AndroidGpuFenceResult::Pending);
    assert(lastTimeout == 50000000ULL && lastFlags == GL_SYNC_FLUSH_COMMANDS_BIT);
    nextWait = GL_CONDITION_SATISFIED;
    assert(R_AndroidGpuFencePoll(&fence) == IW3AndroidGpuFenceResult::Complete);
    assert(deletes == 1 && fence.sync == nullptr);
    assert(R_AndroidGpuFencePoll(&fence) == IW3AndroidGpuFenceResult::Idle);

    failInsert = true;
    assert(!R_AndroidGpuFenceInsert(&fence));
    assert(!fence.sync && flushes == 1);
    failInsert = false;
    assert(R_AndroidGpuFenceInsert(&fence));
    nextWait = GL_WAIT_FAILED;
    assert(R_AndroidGpuFenceWait(&fence, 1000) == IW3AndroidGpuFenceResult::Invalid);
    assert(fence.sync != nullptr && deletes == 1); // do not fabricate completion
    context = reinterpret_cast<void*>(0x99);
    assert(R_AndroidGpuFencePoll(&fence) == IW3AndroidGpuFenceResult::Invalid);
    assert(!R_AndroidGpuFenceAbandon(&fence));
    assert(!R_AndroidGpuFenceRelease(&fence)); // cannot delete from wrong context
    context = reinterpret_cast<void*>(0x20);
    bool foreignPoll = false, foreignRelease = false;
    std::thread foreign([&]() {
        foreignPoll = R_AndroidGpuFencePoll(&fence) == IW3AndroidGpuFenceResult::Invalid;
        foreignRelease = !R_AndroidGpuFenceRelease(&fence);
    });
    foreign.join();
    assert(foreignPoll && foreignRelease);
    assert(R_AndroidGpuFenceAbandon(&fence));
    assert(deletes == 2);
    assert(R_AndroidGpuFenceRelease(&fence));
    assert(!fence.ownerThreadValid && fence.sync == nullptr);
    assert(R_AndroidGpuFenceBind(&fence, display, context));
    nextWait = GL_ALREADY_SIGNALED;
    assert(R_AndroidGpuFenceInsert(&fence));
    assert(R_AndroidGpuFencePoll(&fence) == IW3AndroidGpuFenceResult::Complete);
    assert(deletes == 3);
    assert(R_AndroidGpuFenceRelease(&fence));
    std::puts("IW3_GLES3_GPU_FENCE_HOST_SANITIZER_PASS_NOT_GAME");
}
"""


class GenuineAndroidGpuFenceTests(unittest.TestCase):
    def test_gles3_sync_lifecycle_with_sanitizers(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("glFenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE, 0)", source)
        self.assertIn("glClientWaitSync", source)
        self.assertIn("glDeleteSync", source)
        self.assertIn("eglGetCurrentContext()", source)
        self.assertNotIn("return true; // pretend", source)
        with tempfile.TemporaryDirectory() as tmp:
            inc = Path(tmp)
            (inc / "EGL").mkdir()
            (inc / "GLES3").mkdir()
            (inc / "EGL/egl.h").write_text(EGL, encoding="utf-8")
            (inc / "GLES3/gl3.h").write_text(GLES, encoding="utf-8")
            source_file = inc / "gpu_fence_harness.cpp"
            exe = inc / "gpu_fence_harness"
            source_file.write_text(HARNESS, encoding="utf-8")
            cmd = [os.environ.get("CXX", "g++"), "-std=c++20", "-O1", "-g",
                   "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                   "-pthread", "-I", str(inc), "-I", str(GFX),
                   str(source_file), "-o", str(exe)]
            built = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            ran = subprocess.run([str(exe)], capture_output=True, text=True,
                                 env=env, timeout=30)
            self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
            self.assertIn("IW3_GLES3_GPU_FENCE_HOST_SANITIZER_PASS_NOT_GAME", ran.stdout)


if __name__ == "__main__":
    unittest.main()
