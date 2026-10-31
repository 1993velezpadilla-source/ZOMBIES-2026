"""64-bit host regression of the original IW3 pure-IWD reference functions.

Extracts the genuine KisakCOD function bodies. External command/string/audio
services are host-test fixtures only; they are NOT linked into the Android JNI
diagnostic or passed off as an original-engine runtime.
"""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/qcommon/files.cpp"
PURE_SIGNATURE = "void __cdecl FS_PureServerSetLoadedIwds(char *iwdSums, char *iwdNames)"
FF_SIGNATURE = "void __cdecl FS_ServerSetReferencedFFs(char *FFSums, char *FFNames)"


class OriginalIwdPointerWidthTests(unittest.TestCase):
    def test_original_iwd_pointers_and_ff_capacity(self):
        source = SOURCE.read_text(encoding="utf-8")
        pure = function_source(source, PURE_SIGNATURE)
        ff = function_source(source, FF_SIGNATURE)
        self.assertIn("sizeof(fs_serverIwdNames[0]) * fs_numServerIwds", pure)
        self.assertIn("sizeof(fs_serverIwds[0]) * fs_numServerIwds", pure)
        self.assertNotIn("Com_Memcpy(fs_serverIwdNames, s0, 4 *", pure)
        self.assertIn(
            "sizeof(fs_serverReferencedFFCheckSums) / sizeof(fs_serverReferencedFFCheckSums[0])",
            ff,
        )
        fixture = r"""
#include <cassert>
#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sstream>
#include <stdexcept>
#include <string>
#include <strings.h>
#include <vector>
#define __cdecl
#define iassert(x) assert(x)
static_assert(sizeof(void*) == 8, "This regression requires a 64-bit host");
enum { ERR_DROP = 1, SND_STOP_STREAMED = 2, CON_CHANNEL_FILES = 3 };
int fs_numServerIwds = 0;
int fs_serverIwds[1024] = {};
const char* fs_serverIwdNames[1024] = {};
int fs_fakeChkSum = 77;
int fs_numServerReferencedFFs = 0;
int fs_serverReferencedFFCheckSums[32] = {};
const char* fs_serverReferencedFFNames[32] = {};
int g_ff_limit = -1;
static std::vector<std::string> args;

void Cmd_TokenizeString(char* s) {
    args.clear();
    std::istringstream input(s);
    std::string token;
    while (input >> token) args.push_back(token);
}
int Cmd_Argc() { return static_cast<int>(args.size()); }
const char* Cmd_Argv(int i) { return args.at(static_cast<size_t>(i)).c_str(); }
void Cmd_EndTokenizedString() { args.clear(); }
const char* CopyString(const char* s) {
    char* copy = static_cast<char*>(std::malloc(std::strlen(s) + 1));
    assert(copy);
    std::strcpy(copy, s);
    return copy;
}
void FreeString(const char* s) { std::free(const_cast<char*>(s)); }
void Com_Error(int, const char*) { throw std::runtime_error("unexpected Com_Error"); }
int I_stricmp(const char* a, const char* b) { return strcasecmp(a, b); }
void SND_StopSounds(int) {}
void Com_DPrintf(int, const char*, ...) {}
void Com_Memcpy(void* dest, const void* src, size_t n) { std::memcpy(dest, src, n); }
void FS_ShutdownServerIwdNames() {
    for (int i = 0; i < fs_numServerIwds; ++i) {
        FreeString(fs_serverIwdNames[i]);
        fs_serverIwdNames[i] = nullptr;
    }
    fs_numServerIwds = 0;
}
void FS_ShutdownServerReferencedFFs() { fs_numServerReferencedFFs = 0; }
int FS_ServerSetReferencedFiles(char*, char*, int limit, int*, const char**) {
    g_ff_limit = limit;
    return limit;
}

/* ORIGINAL_IW3_PURE_FUNCTION */
/* ORIGINAL_IW3_FF_FUNCTION */

int main() {
    char sums[] = "101 202 303";
    char names[] = "main/iw_00 main/iw_01 main/iw_02";
    FS_PureServerSetLoadedIwds(sums, names);
    assert(fs_numServerIwds == 3);
    assert(fs_serverIwds[0] == 101 && fs_serverIwds[1] == 202 && fs_serverIwds[2] == 303);
    assert(fs_serverIwdNames[0] && fs_serverIwdNames[1] && fs_serverIwdNames[2]);
    assert(std::strcmp(fs_serverIwdNames[0], "main/iw_00") == 0);
    assert(std::strcmp(fs_serverIwdNames[1], "main/iw_01") == 0);
    assert(std::strcmp(fs_serverIwdNames[2], "main/iw_02") == 0);
    const char* saved = fs_serverIwdNames[1];

    // The original unchanged-list fast path must retain the old ownership.
    char sameSums[] = "101 202 303";
    char sameNames[] = "main/iw_00 main/iw_01 main/iw_02";
    FS_PureServerSetLoadedIwds(sameSums, sameNames);
    assert(fs_serverIwdNames[1] == saved);

    // Replacing a list with a different size must copy every 64-bit pointer.
    char changedSums[] = "404 505";
    char changedNames[] = "main/iw_03 main/iw_04";
    FS_PureServerSetLoadedIwds(changedSums, changedNames);
    assert(fs_numServerIwds == 2);
    assert(fs_serverIwds[0] == 404 && fs_serverIwds[1] == 505);
    assert(fs_serverIwdNames[0] && fs_serverIwdNames[1]);
    assert(std::strcmp(fs_serverIwdNames[0], "main/iw_03") == 0);
    assert(std::strcmp(fs_serverIwdNames[1], "main/iw_04") == 0);

    char ffSums[] = "1";
    char ffNames[] = "main/test";
    FS_ServerSetReferencedFFs(ffSums, ffNames);
    assert(g_ff_limit == 32); // Original FF arrays hold only 32 entries.
    assert(fs_numServerReferencedFFs == 32);
    FS_ShutdownServerIwdNames();
    std::puts("IW3_ORIGINAL_IWD_POINTER_WIDTH_AND_FF_CAPACITY_PASS");
    return 0;
}
"""
        fixture = fixture.replace("/* ORIGINAL_IW3_PURE_FUNCTION */", pure)
        fixture = fixture.replace("/* ORIGINAL_IW3_FF_FUNCTION */", ff)
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            cpp = work / "original_iwd_pointers.cpp"
            binary = work / "original_iwd_pointers"
            cpp.write_text(fixture, encoding="utf-8")
            command = [
                os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
                "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                *shlex.split(os.environ.get("IW3_IWD_POINTER_TEST_CXXFLAGS", "")),
                str(cpp), "-o", str(binary),
            ]
            build = subprocess.run(command, capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            result = subprocess.run(
                [str(binary)], capture_output=True, text=True, timeout=20, env=env
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(
                "IW3_ORIGINAL_IWD_POINTER_WIDTH_AND_FF_CAPACITY_PASS",
                result.stdout,
            )


if __name__ == "__main__":
    unittest.main()
