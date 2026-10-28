"""Regression coverage for LP64 layouts pulled in by original IW3 frame code.

These assertions permit native-width compilation only. They do not claim that
the original script VM or the full Android runtime has been linked/executed.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD/src"


class Lp64ScriptLayoutTests(unittest.TestCase):
    def test_pointer_bearing_script_records_keep_win32_and_lp64_assertions(self):
        header = (ENGINE / "script/scr_variable.h").read_text(encoding="utf-8")
        self.assertIn("KISAK_SCRIPT_POINTER_LAYOUT_LP64", header)
        expected = {
            "VariableStackBuffer": ("0x10", "0xC"),
            "VariableUnion": ("0x8", "0x4"),
            "VariableValue": ("0x10", "0x8"),
            "VariableValueInternal_u": ("0x8", "0x4"),
            "VariableValueInternal": ("0x18", "0x10"),
            "scrVarDebugPub_t": ("0x140008", "0xE0004"),
            "scrVarGlob_t": ("0x240000", "0x180000"),
            "scr_classStruct_t": ("0x10", "0xC"),
            "VariableDebugInfo": ("0x20", "0x10"),
            "ThreadDebugInfo": ("0x110", "0x8C"),
        }
        for name, (lp64_size, win32_size) in expected.items():
            with self.subTest(name=name):
                self.assertIn(f"sizeof({name}) == {lp64_size}", header)
                self.assertIn(f"sizeof({name}) == {win32_size}", header)
        self.assertIn("#undef KISAK_SCRIPT_POINTER_LAYOUT_LP64", header)

    def test_network_address_alignment_is_standard_cpp(self):
        header = (ENGINE / "qcommon/net_chan.h").read_text(encoding="utf-8")
        self.assertIn("struct alignas(4) netadr_t", header)
        self.assertNotIn("struct __declspec(align(4)) netadr_t", header)

    def test_math_header_avoids_android_posix_random_collision(self):
        header = (ENGINE / "universal/com_math.h").read_text(encoding="utf-8")
        source = (ENGINE / "universal/com_math.cpp").read_text(encoding="utf-8")
        self.assertIn("#if defined(__ANDROID__)\n// Avoid colliding with POSIX long random(void) on Android/Linux.\nfloat __cdecl Com_Random();", header)
        self.assertIn("float __cdecl Com_Random()", source)
        self.assertIn("return (Com_Random() * 2.0 - 1.0);", source)
        self.assertIn("#define KISAK_FORCEINLINE static inline __attribute__((always_inline))", header)

    def test_no_other_engine_callsite_depends_on_posix_random_name(self):
        # Strip comments first so a note in source does not count as a callsite.
        pattern = re.compile(r"\brandom\s*\(")
        ignored = {
            ENGINE / "universal/com_math.cpp",
            ENGINE / "universal/com_math.h",
        }
        hits = []
        for path in ENGINE.rglob("*"):
            if path.suffix not in {".c", ".cc", ".cpp", ".h", ".hpp", ".inl"} or path in ignored:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            text = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
            if pattern.search(text):
                hits.append(str(path.relative_to(ROOT)))
        self.assertEqual(hits, [], "Rename these engine callsites to the portable engine RNG: " + ", ".join(hits))


if __name__ == "__main__":
    unittest.main()
