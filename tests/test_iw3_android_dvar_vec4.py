"""Regression tests for the original KisakCOD Vec4Compare dependency provider."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_dvar_vec4 import (
    SOURCE, SIGNATURE, REQUIRED, FORBIDDEN, prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalDvarVec4ProviderTests(unittest.TestCase):
    def test_generated_provider_is_the_exact_original_function_body(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        body = function_source(source, SIGNATURE)
        with TemporaryDirectory() as temp:
            output = Path(temp) / "generated" / "iw3_dvar_vec4_compare.cpp"
            report = prepare(ENGINE, output, Path(temp) / "evidence.json")
            staged = output.read_text(encoding="utf-8")
            self.assertIn(body, staged)
            self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
            self.assertTrue(report["original_Vec4Compare_body_preserved_verbatim"])
            self.assertTrue(report["uses_exact_four_component_float_equality"])
            self.assertFalse(report["full_dvar_runtime_linked"])
            self.assertFalse(report["playable_apk"])
            for marker in REQUIRED:
                self.assertIn(marker, staged)
            for marker in FORBIDDEN:
                self.assertNotIn(marker, staged)
        self.assertEqual(source_path.read_bytes(), original)

    def test_cmake_and_arm64_link_gate_include_provider_without_hiding_other_services(self):
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("IW3_EXTRACTED_DVAR_VEC4_COMPARE", cmake)
        self.assertIn("dvar_vec4_native_test.cpp", cmake)
        self.assertIn("prepare_real_engine_dvar_vec4.py", workflow)
        self.assertIn("IW3_EXTRACTED_DVAR_VEC4_COMPARE", workflow)
        self.assertIn("Vec4Compare dependency should have been resolved", workflow)
        self.assertIn("Com_Printf", workflow)


if __name__ == "__main__":
    unittest.main()
