"""Original KisakCOD r_buffers Android identity/lock lifecycle (mocked EGL/GLES).
No rendered frame, real map, Android runtime, or playable APK is implied.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_iw3_android_renderer_original_buffer_storage_gles3 import EGL, GLES, HARNESS, GFX

MAIN = r"""
#include "r_android_buffer_handles.h"
int main() {
    static_assert(sizeof(void*)==8, "LP64 handle identity");
    assert(!R_AndroidCreateBufferHandle(false, 0, false));
    assert(!R_AndroidCreateBufferHandle(true, 31, false));
    void *vb = R_AndroidCreateBufferHandle(false, 64, false);
    assert(vb && objects.size()==1 && arrayBound==77);
    assert(!R_AndroidUnlockBufferHandle(vb));
    auto *v = static_cast<unsigned char *>(R_AndroidLockBufferHandle(vb,0,0,0));
    assert(v && !R_AndroidLockBufferHandle(vb,0,4,0));
    v[0]=0x31; v[63]=0x72;
    assert(R_AndroidUnlockBufferHandle(vb));
    assert(!R_AndroidUnlockBufferHandle(vb));
    unsigned int vid=0;std::size_t off=0,stride=0;
    assert(R_AndroidGlesChangeStreamSource(0,vb,0,16));
    assert(R_AndroidGlesGetStreamSource(0,&vid,&off,&stride));
    assert(objects.at(vid)[0]==0x31 && objects.at(vid)[63]==0x72);
    assert(!R_AndroidLockBufferHandle(vb,0,4,0x2000));
    assert(!R_AndroidLockBufferHandle(vb,0,4,0x1000));
    assert(!R_AndroidLockBufferHandle(vb,0,4,0x10));
    void *ib=R_AndroidCreateBufferHandle(true,32,true);
    assert(ib && elementBound==88 && objects.size()==2);
    assert(!R_AndroidLockBufferHandle(ib,1,4,0));
    assert(!R_AndroidLockBufferHandle(ib,2,3,0));
    auto *idx=static_cast<unsigned char *>(R_AndroidLockBufferHandle(ib,2,4,0x1000));
    assert(idx);
    idx[0]=5;idx[1]=6;idx[2]=7;idx[3]=8;
    assert(R_AndroidUnlockBufferHandle(ib));
    assert(R_AndroidGlesBindIndexBuffer(ib));
    const auto iid=elementBound;
    assert(objects.at(iid)[2]==5 && objects.at(iid)[5]==8);
    auto *again=static_cast<unsigned char *>(R_AndroidLockBufferHandle(ib,0,4,0x2000));
    assert(again);again[0]=9;
    assert(!R_AndroidReleaseBufferHandle(ib)); // no release while locked
    failUpdate=true;
    assert(!R_AndroidUnlockBufferHandle(ib));
    assert(!R_AndroidLockBufferHandle(ib,0,4,0));
    failUpdate=false;
    assert(R_AndroidUnlockBufferHandle(ib));
    assert(objects.at(iid)[0]==9);
    context=false;
    assert(!R_AndroidReleaseBufferHandle(vb));
    context=true;
    assert(R_AndroidReleaseBufferHandle(vb));
    assert(!R_AndroidGlesGetStreamSource(0,&vid,&off,&stride));
    assert(!R_AndroidReleaseBufferHandle(vb));
    assert(R_AndroidReleaseBufferHandle(ib));
    assert(objects.empty());
    assert(!R_AndroidGlesBindIndexBuffer(ib));
    R_AndroidInvalidateBufferHandles();
    R_AndroidGlesInvalidateBufferStorage();
    R_AndroidGlesInvalidateVertexStreams();
    R_AndroidGlesInvalidateIndexBuffers();
    std::puts("IW3_ORIGINAL_BUFFER_HANDLE_LOCK_HOST_SANITIZER_PASS_NOT_FRAME");
}
"""

class OriginalBufferHandleLifecycle(unittest.TestCase):
    def test_original_r_buffers_callsites_android_split(self):
        source=(GFX / "r_buffers.cpp").read_text()
        self.assertIn('#include "r_android_buffer_handles.h"',source)
        for name in ("R_AllocStaticVertexBuffer", "R_AllocDynamicVertexBuffer",
                     "R_AllocStaticIndexBuffer", "R_AllocDynamicIndexBuffer",
                     "R_LockVertexBuffer", "R_LockIndexBuffer",
                     "R_FinishStaticVertexBuffer", "R_FinishStaticIndexBuffer",
                     "R_DestroyDynamicBuffers"):
            self.assertIn(name,source)
        self.assertGreaterEqual(source.count("R_AndroidCreateBufferHandle("),4)
        self.assertGreaterEqual(source.count("R_AndroidUnlockBufferHandle("),4)
        self.assertIn("dx.device->CreateVertexBuffer",source) # Windows preserved

    def test_original_handle_staging_and_real_gles3_storage(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"EGL").mkdir();(root/"GLES3").mkdir()
            (root/"EGL/egl.h").write_text(EGL)
            (root/"GLES3/gl3.h").write_text(GLES)
            (root/"test.cpp").write_text(HARNESS.split("int main(){",1)[0]+MAIN)
            binary=root/"test"
            build=subprocess.run(
                [os.environ.get("CXX","g++"),"-std=c++17","-D__ANDROID__",
                 "-O1","-g","-UNDEBUG","-fsanitize=address,undefined",
                 "-fno-omit-frame-pointer","-I",str(root),"-I",str(GFX),
                 str(root/"test.cpp"),str(GFX/"r_android_buffer_handles.cpp"),
                 str(GFX/"r_android_buffer_storage.cpp"),
                 str(GFX/"r_android_vertex_stream.cpp"),
                 str(GFX/"r_android_indexed_draw.cpp"),
                 "-o",str(binary)],capture_output=True,text=True,timeout=90)
            self.assertEqual(build.returncode,0,build.stdout+build.stderr)
            env=os.environ.copy();env["ASAN_OPTIONS"]="detect_leaks=1"
            run=subprocess.run([str(binary)],capture_output=True,text=True,
                               env=env,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn("IW3_ORIGINAL_BUFFER_HANDLE_LOCK_HOST_SANITIZER_PASS_NOT_FRAME",run.stdout)

if __name__=="__main__":
    unittest.main()
