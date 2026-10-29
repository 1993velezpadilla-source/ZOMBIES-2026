"""Regression guard for compiling the authentic IW3 collision-trace translation unit on Android ARM64."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE_TRACE = ROOT / "third_party/KisakCOD/src/qcommon/cm_trace.cpp"
WORKFLOW = ROOT / ".github/workflows/iw3-mover-trace-services-arm64.yml"


class OriginalCollisionTraceArm64GateTests(unittest.TestCase):
    def test_original_collision_core_contains_real_box_and_world_trace(self):
        source = ENGINE_TRACE.read_text(encoding="utf-8")
        for signature in (
            "void __cdecl CM_BoxTrace(",
            "void __cdecl CM_Trace(",
            "void __cdecl CM_TraceThroughTree(",
            "void __cdecl CM_TraceThroughLeaf(",
        ):
            with self.subTest(signature=signature):
                self.assertIn(signature, source)


    def test_collision_core_does_not_import_d3d_renderer_graph(self):
        source = ENGINE_TRACE.read_text(encoding="utf-8")
        qcommon = (ROOT / "third_party/KisakCOD/src/qcommon/qcommon.h").read_text(encoding="utf-8")
        self.assertNotIn("#include <xanim/xanim.h>", source)
        self.assertIn("enum DynEntityDrawType", qcommon)
        self.assertIn("DYNENT_DRAW_MODEL", qcommon)
        self.assertIn("DYNENT_DRAW_BRUSH", qcommon)

    def test_workflow_compiles_original_source_not_a_generated_stub(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            'collision_source="$GITHUB_WORKSPACE/third_party/KisakCOD/src/qcommon/cm_trace.cpp"',
            workflow,
        )
        self.assertIn('-c "$collision_source" -o "$collision_object"', workflow)
        self.assertIn("IW3_ORIGINAL_CM_TRACE_CORE_AARCH64_COMPILE_GREEN", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)

    def test_audit_does_not_claim_runtime_or_map_execution(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("IW3_REAL_MAP_LOADED=false", workflow)
        self.assertIn("IW3_GAMEPLAY_PROVEN=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)


if __name__ == "__main__":
    unittest.main()
