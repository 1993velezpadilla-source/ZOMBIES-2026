"""LP64 regression for the original IW3 single-player client static allocations.

Extracts and executes TRACK_cl_main verbatim with instrumented tracking service.
This is a host-only memory-accounting test, NOT renderer or gameplay evidence.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/client/cl_main.cpp"
SIGNATURE = "void __cdecl TRACK_cl_main()"


class OriginalClientStaticTrackingTests(unittest.TestCase):
    def test_native_client_state_sizes_under_asan_ubsan(self):
        source = SOURCE.read_text(encoding="utf-8")
        original = function_source(source, SIGNATURE)
        self.assertIn("#include <qcommon/mem_track.h>", source)
        for name in ("clientUIActives", "clients", "clientConnections"):
            self.assertIn(f"TRACK_STATIC_ARR({name}, 9)", original)
        self.assertIn("TRACK_STATIC_DAT(cls, 9)", original)
        for size in ("633532", "271392", "612"):
            self.assertNotIn(size, original)

        fixture = r"""
#include <cassert>
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <vector>
#define __cdecl
struct clientUIActive_t { void* state; unsigned char flags[21]; };
struct clientActive_t { void* snapshots[3]; unsigned char payload[41]; };
struct clientConnection_t { void* commands[5]; int sequence; };
struct clientStatic_t { void* renderer; unsigned char data[37]; };
clientUIActive_t clientUIActives[1]{};
clientActive_t clients[1]{};
clientConnection_t clientConnections[1]{};
clientStatic_t cls{};
struct Record { void* address; size_t bytes; const char* name; int type; };
std::vector<Record> records;
void track_static_alloc_internal(void* ptr, int size, const char* name, int type) {
    assert(size > 0);
    records.push_back({ptr, static_cast<size_t>(size), name, type});
}
#define TRACK_STATIC_ARR(glob, type) track_static_alloc_internal(glob, sizeof(glob), #glob, type)
#define TRACK_STATIC_DAT(glob, type) track_static_alloc_internal(&glob, sizeof(glob), #glob, type)
/* ORIGINAL_FUNCTION */
int main() {
    static_assert(sizeof(void*) == 8, "LP64 required");
    TRACK_cl_main();
    assert(records.size() == 4);
#define CHECK(i, obj) do { \
    assert(records[i].address == static_cast<void*>(&(obj))); \
    assert(records[i].bytes == sizeof(obj)); \
    assert(records[i].type == 9); \
    assert(std::strcmp(records[i].name, #obj) == 0); \
} while (0)
    CHECK(0, clientUIActives);
    CHECK(1, clients);
    CHECK(2, clientConnections);
    CHECK(3, cls);
    assert(records[0].bytes != 20);
    assert(records[1].bytes != 633532);
    assert(records[2].bytes != 271392);
    assert(records[3].bytes != 612);
    std::puts("IW3_ORIGINAL_CLIENT_STATIC_TRACKING_LP64_PASS");
}
"""
        fixture = fixture.replace("/* ORIGINAL_FUNCTION */", original)
        with tempfile.TemporaryDirectory() as tmp:
            cpp = Path(tmp) / "iw3_original_client_tracking.cpp"
            exe = Path(tmp) / "iw3_original_client_tracking"
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
            run = subprocess.run(
                [str(exe)], capture_output=True, text=True, timeout=30, env=env,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_CLIENT_STATIC_TRACKING_LP64_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
