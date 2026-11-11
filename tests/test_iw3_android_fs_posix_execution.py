"""Compile and execute authentic KisakCOD FS path bodies for POSIX and Win32.

This is a host portability regression, not evidence of an Android game runtime.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/universal/com_files.cpp"


class OriginalFilesystemSeparatorExecution(unittest.TestCase):
    def test_authentic_separator_and_mkdir_bodies_run_in_both_modes(self):
        compiler = shutil.which("c++") or shutil.which("g++")
        if not compiler:
            self.skipTest("Host C++ compiler not installed")
        original = SOURCE.read_text(encoding="utf-8")
        bodies = "\n\n".join(
            function_source(original, signature)
            for signature in (
                "void __cdecl FS_ReplaceSeparators(char *path)",
                "int __cdecl FS_CreatePath(char *OSPath)",
            )
        )
        harness = r"""
#include <cassert>
#include <cstring>
#include <string>
#include <vector>
#define __cdecl
constexpr int CON_CHANNEL_FILES = 0;
std::vector<std::string> mkdir_calls;
void Sys_Mkdir(const char *path) { mkdir_calls.emplace_back(path); }
void Com_PrintWarning(int, const char *, ...) {}
""" + bodies + r"""
int main() {
    char mixed[] = "/private\\iw3//main\\players/config.cfg";
    FS_ReplaceSeparators(mixed);
#if defined(IW3_FS_POSIX_PATHS_TEST)
    assert(std::strcmp(mixed, "/private/iw3/main/players/config.cfg") == 0);
    char path[] = "/private/iw3/main/players/profile.cfg";
    const char *expected_first = "/private";
    const char *expected_last = "/private/iw3/main/players";
#else
    assert(std::strcmp(mixed, "\\private\\iw3\\main\\players\\config.cfg") == 0);
    char path[] = "\\private\\iw3\\main\\players\\profile.cfg";
    const char *expected_first = "\\private";
    const char *expected_last = "\\private\\iw3\\main\\players";
#endif
    assert(FS_CreatePath(path) == 0);
    assert(mkdir_calls.size() == 4);
    assert(mkdir_calls.front() == expected_first);
    assert(mkdir_calls.back() == expected_last);
    char invalid[] = "/private/iw3/main/../escape";
    assert(FS_CreatePath(invalid) == 1);
    assert(mkdir_calls.size() == 4);
}
"""
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "fs_path_original.cpp"
            source.write_text(harness, encoding="utf-8")
            for mode, flags in (
                ("posix", ["-DIW3_FS_POSIX_PATHS_TEST=1"]),
                ("win32", []),
            ):
                binary = Path(temporary) / mode
                build = subprocess.run(
                    [compiler, "-std=c++17", "-O0", "-Wall", "-Wextra",
                     "-UNDEBUG", *flags, str(source), "-o", str(binary)],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(build.returncode, 0, build.stderr)
                run = subprocess.run(
                    [str(binary)], capture_output=True, text=True, check=False
                )
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
