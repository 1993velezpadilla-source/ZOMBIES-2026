#!/usr/bin/env python3
"""Tests run without any proprietary Call of Duty files or downloaded tools."""
from __future__ import annotations
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from iw3_weapon_probe import glb_metadata, scan_output, stage_archive, zip_members_for, IW3_ASSET_TYPES


def fake_glb(path: Path, meshes=1, skins=0, animations=0) -> None:
    payload = {"asset": {"version": "2.0"},
               "meshes": [{} for _ in range(meshes)],
               "skins": [{} for _ in range(skins)],
               "animations": [{} for _ in range(animations)],
               "nodes": [{}]}
    blob = json.dumps(payload).encode("utf-8")
    blob += b" " * ((-len(blob)) % 4)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<4sIIII", b"glTF", 2, 20 + len(blob), len(blob), 0x4E4F534A) + blob)


class WeaponProbeTests(unittest.TestCase):
    def test_actual_iw3_asset_type_names(self):
        # Native type names from OpenAssetTools GameIW3.cpp.
        self.assertEqual(IW3_ASSET_TYPES, ("xmodel", "xanim", "weapon", "image", "material"))

    def test_fixed_allowlist(self):
        self.assertEqual(zip_members_for(["common_mp"], True),
                         ["zone/spanish/common_mp.ff", "main/iw_02.iwd", "main/iw_03.iwd"])

    def test_detects_missing_archive_without_creating_data(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError, "Missing/incorrect"):
                stage_archive(Path(t), Path(t) / "out", ["common_mp"], True)

    def test_glb_header_and_rig_counts(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "weapon_mp5.glb"
            fake_glb(p, meshes=2, skins=1, animations=3)
            self.assertEqual(glb_metadata(p)["skins"], 1)
            self.assertEqual(glb_metadata(p)["animations"], 3)
            corrupted = Path(t) / "broken.glb"
            corrupted.write_bytes(b"broken")
            with self.assertRaises(ValueError):
                glb_metadata(corrupted)

    def test_scanner_does_not_confuse_mesh_with_animation(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            fake_glb(root / "xmodels" / "weapon_ak47.glb")
            fake_glb(root / "xmodels" / "weapon_mp5.glb", skins=1, animations=2)
            (root / "viewhands_arms.xanim_bin").write_bytes(b"FAKE")
            report = scan_output(root)
            self.assertEqual(report["glb_total"], 2)
            self.assertEqual(report["glb_with_skins"], 1)
            self.assertEqual(report["glb_with_animations"], 1)
            self.assertTrue(report["weapon_filename_matches"]["AK-47"])
            self.assertTrue(report["weapon_filename_matches"]["MP5"])
            self.assertTrue(report["weapon_filename_matches"]["viewhands"])

    def test_rejects_glb_length_mismatch(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "m4.glb"
            fake_glb(p)
            with p.open("ab") as f:
                f.write(b"????")
            with self.assertRaisesRegex(ValueError, "Invalid GLB"):
                glb_metadata(p)


if __name__ == "__main__":
    unittest.main()
