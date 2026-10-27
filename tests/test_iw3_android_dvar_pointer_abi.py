"""Regression coverage for original KisakCOD dvar LP64 pointer handling."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_dvar_pointer_abi import (
    SOURCE, FUNCTIONS, SMOKE_FUNCTIONS, REQUIRED, FORBIDDEN, prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalDvarPointerAbiTests(unittest.TestCase):
    def test_corrected_functions_are_extracted_from_authentic_source(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        audit_bodies = [function_source(source, signature) for signature in FUNCTIONS]
        smoke_bodies = [function_source(source, signature) for signature in SMOKE_FUNCTIONS]
        with TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "generated" / "iw3_dvar_pointer_abi.cpp"
            smoke_output = root / "generated" / "iw3_dvar_pointer_smoke.cpp"
            report_path = root / "dvar-pointer-report.json"
            report = prepare(ENGINE, output, smoke_output, report_path)
            staged = output.read_text(encoding="utf-8")
            smoke = smoke_output.read_text(encoding="utf-8")
            for body in audit_bodies:
                self.assertIn(body, staged)
            for body in smoke_bodies:
                self.assertIn(body, smoke)
            self.assertEqual(
                report["source_sha256"], hashlib.sha256(original).hexdigest()
            )
            self.assertTrue(report["authentic_kisakcod_function_bodies_extracted"])
            self.assertTrue(report["string_values_use_native_pointer_union_member"])
            self.assertTrue(report["enum_tables_use_native_pointer_member_and_indexing"])
            self.assertTrue(report["domain_callbacks_use_declared_DvarValue_by_value_abi"])
            self.assertTrue(report["integer_domains_use_native_min_max_fields"])
            self.assertFalse(report["full_dvar_registry_linked"])
            self.assertFalse(report["filesystem_startup_invoked"])
            self.assertFalse(report["fastfile_or_map_loaded"])
            self.assertFalse(report["renderer_or_gameplay_proven"])
            self.assertFalse(report["playable_apk"])
            for marker in REQUIRED:
                self.assertIn(marker, staged)
            for marker in FORBIDDEN:
                self.assertNotIn(marker, source)
                self.assertNotIn(marker, staged)
            self.assertIn('"playable_apk": false', report_path.read_text(encoding="utf-8"))
        self.assertEqual(source_path.read_bytes(), original)

    def test_string_and_enum_paths_never_alias_native_pointers_through_int(self):
        source = (ENGINE / SOURCE).read_text(encoding="utf-8")
        self.assertIn("v5.string = value;", source)
        self.assertIn("value->string = CopyString(string);", source)
        self.assertIn("value->string = string;", source)
        self.assertIn("dvarDomain.enumeration.strings = valueList;", source)
        self.assertIn("malleableDvar->domain.enumeration.strings = stringTable;", source)
        self.assertIn("return dvar->domain.enumeration.strings[dvar->current.integer];", source)
        self.assertIn("domain->enumeration.strings[stringIndex]", source)
        self.assertIn("if (dvar->domainFunc && !dvar->domainFunc(dvar, value))", source)
        self.assertIn("if (!customFunc(dvar, dvar->current))", source)
        self.assertIn("if (value.integer < domain.integer.min)", source)
        self.assertIn("else if (value.integer > domain.integer.max)", source)
        self.assertNotIn("domain.enumeration.stringCount > domain.integer.max", source)
        self.assertNotIn("value.integer = domain.enumeration.stringCount;", source)
        self.assertNotIn("domain.integer.max + 4 *", source)
        self.assertNotIn("uint8_t(__cdecl *)(dvar_s *, int, uint32_t, uint32_t, uint32_t)", source)
        self.assertIn("dvar->current.string = nullptr;", source)
        self.assertIn("dvar->latched.string = nullptr;", source)
        self.assertIn("dvar->reset.string = nullptr;", source)


if __name__ == "__main__":
    unittest.main()
