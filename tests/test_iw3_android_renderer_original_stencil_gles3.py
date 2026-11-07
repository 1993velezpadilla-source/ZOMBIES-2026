"""Original IW3 front/back stencil GLES3 bridge: mocked host ASan/UBSan, NOT a game."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "third_party/KisakCOD/src/gfx_d3d"
EGL = "#pragma once\nusing EGLDisplay=void*; using EGLContext=void*;\n#define EGL_NO_DISPLAY ((EGLDisplay)0)\n#define EGL_NO_CONTEXT ((EGLContext)0)\nEGLDisplay eglGetCurrentDisplay(); EGLContext eglGetCurrentContext();\n"
GLES = "#pragma once\nusing GLenum=unsigned int; using GLint=int; using GLuint=unsigned int; using GLboolean=unsigned char;\n#define GL_NO_ERROR 0\n#define GL_FALSE 0\n#define GL_TRUE 1\n#define GL_INVALID_ENUM 0x0500\n#define GL_STENCIL_TEST 0x0B90\n#define GL_FRONT 0x0404\n#define GL_BACK 0x0405\n#define GL_KEEP 0x1E00\n#define GL_ZERO 0\n#define GL_REPLACE 0x1E01\n#define GL_INCR 0x1E02\n#define GL_DECR 0x1E03\n#define GL_INVERT 0x150A\n#define GL_INCR_WRAP 0x8507\n#define GL_DECR_WRAP 0x8508\n#define GL_NEVER 0x0200\n#define GL_LESS 0x0201\n#define GL_EQUAL 0x0202\n#define GL_LEQUAL 0x0203\n#define GL_GREATER 0x0204\n#define GL_NOTEQUAL 0x0205\n#define GL_GEQUAL 0x0206\n#define GL_ALWAYS 0x0207\n#define GL_STENCIL_FAIL 0xb91\n#define GL_STENCIL_PASS_DEPTH_FAIL 0xb92\n#define GL_STENCIL_PASS_DEPTH_PASS 0xb93\n#define GL_STENCIL_FUNC 0xb94\n#define GL_STENCIL_REF 0xb95\n#define GL_STENCIL_VALUE_MASK 0xb96\n#define GL_STENCIL_BACK_FAIL 0xb97\n#define GL_STENCIL_BACK_PASS_DEPTH_FAIL 0xb98\n#define GL_STENCIL_BACK_PASS_DEPTH_PASS 0xb99\n#define GL_STENCIL_BACK_FUNC 0xb9a\n#define GL_STENCIL_BACK_REF 0xb9b\n#define GL_STENCIL_BACK_VALUE_MASK 0xb9c\nGLenum glGetError(); GLboolean glIsEnabled(GLenum); void glGetIntegerv(GLenum,GLint*);\nvoid glEnable(GLenum); void glDisable(GLenum);\nvoid glStencilOpSeparate(GLenum,GLenum,GLenum,GLenum);\nvoid glStencilFuncSeparate(GLenum,GLenum,GLint,GLuint);\n"
HARNESS = "#include <cassert>\n#include <cstdio>\n#include \"r_android_stencil_state.cpp\"\nstruct State {GLint fail=GL_KEEP, zfail=GL_KEEP, pass=GL_KEEP, func=GL_ALWAYS, ref=23, mask=0x5a;};\nstatic State front{}, back{};\nstatic bool context=true, failQuery=false, failMutation=false, enabled=false;\nstatic GLenum errorCode=GL_NO_ERROR;\nstatic int writes=0;\nEGLDisplay eglGetCurrentDisplay(){return context?(void*)1:EGL_NO_DISPLAY;}\nEGLContext eglGetCurrentContext(){return context?(void*)2:EGL_NO_CONTEXT;}\nGLenum glGetError(){auto e=errorCode;errorCode=GL_NO_ERROR;return e;}\nGLboolean glIsEnabled(GLenum e){assert(e==GL_STENCIL_TEST);if(failQuery){errorCode=0x502;return GL_FALSE;}return enabled?GL_TRUE:GL_FALSE;}\nvoid glGetIntegerv(GLenum e,GLint *p){\n  if(failQuery){errorCode=0x502;return;}\n  switch(e){\n  case GL_STENCIL_FAIL:*p=front.fail;break;\n  case GL_STENCIL_PASS_DEPTH_FAIL:*p=front.zfail;break;\n  case GL_STENCIL_PASS_DEPTH_PASS:*p=front.pass;break;\n  case GL_STENCIL_FUNC:*p=front.func;break;\n  case GL_STENCIL_REF:*p=front.ref;break;\n  case GL_STENCIL_VALUE_MASK:*p=front.mask;break;\n  case GL_STENCIL_BACK_FAIL:*p=back.fail;break;\n  case GL_STENCIL_BACK_PASS_DEPTH_FAIL:*p=back.zfail;break;\n  case GL_STENCIL_BACK_PASS_DEPTH_PASS:*p=back.pass;break;\n  case GL_STENCIL_BACK_FUNC:*p=back.func;break;\n  case GL_STENCIL_BACK_REF:*p=back.ref;break;\n  case GL_STENCIL_BACK_VALUE_MASK:*p=back.mask;break;\n  default:assert(false);\n  }\n}\nbool shouldFail(){++writes;if(failMutation){failMutation=false;errorCode=0x502;return true;}return false;}\nvoid glEnable(GLenum e){assert(e==GL_STENCIL_TEST);if(!shouldFail())enabled=true;}\nvoid glDisable(GLenum e){assert(e==GL_STENCIL_TEST);if(!shouldFail())enabled=false;}\nvoid glStencilOpSeparate(GLenum face,GLenum fail,GLenum zfail,GLenum pass){\n  assert(face==GL_FRONT||face==GL_BACK);\n  if(shouldFail())return;\n  State &s=(face==GL_FRONT?front:back);s.fail=fail;s.zfail=zfail;s.pass=pass;\n}\nvoid glStencilFuncSeparate(GLenum face,GLenum fn,GLint ref,GLuint mask){\n  assert(face==GL_FRONT||face==GL_BACK);\n  if(shouldFail())return;\n  State &s=(face==GL_FRONT?front:back);s.func=fn;s.ref=ref;s.mask=mask;\n}\nint main(){\n  static_assert(sizeof(void*)==8,\"LP64 required\");\n  context=false;\n  assert(!R_AndroidGlesEnableStencil(true));\n  assert(!R_AndroidGlesSetStencilOp(false,0,0,0));\n  assert(!R_AndroidGlesSetStencilFunc(false,0));\n  assert(writes==0);\n  context=true;errorCode=0x500;assert(!R_AndroidGlesEnableStencil(true));\n  assert(!R_AndroidGlesSetStencilOp(false,8,0,0));\n  assert(!R_AndroidGlesSetStencilOp(false,0,8,0));\n  assert(!R_AndroidGlesSetStencilOp(false,0,0,8));\n  assert(!R_AndroidGlesSetStencilFunc(false,8));\n  assert(writes==0);\n  failQuery=true;\n  assert(!R_AndroidGlesEnableStencil(true));\n  assert(!R_AndroidGlesSetStencilOp(false,0,1,2));\n  assert(!R_AndroidGlesSetStencilFunc(false,1));\n  failQuery=false;assert(writes==0);\n  assert(R_AndroidGlesEnableStencil(true));assert(enabled);\n  assert(R_AndroidGlesEnableStencil(false));assert(!enabled);\n  assert(R_AndroidGlesSetStencilOp(false,0,1,2));\n  assert(front.pass==GL_KEEP&&front.fail==GL_ZERO&&front.zfail==GL_REPLACE);\n  assert(back.pass==GL_KEEP&&back.fail==GL_KEEP);\n  assert(R_AndroidGlesSetStencilOp(true,6,7,5));\n  assert(back.pass==GL_INCR_WRAP&&back.fail==GL_DECR_WRAP&&back.zfail==GL_INVERT);\n  const GLenum expected[8]={GL_NEVER,GL_LESS,GL_EQUAL,GL_LEQUAL,GL_GREATER,GL_NOTEQUAL,GL_GEQUAL,GL_ALWAYS};\n  for(int i=0;i<8;++i){\n    assert(R_AndroidGlesSetStencilFunc(false,i));assert(front.func==expected[i]);\n    assert(R_AndroidGlesSetStencilFunc(true,i));assert(back.func==expected[i]);\n  }\n  assert(front.ref==23&&front.mask==0x5a&&back.ref==23&&back.mask==0x5a);\n  failMutation=true;assert(!R_AndroidGlesEnableStencil(true));assert(!enabled);\n  failMutation=true;assert(!R_AndroidGlesSetStencilOp(false,4,3,2));\n  assert(front.pass==GL_KEEP&&front.fail==GL_ZERO&&front.zfail==GL_REPLACE);\n  failMutation=true;assert(!R_AndroidGlesSetStencilFunc(true,0));assert(back.func==GL_ALWAYS);\n  std::puts(\"IW3_ORIGINAL_STENCIL_GLES3_ASAN_UBSAN_PASS_NOT_FRAME\");\n}\n"

class OriginalStencilGles3(unittest.TestCase):
    def test_original_iw3_stencil_gles3(self):
        original = (GFX / "r_state.cpp").read_text()
        for name in ("R_AndroidGlesEnableStencil", "R_AndroidGlesSetStencilOp",
                     "R_AndroidGlesSetStencilFunc"):
            self.assertIn(name + "(", original)
        for d3d in ("D3DRS_STENCILENABLE", "D3DRS_STENCILPASS",
                    "D3DRS_CCW_STENCILPASS", "D3DRS_STENCILFUNC"):
            self.assertIn(d3d, original)
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
            self.assertIn("IW3_ORIGINAL_STENCIL_GLES3_ASAN_UBSAN_PASS_NOT_FRAME", run.stdout)

if __name__ == "__main__":
    unittest.main()
