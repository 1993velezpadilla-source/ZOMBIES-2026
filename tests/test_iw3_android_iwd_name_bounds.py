"""Run the authentic KisakCOD pure-server IWD name classifiers under host ASan/UBSan.

The extracted bodies are unchanged from qcommon/files.cpp; external string
helpers are test-only providers, not Android runtime or gameplay evidence.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/qcommon/files.cpp"


class OriginalIwdNameBoundsTests(unittest.TestCase):
    def test_original_pure_iwd_name_bounds(self):
        source = SOURCE.read_text(encoding="utf-8")
        pak = function_source(source, "BOOL __cdecl FS_serverPak(const char *pak)")
        iw = function_source(source, "int __cdecl FS_iwIwd(char *iwd, char *base)")
        self.assertIn("length == sizeof(szFile)", pak)
        self.assertIn("length == sizeof(szFile)", iw)
        self.assertIn("prefixLength >= sizeof(szFile)", iw)
        self.assertNotIn("*v3++", pak)
        self.assertNotIn("*v9++", iw)

        fixture = r"""
#include <cassert>
#include <cstddef>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <string>
#include <strings.h>
#define __cdecl
using BOOL = int;
static char* I_strlwr(char* p) {
    for (char* q = p; *q; ++q)
        if (*q >= 'A' && *q <= 'Z') *q = char(*q - 'A' + 'a');
    return p;
}
static int FS_FilenameCompare(const char* a, const char* b) {
    return strcasecmp(a, b);
}
static const char* va(const char* format, ...) {
    static char buffer[8][256];
    static unsigned slot = 0;
    char* out = buffer[(slot++) % 8];
    va_list ap;
    va_start(ap, format);
    vsnprintf(out, 256, format, ap);
    va_end(ap);
    return out;
}
/* ORIGINAL_PAK */
/* ORIGINAL_IWD */
int main() {
    assert(FS_serverPak(nullptr) == 0);
    assert(FS_serverPak("main/_SVR_pack") != 0);
    assert(FS_serverPak("main/test") == 0);
    std::string maxName = "_svr_" + std::string(62, 'x'); // 67 bytes + NUL
    assert(maxName.size() == 67);
    assert(FS_serverPak(maxName.c_str()) != 0);
    std::string overflowName = maxName + "x";
    assert(FS_serverPak(overflowName.c_str()) == 0);
    assert(FS_serverPak((overflowName + std::string(10000, 'y')).c_str()) == 0);

    auto check = [](const std::string& path, const char* base, int expected) {
        std::string mutablePath = path;
        assert((FS_iwIwd(mutablePath.data(), const_cast<char*>(base)) != 0) == (expected != 0));
    };
    check("main/iw_00", "main", 1);
    check("main/iw_24", "main", 1);
    check("main/iw_25", "main", 0);
    check("main/localized_english_iw00", "main", 1);
    check("main/localized_english_iw24", "main", 1);
    check("main/localized_english_iw25", "main", 0);
    check("mods/localized_english_iw00", "main", 0);
    check("main/localized_" + std::string(53, 'x'), "main", 0);
    check("main/localized_" + std::string(10000, 'x') + "_iw00", "main", 0);
    check("main/localized__iw00", "main", 1);
    check("main/localized_english_iw00", "MAIN", 1);
    assert(FS_iwIwd(nullptr, const_cast<char*>("main")) == 0);
    char empty[] = "";
    assert(FS_iwIwd(empty, nullptr) == 0);
    std::puts("IW3_ORIGINAL_IWD_NAME_BOUNDS_PASS");
}
"""
        fixture = fixture.replace("/* ORIGINAL_PAK */", pak).replace("/* ORIGINAL_IWD */", iw)
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            cpp = work / "iwd_name_bounds.cpp"
            binary = work / "iwd_name_bounds"
            cpp.write_text(fixture, encoding="utf-8")
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(cpp), "-o", str(binary)],
                capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run(
                [str(binary)], capture_output=True, text=True, timeout=30, env=env,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_IWD_NAME_BOUNDS_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
