"""Portability gate for the original IW3 SP model-pose source on Android ARM64."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"
WORKFLOW = ROOT / ".github/workflows/iw3-original-native-android.yml"
POSE = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_model_pose.cpp"


class OriginalRendererModelPosePortabilityTests(unittest.TestCase):
    def test_android_build_compiles_the_complete_original_pose_translation_unit(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        self.assertIn("add_library(iw3_sp_renderer_model_pose_full_compile OBJECT", cmake)
        self.assertIn('"${IW3_ENGINE_SOURCE_ROOT}/gfx_d3d/r_model_pose.cpp"', cmake)
        self.assertIn("target_compile_definitions(iw3_sp_renderer_model_pose_full_compile PRIVATE KISAK_SP=1)", cmake)
        self.assertNotIn("target_link_libraries(iw3_sp_math PRIVATE iw3_sp_renderer_model_pose_full_compile", cmake)

    def test_gate_checks_real_pose_symbols_and_keeps_rendering_claims_false(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("CMakeFiles/iw3_sp_renderer_model_pose_full_compile.dir", workflow)
        self.assertIn("R_DObjCalcPose(GfxSceneEntity const*, DObj_s const*, int*)", workflow)
        self.assertIn("R_UpdateSceneEntBounds(GfxSceneEntity*, GfxSceneEntity**, DObj_s const**, int)", workflow)
        self.assertIn("IW3_ORIGINAL_RENDERER_MODEL_POSE_AARCH64_OBJECT_PASS", workflow)
        self.assertIn("IW3_RENDERER_BACKEND_LINKED=false", workflow)
        self.assertIn("IW3_REAL_MAP_LOADED=false", workflow)
        self.assertIn("IW3_RENDERER_FRAME_PROVEN=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)

    def test_source_is_the_original_engine_pose_module_not_a_replacement(self):
        source = POSE.read_text(encoding="utf-8")
        self.assertIn("#if defined(__ANDROID__)", source)
        self.assertIn("__atomic_compare_exchange_n(&sceneEnt->cull.state, &expectedCullState, 1u,", source)
        self.assertIn("__ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST", source)
        self.assertIn("InterlockedCompareExchange((volatile LONG *)&sceneEnt->cull, 1, 0) != 0", source)
        self.assertIn("DObjAnimMat *__cdecl R_DObjCalcPose(", source)
        self.assertIn("DObjAnimMat *R_UpdateSceneEntBounds(", source)
        self.assertNotIn("Godot", source)


if __name__ == "__main__":
    unittest.main()
