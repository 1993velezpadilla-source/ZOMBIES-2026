"""Synthetic regression tests for real-source census, never a fake playable count."""
from pathlib import Path
import json
import struct
import tempfile
import unittest

from discover_cod4_original import discover, source_match, source_glb_metadata


def glb(path, *, skin=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {"asset": {"version": "2.0"}, "meshes": [{}],
           "skins": [{}] if skin else [], "animations": []}
    text = json.dumps(doc).encode()
    text += b" " * ((-len(text)) % 4)
    path.write_bytes(struct.pack("<4sIIII", b"glTF", 2,
                                 20 + len(text), len(text), 0x4E4F534A) + text)


MANIFEST = {"schema_version": 1, "target_weapon_count": 2, "weapons": [
    {"id": "m4", "name": "M4", "category": "assault", "fire_mode": "auto",
     "model_aliases": ["viewmodel_m4"]},
    {"id": "m1014", "name": "Benelli M4", "category": "shotgun", "fire_mode": "semi",
     "model_aliases": ["viewmodel_benelli_m4"]}
]}


class DiscoveryTests(unittest.TestCase):
    def test_no_confusion_m4_with_benelli(self):
        self.assertFalse(source_match("viewmodel_benelli_m4", ["viewmodel_m4"]))
        self.assertFalse(source_match("viewmodel_m40a3", ["viewmodel_m4"]))
        self.assertTrue(source_match("viewmodel_m4_lod0", ["viewmodel_m4"]))
        self.assertTrue(source_match("viewmodel_m4_acog_lod1", ["viewmodel_m4"]))

    def test_separate_animation_files_do_not_mean_playable(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            glb(root/"common_mp/model_export/viewmodel_m4_lod0.glb")
            glb(root/"common_mp/model_export/viewmodel_benelli_m4_lod0.glb")
            for action in ("idle", "fire", "reload", "ads_up"):
                p = root/f"common_mp/xanim/viewmodel_m4_{action}.xanim_bin"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b"XANIM SOURCE ONLY")
            data = discover(root, MANIFEST)
            self.assertEqual(data["unique_weapon_identities_with_skinned_model"], 2)
            self.assertEqual(data["unique_weapon_identities_with_xanim_name_coverage"], 1)
            self.assertFalse(data["full_arsenal_playable"])
            self.assertFalse(data["weapons"][0]["glb_animation_retargeted"])
            self.assertFalse(data["weapons"][1]["source_animation_coverage"])

    def test_missing_skin_not_a_valid_3d_fps_viewmodel(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            glb(root/"common_mp/model_export/viewmodel_m4_lod0.glb", skin=False)
            data = discover(root, MANIFEST)
            self.assertFalse(data["weapons"][0]["source_model_found"])

    def test_missing_everything_is_not_success(self):
        with tempfile.TemporaryDirectory() as d:
            data = discover(Path(d), MANIFEST)
            self.assertEqual(data["unique_weapon_identities_with_skinned_model"], 0)
            self.assertEqual(data["unique_weapon_identities_with_xanim_name_coverage"], 0)

    def test_duplicate_weapon_ids_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            bad = dict(MANIFEST)
            bad["weapons"] = [MANIFEST["weapons"][0]] * 2
            with self.assertRaisesRegex(ValueError, "duplicate weapon ids"):
                discover(Path(d), bad)


if __name__ == "__main__":
    unittest.main()
