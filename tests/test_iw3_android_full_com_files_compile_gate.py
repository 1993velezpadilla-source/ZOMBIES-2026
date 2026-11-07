from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CMAKE = ROOT / "android" / "iw3-native" / "CMakeLists.txt"


class FullOriginalComFilesCompileGateTests(unittest.TestCase):
    def test_android_build_compiles_the_authentic_full_translation_unit(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        marker = "# Compile the complete authentic com_files.cpp translation unit for Android"
        self.assertIn(marker, cmake)
        start = cmake.index(marker)
        end = cmake.index("endif()", start)
        block = cmake[start:end]

        self.assertIn("if(ANDROID)", block)
        self.assertIn(
            'add_library(iw3_sp_com_files_full_compile OBJECT',
            block,
        )
        self.assertIn(
            '"\u0024{IW3_ENGINE_SOURCE_ROOT}/universal/com_files.cpp"',
            block,
        )
        self.assertIn("KISAK_SP=1", block)
        self.assertIn("-fsigned-char", block)
        self.assertIn("-fno-fast-math", block)

    def test_full_translation_unit_is_compile_only_not_diagnostic_runtime(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        marker = "# Compile the complete authentic com_files.cpp translation unit for Android"
        start = cmake.index(marker)
        end = cmake.index("endif()", start)
        block = cmake[start:end]

        self.assertIn("OBJECT", block)
        self.assertIn("unresolved engine services are expected", block)
        self.assertIn("NOT linked into the diagnostic JNI library", block)
        self.assertNotIn(
            "target_link_libraries(iw3_sp_math PRIVATE iw3_sp_com_files_full_compile)",
            cmake,
        )


if __name__ == "__main__":
    unittest.main()
