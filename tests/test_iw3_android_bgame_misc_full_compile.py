"""Regression for compiling and partially linking the complete original IW3 BGame dvar TU."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD/src/bgame/bg_misc.cpp"
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"
WORKFLOW = ROOT / ".github/workflows/iw3-original-native-android.yml"


class OriginalBGameMiscArm64Tests(unittest.TestCase):
    def test_complete_original_translation_unit_is_an_android_object_target(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        self.assertIn("add_library(iw3_sp_bgame_misc_full_compile OBJECT", cmake)
        self.assertIn('${IW3_ENGINE_SOURCE_ROOT}/bgame/bg_misc.cpp', cmake)
        self.assertIn("KISAK_SP=1 KISAK_OPENAL=1", cmake)

    def test_real_original_registration_function_and_melee_dvars_exist(self):
        source = ENGINE.read_text(encoding="utf-8")
        self.assertEqual(source.count("void __cdecl BG_RegisterDvars()"), 1)
        self.assertIn("player_meleeRange = Dvar_RegisterFloat(", source)
        self.assertIn("player_meleeWidth = Dvar_RegisterFloat(", source)
        self.assertIn("player_meleeHeight = Dvar_RegisterFloat(", source)
        self.assertIn("player_meleeChargeFriction = Dvar_RegisterFloat(", source)

    def test_workflow_links_full_bgame_object_to_original_dvar_object(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("iw3_sp_bgame_misc_full_compile.dir", workflow)
        self.assertIn("iw3_sp_full_dvar.dir", workflow)
        self.assertIn('ld.lld" -m aarch64linux -r "$bg_misc_object" "$dvar_object"', workflow)
        self.assertIn("IW3_ORIGINAL_BGAME_MISC_DVAR_FLOAT_RELOCATABLE_LINK_PASS", workflow)
        self.assertIn("IW3_BGAME_MISC_RUNTIME_INVOKED=false", workflow)
        self.assertIn("IW3_BGAME_DVARS_REGISTERED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)


if __name__ == "__main__":
    unittest.main()
