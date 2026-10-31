"""Run the authentic IW3 weapon accuracy file loader against adversarial file I/O.

The extracted function is the original KisakCOD source, not a reimplementation.
Mocked filesystem/parser services are test-only and do not establish gameplay.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/bgame/bg_weapons_load_obj.cpp"
SIGNATURE = "char __cdecl G_ParseWeaponAccurayGraphInternal("


class OriginalWeaponAccuracyFileIOTests(unittest.TestCase):
    def test_real_loader_rejects_short_reads_and_truncated_paths(self):
        original = function_source(SOURCE.read_text(encoding="utf-8"), SIGNATURE)
        self.assertIn("FS_Read((uint8_t *)buffer, len, f) != len", original)
        self.assertIn("FS_Read((uint8_t *)buffer, v6 - len, f) != v6 - len", original)
        self.assertIn("pathLength >= ARRAYSIZE(string)", original)
        fixture = r"""
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#define __cdecl
#define iassert(x) assert(x)
#define ARRAYSIZE(x) (sizeof(x) / sizeof((x)[0]))
constexpr int WEAPTYPE_BULLET = 0;
constexpr int WEAPTYPE_PROJECTILE = 1;
constexpr int FS_READ = 0;
constexpr int CON_CHANNEL_SERVER = 1;
struct WeaponDef { int weapType = WEAPTYPE_BULLET; };
static std::string fileBytes, lastPath;
static size_t cursor = 0;
static int opens = 0, closes = 0, reads = 0, parses = 0, warnings = 0;
static int shortReadCall = 0;
static bool parserResult = true;
void Com_PrintWarning(int, const char*, ...) { ++warnings; }
int FS_FOpenFileByMode(const char* path, int* handle, int) {
    ++opens;
    lastPath = path;
    *handle = 17;
    cursor = 0;
    return static_cast<int>(fileBytes.size());
}
int FS_Read(uint8_t* dst, int count, int handle) {
    assert(handle == 17 && count >= 0 && cursor <= fileBytes.size());
    ++reads;
    size_t n = std::min(static_cast<size_t>(count), fileBytes.size() - cursor);
    if (reads == shortReadCall && n > 0) --n;
    std::memcpy(dst, fileBytes.data() + cursor, n);
    cursor += n;
    return static_cast<int>(n);
}
void FS_FCloseFile(int handle) { assert(handle == 17); ++closes; }
char G_ParseAIWeaponAccurayGraphFile(const char*, const char*, float (*)[2], int* count) {
    ++parses;
    *count = 1;
    return parserResult;
}
/* ORIGINAL_LOADER */
static void reset(const std::string& bytes) {
    fileBytes = bytes;
    cursor = 0;
    opens = closes = reads = parses = warnings = shortReadCall = 0;
    lastPath.clear();
    parserResult = true;
}
static int invoke(const char* name = "good.accu", int type = WEAPTYPE_BULLET) {
    WeaponDef def;
    def.weapType = type;
    float knots[16][2]{};
    int count = 0;
    return G_ParseWeaponAccurayGraphInternal(&def, "aivsai", name, knots, &count);
}
int main() {
    const std::string magic = "WEAPONACCUFILE";
    reset(magic + "1 0 1");
    assert(invoke() == 1 && opens == 1 && closes == 1 && reads == 2 && parses == 1);
    assert(lastPath == "accuracy/aivsai/good.accu");

    reset("WEAPON");
    assert(invoke() == 0 && closes == 1 && reads == 0 && parses == 0);

    reset(magic + "1 0 1");
    shortReadCall = 1;
    assert(invoke() == 0 && closes == 1 && reads == 1 && parses == 0);

    reset(magic + "1 0 1");
    shortReadCall = 2;
    assert(invoke() == 0 && closes == 1 && reads == 2 && parses == 0);

    reset(std::string(magic.size(), 'X') + "1 0 1");
    assert(invoke() == 0 && closes == 1 && parses == 0);

    reset(magic + std::string(8192, 'x'));
    assert(invoke() == 0 && closes == 1 && reads == 1 && parses == 0);

    reset(magic + "1 0 1");
    std::string tooLong(1024, 'q');
    assert(invoke(tooLong.c_str()) == 0);
    assert(opens == 0 && closes == 0 && parses == 0 && warnings > 0);

    reset(magic + "1 0 1");
    assert(invoke("good.accu", 5) == 1 && opens == 0);
    assert(invoke("") == 1 && opens == 0);

    reset(magic + "1 0 1");
    parserResult = false;
    assert(invoke() == 0 && closes == 1 && parses == 1);
    std::puts("IW3_ORIGINAL_WEAPON_ACCURACY_FILE_IO_PASS");
}
"""
        fixture = fixture.replace("/* ORIGINAL_LOADER */", original)
        with tempfile.TemporaryDirectory() as tmp:
            cpp = Path(tmp) / "original_weapon_accuracy_io.cpp"
            exe = Path(tmp) / "original_weapon_accuracy_io"
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
            self.assertIn("IW3_ORIGINAL_WEAPON_ACCURACY_FILE_IO_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
