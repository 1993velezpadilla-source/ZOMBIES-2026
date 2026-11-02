from __future__ import annotations
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from iw3_arsenal_detail import inspect


def glb(path, skins=0, animations=0):
    payload=json.dumps({"asset":{"version":"2.0"}, "meshes":[{}],
                       "skins":[{}]*skins, "animations":[{}]*animations}).encode()
    payload+=b" "*((-len(payload))%4)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(struct.pack("<4sIIII",b"glTF",2,20+len(payload),len(payload),0x4E4F534A)+payload)


class DetailTests(unittest.TestCase):
    def test_no_confusion_between_benelli_m4_and_m4_rifle(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            for name in ["viewmodel_m4_lod0.glb","viewmodel_m4_lod1.glb",
                         "viewmodel_benelli_m4_gold_mp_lod0.glb",
                         "viewmodel_ak47_lod0.glb", "viewmodel_mp5_lod0.glb",
                         "viewmodel_base_viewhands_lod0.glb"]:
                glb(p/"common_mp"/"model_export"/name,skins=1)
            (p/"common_mp"/"xanim").mkdir()
            (p/"common_mp"/"xanim"/"reload.xanim_bin").write_bytes(b"FAKE")
            r=inspect(p)
            self.assertEqual(r["total_glb"],6)
            self.assertEqual(r["total_skinned"],6)
            self.assertEqual(r["total_animated"],0)
            self.assertEqual(r["target_counts"]["M4_rifle"],2)
            self.assertEqual(r["target_counts"]["AK47"],1)
            self.assertEqual(r["target_counts"]["MP5"],1)
            self.assertEqual(r["target_counts"]["viewhands"],1)
            self.assertEqual(r["zones"]["common_mp"]["xanim_named_file_count"],1)
            self.assertEqual(r["unique_viewmodel_families"],5)
            self.assertFalse(r["ready_for_godot_animated_weapon"])


if __name__ == "__main__":
    unittest.main()
