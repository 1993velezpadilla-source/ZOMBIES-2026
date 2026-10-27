"""Guard the real KisakCOD filesystem TU's Android portability boundary."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/universal/com_files.cpp"
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"


def function_body(source: str, signature: str) -> str:
    start = source.find(signature)
    if start < 0 or source.find(signature, start + 1) >= 0:
        raise AssertionError(f"expected exactly one function signature: {signature}")
    opening = source.find("{", start)
    if opening < 0:
        raise AssertionError("function opening brace missing")
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1:index]
    raise AssertionError("function closing brace missing")


class OriginalFilesystemAndroidPortTests(unittest.TestCase):
    def test_directinput_header_is_excluded_from_android_translation_unit(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn(
            '#if defined(__ANDROID__)\n'
            '#include "iw3_android_platform.h"\n'
            '#include <sys/stat.h>\n'
            '#include <unistd.h>',
            source,
        )
        self.assertIn(
            '#else\n#include <win32/win_local.h>\n#endif',
            source,
        )

    def test_android_overwrite_uses_rooted_fd_not_win32_attributes(self):
        source = SOURCE.read_text(encoding="utf-8")
        body = function_body(source, "int __cdecl FS_OpenFileOverwrite(char *qpath)")
        android = body.split("#if defined(__ANDROID__)", 1)[1].split("#else", 1)[0]
        windows = body.split("#else", 1)[1].split("#endif", 1)[0]
        self.assertIn("z2026_platform_open_engine_path_fd(ospath)", android)
        self.assertIn("fstat(attributesFd, &oldAttributes)", android)
        self.assertIn("fchmod(attributesFd", android)
        self.assertNotIn("GetFileAttributesA", android)
        self.assertIn("GetFileAttributesA(ospath)", windows)
        self.assertIn("SetFileAttributesA(ospath, attributes)", windows)

    def test_filesystem_tu_does_not_import_unused_bsp_renderer_dependency(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("#include <qcommon/com_bsp.h>", source)
        self.assertIn("void __cdecl Com_GetBspFilename(char *filename, uint32_t size, const char *mapname)", source)

    def test_thread_context_abi_is_shared_without_win32_or_d3d_headers(self):
        threads = (ROOT / "third_party/KisakCOD/src/qcommon/threads.h").read_text(encoding="utf-8")
        backend = (ROOT / "third_party/KisakCOD/src/gfx_d3d/rb_backend.h").read_text(encoding="utf-8")
        context = (ROOT / "third_party/KisakCOD/src/qcommon/thread_context.h").read_text(encoding="utf-8")
        self.assertIn("#include <qcommon/thread_context.h>", threads)
        self.assertIn("#else\n#include <Windows.h>\n#include <gfx_d3d/rb_backend.h>", threads)
        self.assertIn("#if defined(__ANDROID__)", threads)
        self.assertIn("using DWORD = std::uint32_t;", threads)
        self.assertIn("using HANDLE = void *;", threads)
        self.assertIn("#include <Windows.h>", threads)
        self.assertIn("#include <qcommon/thread_context.h>", backend)
        self.assertNotIn("enum ThreadContext_t", backend)
        self.assertIn("THREAD_CONTEXT_COUNT = 12", context)
        self.assertIn("THREAD_CONTEXT_COUNT        = 0x7", context)

    def test_android_gate_compiles_complete_original_filesystem_source(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        self.assertIn(
            'add_library(iw3_sp_full_filesystem OBJECT\n'
            '        "${IW3_ENGINE_SOURCE_ROOT}/universal/com_files.cpp")',
            cmake,
        )
        self.assertIn("target_compile_definitions(iw3_sp_full_filesystem PRIVATE KISAK_SP=1)", cmake)


if __name__ == "__main__":
    unittest.main()
