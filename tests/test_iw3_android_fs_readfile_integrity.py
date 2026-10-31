"""Execute the authentic KisakCOD FS_ReadFile body against short/corrupt reads.

This is a host-only original-engine regression, NOT Android runtime/gameplay.
The filesystem/Hunk external services are isolated test providers; the body
under test is extracted verbatim from com_files.cpp.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/universal/com_files.cpp"
SIGNATURE = "int __cdecl FS_ReadFile(const char *qpath, void **buffer)"


class OriginalFsReadFileIntegrityTests(unittest.TestCase):
    def test_original_readfile_rejects_corrupt_lengths_and_short_reads(self):
        body = function_source(SOURCE.read_text(encoding="utf-8"), SIGNATURE)
        self.assertIn("FS_Read(buf, len, h)", body)
        self.assertIn("FS_FreeMem((char *)buf);", body)
        self.assertIn("len == INT_MAX", body)
        self.assertIn("--fs_loadStack;", body)

        fixture = r"""
#include <algorithm>
#include <cassert>
#include <climits>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#define __cdecl
constexpr int ERR_FATAL = 1;
static int fs_loadStack = 0;
static int next_handle = 7, next_len = 4;
static uint32_t next_read = 4;
static bool fail_alloc = false;
static int opens = 0, reads = 0, closes = 0, allocs = 0, frees = 0, errors = 0;

static void reset() {
    fs_loadStack = 0;
    next_handle = 7; next_len = 4; next_read = 4; fail_alloc = false;
    opens = reads = closes = allocs = frees = errors = 0;
}
void FS_CheckFileSystemStarted() {}
void Com_Error(int, const char*, ...) { ++errors; }
uint32_t FS_FOpenFileRead(const char*, int* h) {
    ++opens; *h = next_handle; return static_cast<uint32_t>(next_len);
}
uint32_t FS_Read(uint8_t* p, uint32_t n, int) {
    ++reads;
    if (next_read <= n) std::memset(p, 'A', next_read);
    return next_read;
}
void FS_FCloseFile(int h) { assert(h == 7); ++closes; }
uint32_t* FS_AllocMem(int n) {
    ++allocs;
    return fail_alloc ? nullptr : static_cast<uint32_t*>(std::malloc(n));
}
void FS_FreeMem(char* p) { assert(p); ++frees; std::free(p); }
/* ORIGINAL_READFILE */
int main() {
    reset();
    void* out = reinterpret_cast<void*>(1);
    assert(FS_ReadFile("main/iw_00.iwd", &out) == 4);
    assert(out && std::memcmp(out, "AAAA", 4) == 0);
    assert(static_cast<char*>(out)[4] == 0);
    assert(opens == 1 && reads == 1 && closes == 1 && fs_loadStack == 1);
    FS_FreeMem(static_cast<char*>(out)); --fs_loadStack;
    assert(frees == 1 && fs_loadStack == 0);

    reset();
    assert(FS_ReadFile("main/iw_00.iwd", nullptr) == 4);
    assert(opens == 1 && reads == 0 && allocs == 0 && closes == 1);

    reset(); next_read = 2; out = reinterpret_cast<void*>(1);
    assert(FS_ReadFile("truncated.map", &out) == -1);
    assert(out == nullptr && opens == 1 && reads == 1 && closes == 1);
    assert(allocs == 1 && frees == 1 && fs_loadStack == 0);

    reset(); next_read = UINT32_MAX; out = reinterpret_cast<void*>(1);
    assert(FS_ReadFile("read-error.map", &out) == -1);
    assert(out == nullptr && frees == 1 && fs_loadStack == 0 && closes == 1);

    reset(); next_len = INT_MAX; out = reinterpret_cast<void*>(1);
    assert(FS_ReadFile("overflow.map", &out) == -1);
    assert(out == nullptr && allocs == 0 && closes == 1);

    reset(); next_len = -1; out = reinterpret_cast<void*>(1);
    assert(FS_ReadFile("invalid.map", &out) == -1);
    assert(out == nullptr && allocs == 0 && closes == 1);

    reset(); next_handle = 0; out = reinterpret_cast<void*>(1);
    assert(FS_ReadFile("missing.map", &out) == -1);
    assert(out == nullptr && allocs == 0 && closes == 0);

    reset(); fail_alloc = true; out = reinterpret_cast<void*>(1);
    assert(FS_ReadFile("oom.map", &out) == -1);
    assert(out == nullptr && allocs == 1 && closes == 1 && fs_loadStack == 0);

    reset(); next_len = 0; next_read = 0;
    assert(FS_ReadFile("empty.cfg", &out) == 0);
    assert(out && static_cast<char*>(out)[0] == 0);
    assert(reads == 0 && closes == 1 && fs_loadStack == 1);
    FS_FreeMem(static_cast<char*>(out)); --fs_loadStack;

    reset(); out = reinterpret_cast<void*>(1);
    assert(FS_ReadFile(nullptr, &out) == -1);
    assert(out == nullptr && errors == 1 && opens == 0);
    std::puts("IW3_ORIGINAL_FS_READFILE_INTEGRITY_PASS");
}
"""
        fixture = fixture.replace("/* ORIGINAL_READFILE */", body)
        with tempfile.TemporaryDirectory() as tmp:
            cpp = Path(tmp) / "original_fs_readfile.cpp"
            exe = Path(tmp) / "original_fs_readfile"
            cpp.write_text(fixture, encoding="utf-8")
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(exe)], capture_output=True, text=True,
                                 timeout=30, env=env)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_FS_READFILE_INTEGRITY_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
