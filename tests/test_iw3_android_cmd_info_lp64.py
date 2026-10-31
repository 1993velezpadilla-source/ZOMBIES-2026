"""Execute genuine IW3 Info_Validate and Info_SetValueForKey on a 64-bit host.

This tests original q_shared.cpp function bodies, not a mock engine. The
Android ARM64 full-translation-unit compile runs separately in GitHub Actions.
No bootstrap, map, renderer or playable APK is implied.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/universal/q_shared.cpp"
WORKFLOW = ROOT / ".github/workflows/iw3-command-full-arm64.yml"


class OriginalInfoStringLP64(unittest.TestCase):
    def test_original_info_string_pointer_checks_execute_on_64bit(self):
        source = SOURCE.read_text()
        begin = source.index("bool __cdecl Info_Validate(const char *s)")
        end = source.index("\nvoid __cdecl Info_SetValueForKey_Big(", begin)
        original = source[begin:end]
        self.assertEqual(original.count("(int)strchr("), 0)
        self.assertIn("const char *v1;", original)
        self.assertIn("const char *v3;", original)
        self.assertIn("const char *v4;", original)
        self.assertIn("const char *v5;", original)
        compiler = shutil.which("c++")
        self.assertIsNotNone(compiler)
        fixture = r"""
#include <cassert>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstring>
#define __cdecl
constexpr int CON_CHANNEL_SYSTEM = 0;
static int warnings = 0;
void MyAssertHandler(const char*, int, int, const char*, ...) { assert(false); }
void Com_Printf(int, const char*, ...) { ++warnings; }
void Info_RemoveKey(char* s, const char* key) {
    // A narrow harness service: only the original info setters are under test.
    if (std::strcmp(key, "player") == 0) s[0] = '\0';
}
int Com_sprintf(char* dest, unsigned int size, const char* format, ...) {
    va_list args;
    va_start(args, format);
    const int n = std::vsnprintf(dest, size, format, args);
    va_end(args);
    return n;
}
""" + original + r"""
int main() {
    static_assert(sizeof(void*) == 8, "LP64 test requires a 64-bit host");
    assert(Info_Validate("normal_name"));
    assert(!Info_Validate("bad\"name"));
    assert(!Info_Validate("bad;name"));
    char info[1024] = {};
    Info_SetValueForKey(info, "player", "A\\;\"B");
    assert(std::strcmp(info, "\\player\\AB") == 0);
    Info_SetValueForKey(info, "player", "new");
    assert(std::strcmp(info, "\\player\\new") == 0);
    const int before = warnings;
    Info_SetValueForKey(info, "bad\\key", "x");
    Info_SetValueForKey(info, "bad;key", "x");
    Info_SetValueForKey(info, "bad\"key", "x");
    assert(warnings == before + 3);
    assert(std::strcmp(info, "\\player\\new") == 0);
    Info_SetValueForKey(info, "player", "");
    assert(info[0] == '\0');
    char oversized[1025];
    std::memset(oversized, 'x', 1024);
    oversized[1024] = '\0';
    Info_SetValueForKey(oversized, "player", "x");
    assert(std::strlen(oversized) == 1024);
    assert(warnings == before + 4);
    return 0;
}
"""
        with tempfile.TemporaryDirectory() as directory:
            cpp = Path(directory) / "original_info_lp64.cpp"
            exe = Path(directory) / "original_info_lp64"
            cpp.write_text(fixture)
            subprocess.run(
                [compiler, "-std=c++20", "-UNDEBUG", "-O1", "-g",
                 "-Wall", "-Wextra", "-Werror=pointer-to-int-cast",
                 "-Werror=int-to-pointer-cast", "-fsanitize=undefined",
                 "-fno-omit-frame-pointer", str(cpp), "-o", str(exe)],
                check=True, capture_output=True, text=True, timeout=45)
            subprocess.run([str(exe)], check=True, capture_output=True,
                           text=True, timeout=15)

    def test_workflow_compiles_original_qshared_for_arm64(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("test_iw3_android_cmd_info_lp64.py", workflow)
        self.assertIn("IW3_ORIGINAL_INFO_STRING_LP64_HOST_PASS", workflow)
        self.assertIn("universal/q_shared.cpp", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)
        self.assertNotIn("IW3_PLAYABLE_APK=true", workflow)


if __name__ == "__main__":
    unittest.main()
