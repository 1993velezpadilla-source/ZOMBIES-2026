"""Authentic KisakCOD material vertex-declaration metadata regression.
Not a VAO, shader translation, rendered frame, or playable APK.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "third_party/KisakCOD/src/gfx_d3d"
HARNESS = r'''
#include "r_android_vertex_declaration.h"
#include <cassert>
#include <cstdio>
int main() {
  static_assert(sizeof(IW3AndroidVertexElement)==8);
  IW3AndroidVertexElement layout[]={{0,0,3,0,0,0},{0,16,4,0,10,0},{0,20,1,0,5,0},{1,0,8,0,5,1}};
  assert(!R_AndroidCreateVertexDeclaration(nullptr,4));
  assert(!R_AndroidCreateVertexDeclaration(layout,0));
  assert(!R_AndroidCreateVertexDeclaration(layout,17));
  void *d=R_AndroidCreateVertexDeclaration(layout,4);assert(d);
  assert(!R_AndroidSelectVertexDeclaration((void*)0x123));
  assert(R_AndroidSelectVertexDeclaration(d));
  assert(R_AndroidCurrentVertexDeclaration()==d);
  IW3AndroidVertexElement copy[4]{};size_t n=0;
  assert(!R_AndroidCopyVertexDeclaration(d,copy,3,&n));
  assert(R_AndroidCopyVertexDeclaration(d,copy,4,&n));
  assert(n==4 && copy[3].stream==1 && copy[3].type==8);
  layout[1].usage=0;assert(!R_AndroidCreateVertexDeclaration(layout,4));
  layout[1].usage=10;layout[1].type=17;assert(!R_AndroidCreateVertexDeclaration(layout,4));
  layout[1].type=4;layout[1].stream=2;assert(!R_AndroidCreateVertexDeclaration(layout,4));
  layout[1].stream=0;layout[1].usageIndex=1;assert(!R_AndroidCreateVertexDeclaration(layout,4));
  assert(R_AndroidReleaseVertexDeclaration(d));
  assert(R_AndroidCurrentVertexDeclaration()==nullptr);
  assert(!R_AndroidReleaseVertexDeclaration(d));
  assert(!R_AndroidSelectVertexDeclaration(d));
  d=R_AndroidCreateVertexDeclaration(layout,1);assert(d);
  R_AndroidInvalidateVertexDeclarations();
  assert(!R_AndroidSelectVertexDeclaration(d));
  std::puts("IW3_ORIGINAL_VERTEX_DECL_METADATA_HOST_PASS_NOT_VAO_NOT_FRAME");
}
'''

class OriginalVertexDeclarationMetadata(unittest.TestCase):
    def test_original_material_and_draw_callsites(self):
        material=(GFX/"r_material.cpp").read_text()
        shade=(GFX/"rb_shade.cpp").read_text()
        self.assertIn("R_AndroidCreateVertexDeclaration(", material)
        self.assertIn("R_AndroidSelectVertexDeclaration(", shade)
        self.assertIn("dx.device->CreateVertexDeclaration(elemTable, &decl)", material)
        self.assertIn("device->SetVertexDeclaration(v3)", shade)
        self.assertIn("R_AndroidReleaseVertexDeclaration(", material)

    def test_host_metadata_lifecycle_sanitized(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"test.cpp").write_text(HARNESS)
            binary=root/"test"
            build=subprocess.run([os.environ.get("CXX","g++"),"-std=c++17",
                "-D__ANDROID__","-UNDEBUG","-O1","-g",
                "-fsanitize=address,undefined","-fno-omit-frame-pointer",
                "-I",str(GFX),str(root/"test.cpp"),
                str(GFX/"r_android_vertex_declaration.cpp"),"-o",str(binary)],
                capture_output=True,text=True,timeout=90)
            self.assertEqual(build.returncode,0,build.stdout+build.stderr)
            env=os.environ.copy();env["ASAN_OPTIONS"]="detect_leaks=1"
            run=subprocess.run([str(binary)],capture_output=True,text=True,
                               env=env,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn("IW3_ORIGINAL_VERTEX_DECL_METADATA_HOST_PASS_NOT_VAO_NOT_FRAME",run.stdout)

if __name__=="__main__":
    unittest.main()
