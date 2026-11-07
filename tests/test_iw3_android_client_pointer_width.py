"""LP64 regression for authentic IW3 SP client skeleton and state loops.

Executes verbatim original CL_ResetSkeletonCache / CL_ClearState and the
original CL_Init arcade score registration loop with test-only services.
This is a host component test, NOT a running Android client or renderer.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/client/cl_main.cpp"


class OriginalClientPointerWidthTests(unittest.TestCase):
    def test_skeleton_configstrings_and_arcade_loops_lp64(self):
        source = SOURCE.read_text(encoding="utf-8")
        skeleton = function_source(source, "void __cdecl CL_ResetSkeletonCache()")
        clear = function_source(source, "void __cdecl CL_ClearState()")
        self.assertIn("reinterpret_cast<uintptr_t>", skeleton)
        self.assertNotIn("(unsigned int)&clients[0].skelMemory", skeleton)
        self.assertIn("clients[0].configstrings + MAX_CONFIGSTRINGS", clear)
        self.assertNotIn("(int)configstrings", clear)
        start = source.index("    v21 = 0;\n    v22 = arcadeScore;\n")
        finish = "    } while (v22 != arcadeScore + 19);"
        end = source.index(finish, start) + len(finish)
        arcade = source[start:end]
        self.assertNotIn("(int)v22", arcade)
        self.assertIn("v22 != arcadeScore + 19", arcade)

        fixture = r"""
#include <cassert>
#include <cstdarg>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#define __cdecl
#define __int16 short
#define iassert(x) assert(x)
#define MAX_CONFIGSTRINGS 2442
constexpr int SND_STOP_ALL = 7;
struct Client {
    uint16_t configstrings[MAX_CONFIGSTRINGS];
    char mapname[64];
    uint32_t skelTimeStamp;
    char skelMemory[524288];
    char* skelMemoryStart;
    int skelMemPos;
};
Client clients[1]{};
struct Connection { uint64_t sequence; };
Connection clientConnections[1]{};
struct dvar_s { int value; };
const dvar_s* arcadeScore[19]{};
dvar_s scores[19]{};
std::vector<uint16_t> removed;
int skeletonClears = 0;
bool Sys_IsMainThread() { return true; }
void CG_CreateNextSnap(int, float, int) {}
void CG_SetNextSnap(int) {}
void SND_StopSounds(int mode) { assert(mode == SND_STOP_ALL); }
void SL_RemoveRefToString(uint16_t value) { removed.push_back(value); }
void Com_ClientDObjClearAllSkel() { ++skeletonClears; }
int Com_sprintf(char* dst, int cap, const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    int n = std::vsnprintf(dst, static_cast<size_t>(cap), fmt, args);
    va_end(args);
    return n;
}
const dvar_s* Dvar_RegisterInt(const char* name, int, int, int, unsigned, const char*) {
    int index = -1;
    assert(std::sscanf(name, "s%d", &index) == 1);
    assert(index >= 0 && index < 19);
    scores[index].value = index + 100;
    return &scores[index];
}
/* ORIGINAL_SKELETON */
/* ORIGINAL_CLEAR */
void test_arcade() {
    int v21;
    const dvar_s** v22;
    char v29[80];
/* ORIGINAL_ARCADE */
}
int main() {
    static_assert(sizeof(void*) == 8, "LP64 host required");
    Client& client = clients[0];
    client.skelTimeStamp = UINT32_MAX;
    CL_ResetSkeletonCache();
    assert(client.skelTimeStamp == 1);
    assert(client.skelMemPos == 0);
    uintptr_t begin = reinterpret_cast<uintptr_t>(&client.skelMemory[0]);
    uintptr_t end = begin + sizeof(client.skelMemory);
    uintptr_t aligned = reinterpret_cast<uintptr_t>(client.skelMemoryStart);
    assert(aligned >= begin && aligned < end && aligned % 16 == 0);
    client.skelTimeStamp = 1;
    CL_ResetSkeletonCache();
    assert(client.skelTimeStamp == 2);
    client.configstrings[0] = 5;
    client.configstrings[MAX_CONFIGSTRINGS - 1] = 42;
    client.configstrings[100] = 99;
    clientConnections[0].sequence = 123;
    CL_ClearState();
    assert(removed.size() == 3);
    assert(removed[0] == 5 && removed[1] == 99 && removed[2] == 42);
    assert(skeletonClears == 1);
    assert(clients[0].configstrings[0] == 0);
    assert(clients[0].configstrings[MAX_CONFIGSTRINGS - 1] == 0);
    assert(clientConnections[0].sequence == 0);
    test_arcade();
    for (int i = 0; i < 19; ++i)
        assert(arcadeScore[i] == &scores[i] && arcadeScore[i]->value == i + 100);
    std::puts("IW3_ORIGINAL_CLIENT_POINTER_WIDTH_LP64_PASS");
}
"""
        fixture = (fixture.replace("/* ORIGINAL_SKELETON */", skeleton)
                   .replace("/* ORIGINAL_CLEAR */", clear)
                   .replace("/* ORIGINAL_ARCADE */", arcade))
        with tempfile.TemporaryDirectory() as tmp:
            cpp = Path(tmp) / "client_lp64.cpp"
            exe = Path(tmp) / "client_lp64"
            cpp.write_text(fixture, encoding="utf-8")
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++20", "-O1", "-g",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run(
                [str(exe)], capture_output=True, text=True, timeout=30, env=env,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_CLIENT_POINTER_WIDTH_LP64_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
