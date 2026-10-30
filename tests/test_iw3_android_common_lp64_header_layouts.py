"""Guard the original SP bootstrap's Android LP64 header layouts."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "third_party/KisakCOD/src"


def require_layout(source: str, name: str, lp64: str, win32: str) -> None:
    expected = (
        f"static_assert(sizeof({name}) == "
        f"(sizeof(void *) == 8 ? {lp64} : {win32}));"
    )
    if expected not in source:
        raise AssertionError(f"{name} must retain Win32 and LP64 runtime sizes")


class CommonLp64HeaderLayoutTests(unittest.TestCase):
    def test_android_sound_win32_scalar_aliases_keep_fixed_width(self):
        source = (SRC / "sound/snd_public.h").read_text(encoding="utf-8")
        self.assertIn("#include <cstdint>", source)
        self.assertIn("typedef std::int32_t LONG;", source)
        self.assertIn("typedef std::uint32_t DWORD;", source)
        self.assertIn("typedef std::uintptr_t ULONG_PTR, *PULONG_PTR;", source)
        self.assertIn('static_assert(sizeof(DWORD) == 4,', source)
        self.assertIn('static_assert(sizeof(LONG) == 4,', source)
        self.assertIn('static_assert(sizeof(ULONG_PTR) == sizeof(void *),', source)

    def test_common_object_uses_only_openal_opaque_types(self):
        source = (SRC / "sound/snd_local.h").read_text(encoding="utf-8")
        cmake = (ROOT / "android/iw3-native/CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn("#if defined(IW3_ANDROID_COMMON_HEADER_ONLY_OPENAL)", source)
        self.assertIn("typedef unsigned int ALuint;", source)
        self.assertIn("typedef struct ALCdevice_struct ALCdevice;", source)
        self.assertIn("typedef struct ALCcontext_struct ALCcontext;", source)
        self.assertIn("#include <AL/al.h>", source)
        self.assertIn("#include <AL/alc.h>", source)
        self.assertIn("#include <AL/efx.h>", source)
        self.assertIn("IW3_ANDROID_COMMON_HEADER_ONLY_OPENAL=1", cmake)
        common_target = cmake.split("add_library(iw3_sp_common_full_compile", 1)[1].split("endif()", 1)[0]
        self.assertIn("IW3_ANDROID_COMMON_HEADER_ONLY_OPENAL=1", common_target)

    def test_bootstrap_uses_declaration_only_generated_buildnumber_header(self):
        compat = (ROOT / "android/iw3-native/common_compat/buildnumber.h").read_text(encoding="utf-8")
        self.assertIn("char *getBuildNumber();", compat)
        self.assertIn("int getBuildNumberAsInt();", compat)
        self.assertNotIn("#define BUILD_NUMBER", compat)
        self.assertNotIn("getBuildNumber() {", compat)

    def test_script_vm_runtime_pointer_layouts_preserve_win32_and_lp64(self):
        source = (SRC / "script/scr_vm.h").read_text(encoding="utf-8")
        layouts = {
            "Scr_StringNode_s": ("0x10", "0x8"),
            "function_stack_t": ("0x20", "0x14"),
            "function_frame_t": ("0x28", "0x18"),
            "scrVmPub_t": ("0x8540", "0x4328"),
            "FuncDebugData": ("0x18", "0x10"),
            "scrVmDebugPub_t": ("0x26410", "0x24210"),
            "scrVmGlob_t": ("0x2048", "0x2028"),
            "scrAnimPub_t": ("0x820", "0x41C"),
            "scrAnimGlob_t": ("0x218", "0x20C"),
        }
        for name, (lp64, win32) in layouts.items():
            with self.subTest(struct=name):
                require_layout(source, name, lp64, win32)

    def test_effect_runtime_pointer_layouts_preserve_win32_and_lp64(self):
        source = (SRC / "EffectsCore/fx_system.h").read_text(encoding="utf-8")
        layouts = {
            "MarkInfoCollidedDObj": ("0x18", "0xC"),
            "MarkInfoCollidedBModel": ("0x18", "0xC"),
            "MarkInfo": ("0x770", "0x448"),
            "MarkModelCoreContext": ("0x38", "0x1C"),
            "FxMarkDObjUpdateContext": ("0x208", "0x108"),
            "FxActiveMarkSurf": ("0x20", "0x14"),
            "FxDrawState": ("0xC8", "0xA8"),
            "FxTrailSegmentDrawState": ("0x40", "0x3C"),
            "FxBeam": ("0x38", "0x34"),
            "FxBeamInfo": ("0x1508", "0x1384"),
            "FxPostLight": ("0x28", "0x24"),
            "FxPostLightInfo": ("0xF08", "0xD84"),
            "FxGenerateVertsCmd": ("0x58", "0x44"),
            "FxEffectDefTableEntry": ("0x10", "0x8"),
            "FxEffectDefTable": ("0x4008", "0x2004"),
            "FxProfileEntry": ("0x20", "0x1C"),
            "FxSprite": ("0x28", "0x20"),
            "FxCurveIterator": ("0x10", "0x8"),
            "FxEditorElemDef": ("0x958", "0x858"),
            "FxEditorEffectDef": ("0x12B48", "0x10B44"),
            "FxElemField": ("0x10", "0x8"),
            "FxFlagOutputSet": ("0x18", "0xC"),
            "FxFlagDef": ("0x18", "0x10"),
        }
        for name, (lp64, win32) in layouts.items():
            with self.subTest(struct=name):
                require_layout(source, name, lp64, win32)


if __name__ == "__main__":
    unittest.main()
