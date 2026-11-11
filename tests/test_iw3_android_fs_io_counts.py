"""Host sanitizer regression executing verbatim original KisakCOD FS_Read/FS_Write.

External I/O providers are test-only. This is NOT an Android game runtime proof.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/universal/com_files.cpp"
READ = "uint32_t __cdecl FS_Read(uint8_t *buffer, uint32_t len, int h)"
WRITE = "uint32_t __cdecl FS_Write(const char *buffer, uint32_t len, int h)"


class OriginalFsIoCountTests(unittest.TestCase):
    def test_signed_errors_and_overreported_io_cannot_wrap(self):
        source = SOURCE.read_text(encoding="utf-8")
        read_body = function_source(source, READ)
        write_body = function_source(source, WRITE)
        self.assertIn("zipRead < 0", read_body)
        self.assertIn("read < 0", read_body)
        self.assertIn("static_cast<uint32_t>(read) > remaining", read_body)
        self.assertIn("written < 0", write_body)
        self.assertIn("static_cast<uint32_t>(written) > remaining", write_body)

        fixture = r"""
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <initializer_list>
#include <vector>
#define __cdecl
constexpr int ERR_FATAL = 1;
struct Handle {
    bool zipFile = false;
    struct { struct { void *z = nullptr; } file; } handleFiles;
    bool handleSync = false;
};
Handle fsh[65];
static std::vector<int> reads, writes;
static size_t ri = 0, wi = 0;
static int zip_result = 0, errors = 0, read_calls = 0, write_calls = 0;
static FILE *disk = nullptr;
void FS_CheckFileSystemStarted() {}
FILE *FS_FileForHandle(int h) { assert(h > 0 && h < 65); return disk; }
int unzReadCurrentFile(void *, void *buffer, unsigned len) {
    if (zip_result > 0 && static_cast<unsigned>(zip_result) <= len)
        std::memset(buffer, 'Z', static_cast<size_t>(zip_result));
    return zip_result;
}
int FS_FileRead(void *buffer, unsigned len, FILE *) {
    ++read_calls;
    assert(ri < reads.size());
    int result = reads[ri++];
    if (result > 0 && static_cast<unsigned>(result) <= len)
        std::memset(buffer, 'R', static_cast<size_t>(result));
    return result;
}
int FS_FileWrite(const void *, unsigned, FILE *) {
    ++write_calls;
    assert(wi < writes.size());
    return writes[wi++];
}
void Com_Error(int, const char *, ...) { ++errors; }
void reset() {
    fsh[7] = Handle{};
    fsh[50] = Handle{};
    reads.clear(); writes.clear();
    ri = wi = 0; zip_result = errors = read_calls = write_calls = 0;
}
/* ORIGINAL_READ */
/* ORIGINAL_WRITE */
int main() {
    disk = std::tmpfile();
    assert(disk);
    uint8_t buffer[16] = {};
    reset(); reads = {2, 2};
    assert(FS_Read(buffer, 4, 7) == 4);
    assert(read_calls == 2 && buffer[3] == 'R');

    reset(); reads = {0, 2, 2};
    assert(FS_Read(buffer, 4, 7) == 4 && read_calls == 3);
    reset(); reads = {0, 0};
    assert(FS_Read(buffer, 4, 7) == 0 && read_calls == 2);

    reset(); reads = {-1};
    assert(FS_Read(buffer, 4, 7) == UINT32_MAX);
    assert(errors == 1 && read_calls == 1);
    reset(); reads = {-1};
    assert(FS_Read(buffer, 4, 50) == UINT32_MAX && errors == 0);
    reset(); reads = {5};
    assert(FS_Read(buffer, 4, 7) == UINT32_MAX && errors == 1);

    reset(); fsh[7].zipFile = true; zip_result = -3;
    assert(FS_Read(buffer, 4, 7) == UINT32_MAX && errors == 0);
    reset(); fsh[7].zipFile = true; zip_result = 5;
    assert(FS_Read(buffer, 4, 7) == UINT32_MAX);
    reset(); fsh[7].zipFile = true; zip_result = 3;
    assert(FS_Read(buffer, 4, 7) == 3 && buffer[2] == 'Z');
    reset(); assert(FS_Read(buffer, 0, 7) == 0 && read_calls == 0);
    reset(); assert(FS_Read(buffer, 4, 0) == 0 && read_calls == 0);

    reset(); writes = {2, 2};
    assert(FS_Write("ABCD", 4, 7) == 4 && write_calls == 2);
    reset(); writes = {0, 2, 2};
    assert(FS_Write("ABCD", 4, 7) == 4 && write_calls == 3);
    reset(); writes = {0, 0};
    assert(FS_Write("ABCD", 4, 7) == 0 && write_calls == 2);
    reset(); writes = {-1};
    assert(FS_Write("ABCD", 4, 7) == 0 && write_calls == 1);
    reset(); writes = {5};
    assert(FS_Write("ABCD", 4, 7) == 0 && write_calls == 1);
    reset(); assert(FS_Write("ABCD", 0, 7) == 0 && write_calls == 0);
    reset(); assert(FS_Write("ABCD", 4, 0) == 0 && write_calls == 0);
    std::fclose(disk);
    std::puts("IW3_ORIGINAL_FS_IO_COUNTS_PASS");
}
"""
        fixture = fixture.replace("/* ORIGINAL_READ */", read_body)
        fixture = fixture.replace("/* ORIGINAL_WRITE */", write_body)
        with tempfile.TemporaryDirectory() as temp:
            cpp = Path(temp) / "original_fs_io.cpp"
            exe = Path(temp) / "original_fs_io"
            cpp.write_text(fixture, encoding="utf-8")
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(exe)], capture_output=True, text=True,
                                 timeout=30, env=env)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_FS_IO_COUNTS_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
