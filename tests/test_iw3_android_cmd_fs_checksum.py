"""Run the authentic IW3 FS_ReferencedIwdPureChecksums body across repeated calls.

This is a host-level filesystem regression, not Android map loading or gameplay.
"""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/universal/com_files.cpp"


class OriginalIwdChecksumTests(unittest.TestCase):
    def test_repeated_checksum_queries_preserve_terminated_prefix(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("char info6[8192];")
        end = source.index("\n}\n", source.index("FS_ReferencedIwdPureChecksums()", start)) + 3
        original = source[start:end]
        self.assertIn("info6[0] = '@';", original)
        self.assertIn("info6[1] = ' ';", original)
        self.assertIn("info6[2] = '\\0';", original)
        self.assertNotIn("info6[strlen(info6)] = '@';", original)

        harness = r"""
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <string>
#define __cdecl
struct iwd_t { bool referenced; int pure_checksum; };
struct searchpath_s { searchpath_s *next; iwd_t *iwd; bool bLocalized; };
int fs_checksumFeed = 17;
int fs_fakeChkSum = 0;
searchpath_s *fs_searchpaths = nullptr;
char *va(const char *fmt, ...) {
    static char output[128];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(output, sizeof(output), fmt, ap);
    va_end(ap);
    return output;
}
void I_strncat(char *dest, int capacity, const char *src) {
    const size_t used = strlen(dest);
    assert(used < static_cast<size_t>(capacity));
    strncat(dest, src, static_cast<size_t>(capacity) - used - 1);
}
__IW3_ORIGINAL__
int main() {
    for (int n = 0; n < 4; ++n)
        assert(std::string(FS_ReferencedIwdPureChecksums()) == "@ 17 ");
    iwd_t iwd{true, 5};
    searchpath_s search{nullptr, &iwd, false};
    fs_searchpaths = &search;
    for (int n = 0; n < 4; ++n)
        assert(std::string(FS_ReferencedIwdPureChecksums()) == "@ 5 20 ");
}
""".replace("__IW3_ORIGINAL__", original)
        with tempfile.TemporaryDirectory() as temp:
            cpp = Path(temp) / "iw3_checksum.cpp"
            exe = Path(temp) / "iw3_checksum"
            cpp.write_text(harness, encoding="utf-8")
            command = [
                os.environ.get("CXX", "g++"), "-std=c++20", "-UNDEBUG", "-O1",
                *shlex.split(os.environ.get("IW3_CMD_TEST_CXXFLAGS", "")),
                str(cpp), "-o", str(exe),
            ]
            build = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
