"""Execute the authentic KisakCOD weapon accuracy graph parser with sanitizers.

Only the original function body is extracted. Parsing/session services are test
providers, not a replacement game engine. This does not prove Android gameplay.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/bgame/bg_weapons_load_obj.cpp"
SIGNATURE = "char __cdecl G_ParseAIWeaponAccurayGraphFile("


class OriginalWeaponAccuracyGraphTests(unittest.TestCase):
    def test_original_parser_accepts_16_and_rejects_invalid_knot_counts(self):
        body = function_source(SOURCE.read_text(encoding="utf-8"), SIGNATURE)
        self.assertIn("knots[knotCountIndex][0]", body)
        self.assertIn("knots[knotCountIndex][1]", body)
        self.assertIn("v4 <= 0 || v4 > 16", body)
        self.assertNotIn("(*knots)[2 * knotCountIndex", body)

        fixture = r"""
#include <cassert>
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#define __cdecl
#define iassert(x) assert(x)
constexpr int CON_CHANNEL_SERVER = 1;
struct parseInfo_t { char token[128]; };
static int starts = 0, ends = 0, warnings = 0, errors = 0;
void Com_BeginParseSession(const char*) { ++starts; }
void Com_EndParseSession() { ++ends; }
void Com_PrintWarning(int, const char*, ...) { ++warnings; }
void Com_PrintError(int, const char*, ...) { ++errors; }
parseInfo_t* Com_Parse(const char** cursor) {
    static parseInfo_t result;
    result.token[0] = 0;
    while (**cursor && std::isspace(static_cast<unsigned char>(**cursor)))
        ++*cursor;
    if (!**cursor) return &result;
    size_t i = 0;
    while (**cursor && !std::isspace(static_cast<unsigned char>(**cursor))) {
        if (i + 1 < sizeof(result.token))
            result.token[i++] = **cursor;
        ++*cursor;
    }
    result.token[i] = 0;
    return &result;
}
/* ORIGINAL_PARSER */
struct Guarded {
    uint64_t before = 0x123456789abcdef0ULL;
    float knots[16][2]{};
    uint64_t after = 0x0fedcba987654321ULL;
};
bool run_case(const std::string& data, bool expected, int expected_count = -1) {
    Guarded guarded;
    int count = -99;
    const int start0 = starts, end0 = ends;
    const bool ok = G_ParseAIWeaponAccurayGraphFile(
        data.c_str(), "weapon/accuracy", guarded.knots, &count);
    assert(ok == expected);
    assert(starts == start0 + 1 && ends == end0 + 1);
    assert(guarded.before == 0x123456789abcdef0ULL);
    assert(guarded.after == 0x0fedcba987654321ULL);
    if (expected_count >= 0) assert(count == expected_count);
    if (ok && expected_count == 2) {
        assert(guarded.knots[0][0] == 0.0f);
        assert(guarded.knots[0][1] == 0.25f);
        assert(guarded.knots[1][0] == 1.0f);
        assert(guarded.knots[1][1] == 0.75f);
    }
    return ok;
}
int main() {
    run_case("2 0 0.25 1 0.75", true, 2);
    std::string sixteen = "16";
    for (int i = 0; i < 16; ++i)
        sixteen += " " + std::to_string(i == 15 ? 1.0 : i / 16.0) + " 0.5";
    run_case(sixteen, true, 16);
    run_case("0", false);
    run_case("-1", false);
    run_case("17", false);
    run_case("nonnumeric", false);
    run_case("2 0 0.25 1", false, 2);
    run_case("1 0 0.25", false, 1);
    run_case("1 1 0.5 0.5 0.5", false, 1);
    run_case(sixteen + " 0.5 0.5", false, 16);
    assert(errors >= 6);
    assert(warnings >= 1);
    std::puts("IW3_ORIGINAL_WEAPON_ACCURACY_GRAPH_BOUNDS_PASS");
}
"""
        fixture = fixture.replace("/* ORIGINAL_PARSER */", body)
        with tempfile.TemporaryDirectory() as tmp:
            cpp = Path(tmp) / "original_weapon_accuracy.cpp"
            exe = Path(tmp) / "original_weapon_accuracy"
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
            self.assertIn("IW3_ORIGINAL_WEAPON_ACCURACY_GRAPH_BOUNDS_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
