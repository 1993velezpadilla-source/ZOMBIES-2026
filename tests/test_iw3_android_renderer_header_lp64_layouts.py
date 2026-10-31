"""Regression tests for 32-bit and LP64 pointer-bearing engine header layouts."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

EXPECTED = {
    "third_party/KisakCOD/src/gfx_d3d/fxprimitives.h": {
        "static_assert(sizeof(FxEffectDef) == (sizeof(void *) == 8 ? 40u : 32u));": "static_assert(sizeof(FxEffectDef) == 32);",
        "static_assert(sizeof(FxImpactTable) == (sizeof(void *) == 8 ? 16u : 8u));": "static_assert(sizeof(FxImpactTable) == 8);",
    },
    "third_party/KisakCOD/src/gfx_d3d/r_gfx.h": {
        "static_assert(sizeof(GfxImage) == (sizeof(void *) == 8 ? 48u : 36u));": "static_assert(sizeof(GfxImage) == 36);",
        "static_assert(sizeof(GfxWorldDpvsStatic) == (sizeof(void *) == 8 ? 168u : 0x68u));": "static_assert(sizeof(GfxWorldDpvsStatic) == 0x68);",
        "static_assert(sizeof(GfxPixelShaderLoadDef) == (sizeof(void *) == 8 ? 16u : 8u));": "static_assert(sizeof(GfxPixelShaderLoadDef) == 8);",
    },
    "third_party/KisakCOD/src/gfx_d3d/r_material.h": {
        "static_assert(sizeof(MaterialPixelShaderProgram) == (sizeof(void *) == 8 ? 24u : 12u));": "static_assert(sizeof(MaterialPixelShaderProgram) == 12);",
        "static_assert(sizeof(MaterialTechniqueSet) == (sizeof(void *) == 8 ? 296u : 148u));": "static_assert(sizeof(MaterialTechniqueSet) == 148);",
        "static_assert(sizeof(Material) == (sizeof(void *) == 8 ? 104u : 80u));": "static_assert(sizeof(Material) == 80);",
    },
    "third_party/KisakCOD/src/gfx_d3d/r_dobj_skin.h": {
        "static_assert(sizeof(GfxModelSurfaceInfo) == (sizeof(void *) == 8 ? 16u : 12u));": "static_assert(sizeof(GfxModelSurfaceInfo) == 12);",
        "static_assert(sizeof(GfxModelSkinnedSurface) == (sizeof(void *) == 8 ? 40u : 24u));": "static_assert(sizeof(GfxModelSkinnedSurface) == 24);",
        "static_assert(sizeof(GfxModelRigidSurface) == (sizeof(void *) == 8 ? 72u : 56u));": "static_assert(sizeof(GfxModelRigidSurface) == 56);",
    },
    "third_party/KisakCOD/src/devgui/devgui.h": {
        "static_assert(sizeof(DevMenuChild) == (sizeof(void *) == 8 ? 8u : 0x4u));": "static_assert(sizeof(DevMenuChild) == 0x4);",
        "static_assert(sizeof(DevMenuItem) == (sizeof(void *) == 8 ? 0x30u : 0x28u));": "static_assert(sizeof(DevMenuItem) == 0x28);",
        "static_assert(sizeof(devguiGlob_t) == (sizeof(void *) == 8 ? 0x70E0u : 0x5E10u));": "static_assert(sizeof(devguiGlob_t) == 0x5E10);",
    },
}


class IW3PointerBearingHeaderLp64LayoutTests(unittest.TestCase):
    def test_pointer_bearing_layouts_assert_win32_and_lp64_sizes(self):
        for relative_path, assertions in EXPECTED.items():
            with self.subTest(header=relative_path):
                content = (ROOT / relative_path).read_text(encoding="utf-8")
                for lp64_assertion, old_assertion in assertions.items():
                    self.assertEqual(content.count(lp64_assertion), 1)
                    self.assertNotIn(old_assertion, content)

    def test_all_pointer_width_layout_assertions_are_covered(self):
        self.assertEqual(sum(len(items) for items in EXPECTED.values()), 14)
        self.assertIn(
            "static_assert(sizeof(Material) == (sizeof(void *) == 8 ? 104u : 80u));",
            (ROOT / "third_party/KisakCOD/src/gfx_d3d/r_material.h").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
