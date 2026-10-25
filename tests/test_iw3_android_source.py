"""Checks that ARM64 port consumes genuine KisakCOD source unchanged."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from tools.iw3_android.prepare_real_engine_math import (
    ENGINE_FILE, ORIGINAL_PROLOGUE, REQUIRED_FUNCTIONS, prepare,
    SURFACE_FILE, SURFACE_PROLOGUE, prepare_surface,
    CONSTANT_FILE, CONSTANT_PROLOGUE, prepare_constants
)

from tools.iw3_android.prepare_g_runframe_prereqs import (
    COM_SHARED, G_MAIN, MEMCPY_SIGNATURE, FRAME_SIGNATURE,
    FRAME_LEGACY_ASSUMPTIONS, FRAME_TYPED_PORTABILITY_MARKERS, IMPORTANT_CALLS,
    function_source, prepare as prepare_frame_prereq,
)

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class NativeIW3SourceBridgeTests(unittest.TestCase):
    def test_real_aim_math_preserved(self):
        source = (ENGINE / ENGINE_FILE).read_bytes()
        self.assertTrue(source.decode("utf-8").startswith(ORIGINAL_PROLOGUE))
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "generated" / "com_math_anglevectors.cpp"
            report = prepare(ENGINE, output)
            patched = output.read_text(encoding="utf-8")
            self.assertTrue(report["original_function_bodies_preserved"])
            self.assertFalse(report["android_iw3_apk_exists"])
            self.assertFalse(report["godot_used"])
            self.assertFalse(report["renderer_gles_ported"])
            self.assertEqual(report["source_sha256"], hashlib.sha256(source).hexdigest())
            self.assertEqual(report["original_iw3_math_functions"], list(REQUIRED_FUNCTIONS))
            original = source.decode("utf-8")[len(ORIGINAL_PROLOGUE):]
            original = original.replace('#include "q_shared.h"', "", 1)
            self.assertEqual(
                patched, '#include "iw3_android_math_compat.h"\n' + original)
        self.assertEqual((ENGINE / ENGINE_FILE).read_bytes(), source)

    def test_original_engine_surface_table_and_functions_are_unchanged(self):
        original = (ENGINE / SURFACE_FILE).read_bytes()
        self.assertTrue(original.decode("utf-8").startswith(SURFACE_PROLOGUE))
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "generated" / "surfaceflags.cpp"
            result = prepare_surface(ENGINE, out)
            self.assertEqual(result["source_sha256"], hashlib.sha256(original).hexdigest())
            self.assertTrue(result["function_bodies_preserved"])
            self.assertGreaterEqual(result["data_table_entries_preserved"], 50)
            expected = '#include "iw3_android_surface_compat.h"\n#include "surfaceflags.h"\n'
            self.assertEqual(out.read_text(encoding="utf-8"),
                             expected + original.decode("utf-8")[len(SURFACE_PROLOGUE):])
        self.assertEqual((ENGINE / SURFACE_FILE).read_bytes(), original)

    def test_original_engine_config_registry_unchanged(self):
        original = (ENGINE / CONSTANT_FILE).read_bytes()
        self.assertTrue(original.decode("utf-8").startswith(CONSTANT_PROLOGUE))
        self.assertIn(b'constantConfigStrings[833]', original)
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "generated" / "com_constantconfigstrings.cpp"
            evidence = prepare_constants(ENGINE, out)
            self.assertTrue(evidence["function_bodies_preserved"])
            self.assertEqual(evidence["original_registry_rows"], 833)
            self.assertEqual(evidence["source_sha256"], hashlib.sha256(original).hexdigest())
            patched = out.read_text(encoding="utf-8")
            expected = ('#include "iw3_android_surface_compat.h"\n'
                        '#include "com_constantconfigstrings.h"\n')
            original_body = original.decode("utf-8")[len(CONSTANT_PROLOGUE):]
            original_body = original_body.replace('#include "q_shared.h"', '', 1)
            self.assertEqual(patched, expected + original_body)
            with self.assertRaisesRegex(ValueError, "Refusing"):
                prepare_constants(ENGINE, ENGINE / CONSTANT_FILE)
        self.assertEqual((ENGINE / CONSTANT_FILE).read_bytes(), original)

    def test_original_sp_runframe_prereq_and_32bit_blockers(self):
        com_original = (ENGINE / COM_SHARED).read_bytes()
        sp_original = (ENGINE / G_MAIN).read_bytes()
        frame = function_source(sp_original.decode("utf-8"), FRAME_SIGNATURE)
        self.assertGreater(frame.count("\n"), 200)
        for marker in FRAME_LEGACY_ASSUMPTIONS:
            self.assertNotIn(marker, frame)
        for marker in FRAME_TYPED_PORTABILITY_MARKERS:
            self.assertIn(marker, frame)
        for call in IMPORTANT_CALLS:
            self.assertIn(call, frame)
        with TemporaryDirectory() as temp:
            out = Path(temp) / "stage" / "iw3_frame_memcpy.cpp"
            report_path = Path(temp) / "evidence.json"
            report = prepare_frame_prereq(ENGINE, out, report_path)
            self.assertFalse(report["g_runframe_compiled_on_android"])
            self.assertFalse(report["iw3_game_apk_available"])
            self.assertTrue(report["original_memcpy_function_preserved_exactly"])
            self.assertTrue(report["frame_animation_loop_uses_typed_entity_fields"])
            self.assertTrue(report["other_sp_engine_abi_assumptions_unverified"])
            self.assertTrue(all(n == 0 for n in report["known_32bit_entity_pointer_hazards_remaining"].values()))
            body = function_source(com_original.decode("utf-8"), MEMCPY_SIGNATURE)
            self.assertEqual(out.read_text(encoding="utf-8"),
                             '#include "iw3_android_frame_compat.h"\n' + body + "\n")
            self.assertEqual(report["original_memcpy_source_sha256"],
                             hashlib.sha256(body.encode("utf-8")).hexdigest())
            self.assertTrue(report_path.is_file())
            with self.assertRaisesRegex(ValueError, "Never overwrite"):
                prepare_frame_prereq(ENGINE, ENGINE / COM_SHARED, report_path)
        self.assertEqual((ENGINE / COM_SHARED).read_bytes(), com_original)
        self.assertEqual((ENGINE / G_MAIN).read_bytes(), sp_original)

    def test_no_vendor_overwrite(self):
        with self.assertRaisesRegex(ValueError, "Refusing"):
            prepare(ENGINE, ENGINE / ENGINE_FILE)


if __name__ == "__main__":
    unittest.main()
