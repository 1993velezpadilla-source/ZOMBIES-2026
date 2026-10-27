"""Regression gates for compiling the full authentic IW3 dvar TU on Android."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DVAR = ROOT / "third_party/KisakCOD/src/universal/dvar.cpp"
WIN_LOCAL = ROOT / "third_party/KisakCOD/src/win32/win_local.h"
FAST_LOCK = ROOT / "third_party/KisakCOD/src/qcommon/fast_critical_section.h"
ANDROID_COMPAT = ROOT / "android/iw3-native/iw3_android_dvar_compat.h"
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"


class OriginalDvarAndroidCompileTests(unittest.TestCase):
    def test_original_dvar_translation_unit_uses_narrow_android_platform_surface(self):
        source = DVAR.read_text(encoding="utf-8")
        self.assertIn(
            '#if defined(__ANDROID__)\\n'
            '#include "iw3_android_dvar_compat.h"\\n'
            '#else\\n'
            '#include <Windows.h>\\n'
            '#include <win32/win_local.h>\\n'
            '#endif',
            source,
        )
        self.assertIn(
            '#if !defined(__ANDROID__)\\n'
            '#include <win32/win_net.h>\\n'
            '#include <devgui/devgui.h>\\n'
            '#include "com_math.h"\\n'
            '#endif',
            source,
        )
        compat = ANDROID_COMPAT.read_text(encoding="utf-8")
        self.assertIn("void NET_Sleep(int msec);", compat)
        self.assertIn("bool __cdecl Vec4Compare(const float *a, const float *b);", compat)
        self.assertIn("Dvar_RegisterVariant", source)
        self.assertIn("Dvar_RegisterNew", source)
        self.assertIn("Dvar_Reregister", source)

    def test_fast_critical_section_layout_is_shared_with_windows_and_android(self):
        lock = FAST_LOCK.read_text(encoding="utf-8")
        win = WIN_LOCAL.read_text(encoding="utf-8")
        self.assertIn("volatile uint32_t readCount;", lock)
        self.assertIn("volatile uint32_t writeCount;", lock)
        self.assertIn("sizeof(FastCriticalSection) == 8", lock)
        self.assertIn("offsetof(FastCriticalSection, writeCount) == 4", lock)
        self.assertIn("#include <qcommon/fast_critical_section.h>", win)
        self.assertNotIn("struct FastCriticalSection", win)
        self.assertNotIn("void Sys_LockWrite(FastCriticalSection* critSect);", win)

    def test_interlocked_compatibility_preserves_original_return_values(self):
        compat = ANDROID_COMPAT.read_text(encoding="utf-8")
        self.assertIn("__atomic_add_fetch(value, static_cast<T>(1), __ATOMIC_SEQ_CST)", compat)
        self.assertIn("__atomic_sub_fetch(value, static_cast<T>(1), __ATOMIC_SEQ_CST)", compat)
        self.assertIn("__atomic_compare_exchange_n(", compat)
        self.assertIn("return expected;", compat)
        self.assertIn("using LONG = std::int32_t;", compat)
        self.assertIn("#define _snprintf std::snprintf", compat)
        self.assertNotIn("Dvar_RegisterVariant(", compat)

    def test_cmake_compiles_full_original_dvar_as_object_but_does_not_link_it_to_diagnostic(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        self.assertIn(
            'add_library(iw3_sp_full_dvar OBJECT\\n'
            '        "${IW3_ENGINE_SOURCE_ROOT}/universal/dvar.cpp")',
            cmake,
        )
        self.assertIn("target_compile_definitions(iw3_sp_full_dvar PRIVATE KISAK_SP=1)", cmake)
        self.assertIn("target_compile_options(iw3_sp_full_dvar PRIVATE", cmake)
        self.assertNotIn(
            'target_sources(iw3_sp_math PRIVATE\\n'
            '        "${IW3_ENGINE_SOURCE_ROOT}/universal/dvar.cpp")',
            cmake,
        )


if __name__ == "__main__":
    unittest.main()
