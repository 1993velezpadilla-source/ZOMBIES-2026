from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/qcommon/files.cpp"
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"


def function_body(source: str, signature: str) -> str:
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening:index + 1]
    raise AssertionError(f"unterminated original function: {signature}")


class OriginalFileComparisonPointerWidthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.cmake = CMAKE.read_text(encoding="utf-8")

    def assert_native_pointer_end(self, name: str, signature: str):
        body = function_body(self.source, signature)
        self.assertIn("const char *v7;", body, name)
        self.assertIn("v7 = &string[strlen(string) + 1];", body, name)
        self.assertIn("v7 == v5", body, name)
        self.assertIn("static_cast<int>(v7 - v5)", body, name)
        self.assertNotIn("uint32_t v7", body, name)
        self.assertNotIn("(uint32_t)&string", body, name)
        self.assertNotIn("(_DWORD)v5", body, name)

    def test_original_iwd_comparison_uses_pointer_difference_not_32_bit_address(self):
        self.assert_native_pointer_end(
            "FS_CompareIwds", "int __cdecl FS_CompareIwds("
        )

    def test_original_fastfile_comparison_uses_pointer_difference_not_32_bit_address(self):
        self.assert_native_pointer_end(
            "FS_CompareFFs", "int __cdecl FS_CompareFFs("
        )

    def test_original_qcommon_files_translation_unit_is_compiled_for_android_abi(self):
        self.assertIn(
            'add_library(iw3_sp_full_qcommon_files OBJECT',
            self.cmake,
        )
        self.assertIn(
            '"${IW3_ENGINE_SOURCE_ROOT}/qcommon/files.cpp"',
            self.cmake,
        )
        self.assertIn(
            "target_compile_definitions(iw3_sp_full_qcommon_files PRIVATE KISAK_SP=1)",
            self.cmake,
        )


if __name__ == "__main__":
    unittest.main()
