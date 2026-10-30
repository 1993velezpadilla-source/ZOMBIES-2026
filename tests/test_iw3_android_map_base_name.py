"""Exercise the authentic IW3 map-name parser under 64-bit host sanitizers.

This compiles the unchanged FS_GetMapBaseName body extracted from the
vendored KisakCOD source. It does not demonstrate Android map loading,
renderer execution, or gameplay.
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
SIGNATURE = "char *__cdecl FS_GetMapBaseName(char *mapname)"


class OriginalMapBaseNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        work = Path(cls.temp.name)
        source = SOURCE.read_text(encoding="utf-8")
        cls.original = function_source(source, SIGNATURE)
        cls.assert_source_invariants(source)
        fixture = r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <strings.h>
#define __cdecl
#define iassert(condition) assert(condition)
static int I_strnicmp(const char *a, const char *b, int n) {
    return strncasecmp(a, b, static_cast<size_t>(n));
}
static int I_stricmp(const char *a, const char *b) {
    return strcasecmp(a, b);
}
char fs_mapBaseName[64];
/* ORIGINAL_IW3_MAP_FUNCTION */
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    std::fputs(FS_GetMapBaseName(argv[1]), stdout);
    return 0;
}
"""
        (work / "map_base.cpp").write_text(
            fixture.replace("/* ORIGINAL_IW3_MAP_FUNCTION */", cls.original),
            encoding="utf-8",
        )
        cls.binary = work / "map_base"
        command = [
            os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
            "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
            *shlex.split(os.environ.get("IW3_MAP_TEST_CXXFLAGS", "")),
            str(work / "map_base.cpp"), "-o", str(cls.binary),
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    @staticmethod
    def assert_source_invariants(source):
        body = function_source(source, SIGNATURE)
        assert "mapLength >= 3" in body
        assert "mapLength < 7" in body
        assert "baseLength >= sizeof(fs_mapBaseName)" in body
        assert "fs_mapBaseName[0] = 0" in body
        assert "mapname[v2 - 3]" not in body

    def check(self, value, expected):
        # Leak detection can be unavailable in containerized CI; ASan and
        # UBSan instrumentation still check each invocation.
        env = os.environ.copy()
        env["ASAN_OPTIONS"] = "detect_leaks=0"
        result = subprocess.run(
            [str(self.binary), value], capture_output=True, text=True,
            env=env, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, expected)

    def test_normal_map_path_and_extension(self):
        self.check("maps/mp/mp_test.d3dbsp", "mp_test")
        self.check("mp_test.d3dbsp", "mp_test")

    def test_plain_name_and_percent_replacement(self):
        self.check("test", "test")
        self.check("maps/mp/mp%test", "mp_test")

    def test_short_names_do_not_underflow(self):
        for name in ("", "b", "bs", "bsp", "x.bsp", "maps/mp/bsp"):
            with self.subTest(name=name):
                self.check(name, "" if name.endswith("bsp") else name)

    def test_exact_capacity_and_overlong_names(self):
        self.check("x" * 63, "x" * 63)
        self.check("x" * 64, "")
        self.check("maps/mp/" + "x" * 300 + ".d3dbsp", "")

    def test_case_insensitive_extension_and_prefix(self):
        self.check("MAPS/MP/Mp_Test.D3DBSP", "Mp_Test")


if __name__ == "__main__":
    unittest.main()
