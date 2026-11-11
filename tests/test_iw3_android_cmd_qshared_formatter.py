"""Execute the authentic q_shared.cpp Com_sprintfPos body under C99/Bionic formatting.

This is a host sanitizer regression of original engine code, NOT an Android
bootstrap, renderer, map load, gameplay run, or playable APK.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/universal/q_shared.cpp"
WORKFLOW = ROOT / ".github/workflows/iw3-command-full-arm64.yml"


class OriginalQSharedBionicFormatting(unittest.TestCase):
    def test_real_com_sprintfpos_truncation_under_sanitizers(self):
        source = SOURCE.read_text()
        begin = source.index("int Com_sprintfPos(")
        end = source.index("\nbool __cdecl CanKeepStringPointer", begin)
        original = source[begin:end]
        self.assertIn("static_cast<uint32_t>(len) >= destModSize", original)
        self.assertIn("len == destModSize || len == -1", original)
        self.assertIn("#if defined(__ANDROID__)", original)
        compiler = shutil.which("c++")
        self.assertIsNotNone(compiler)
        fixture = r"""
#include <cstdint>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <cassert>
#define __cdecl
#define _vsnprintf vsnprintf
""" + original + r"""
int main() {
    char a[8] = {};
    int pos = 0;
    int written = Com_sprintfPos(a, 8, &pos, "%s", "123456789");
    assert(written == 9 && pos == 7 && a[7] == '\0');
    assert(std::strcmp(a, "1234567") == 0);
    assert(Com_sprintfPos(a, 8, &pos, "%s", "X") == -1);
    char b[16] = {};
    pos = 0;
    assert(Com_sprintfPos(b, 16, &pos, "%s", "abc") == 3);
    assert(pos == 3);
    assert(Com_sprintfPos(b, 16, &pos, "%s", "de") == 2);
    assert(pos == 5 && std::strcmp(b, "abcde") == 0);
    char c[8] = {};
    pos = 0;
    assert(Com_sprintfPos(c, 8, &pos, "%s", "1234567") == 7);
    assert(pos == 7 && std::strcmp(c, "1234567") == 0);
    return 0;
}
"""
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "original_formatter.cpp"
            exe = Path(directory) / "original_formatter"
            src.write_text(fixture)
            subprocess.run(
                [compiler, "-std=c++20", "-D__ANDROID__=1", "-UNDEBUG",
                 "-O1", "-Wall", "-Wextra", "-fsanitize=undefined",
                 "-fno-omit-frame-pointer", str(src), "-o", str(exe)],
                check=True, capture_output=True, text=True, timeout=45)
            subprocess.run([str(exe)], check=True, capture_output=True,
                           text=True, timeout=15)

    def test_full_original_translation_unit_is_part_of_arm64_graph(self):
        workflow = WORKFLOW.read_text()
        for required in ("universal/q_shared.cpp",
                         "iw3-original-q-shared-full-aarch64.o",
                         "Com_InitThreadData(int)",
                         "IW3_ORIGINAL_COM_INITTHREADDATA_AARCH64_PROVIDER_RESOLVED",
                         "IW3_PLAYABLE_APK=false"):
            self.assertIn(required, workflow)
        self.assertNotIn("IW3_PLAYABLE_APK=true", workflow)


if __name__ == "__main__":
    unittest.main()
