"""Regression tests for original-only 28-weapon animation bridge."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from luanti_real_arsenal_28 import match, choose_source, build


class FakeBone:
    def __init__(self, name):
        self.name = name


class FakeAnimation:
    def __init__(self):
        self.bones = [FakeBone("j_gun"), FakeBone("tag_weapon"), FakeBone("j_main")]


def glb(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    doc={"asset":{"version":"2.0"}, "meshes":[{}], "skins":[{}], "animations":[]}
    blob=json.dumps(doc).encode()
    blob+=b" "*((-len(blob))%4)
    path.write_bytes(struct.pack("<4sIIII",b"glTF",2,len(blob)+20,len(blob),0x4e4f534a)+blob)


class Original28Tests(unittest.TestCase):
    def test_no_benelli_m4_identity_confusion(self):
        self.assertFalse(match("viewmodel_benelli_m4_lod0", ["viewmodel_m4"]))
        self.assertTrue(match("viewmodel_m4_lod0", ["viewmodel_m4"]))
        self.assertTrue(match("viewmodel_m4_acog_lod0", ["viewmodel_m4"]))

    def test_select_real_matching_joint_tracks(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            glb(root/"model_export/viewmodel_m4_lod0.glb")
            glb(root/"model_export/viewmodel_benelli_m4_lod0.glb")
            (root/"xanim").mkdir()
            for clip in ("idle","ads_up","fire","reload"):
                (root/"xanim"/f"viewmodel_m4_{clip}.xanim_bin").write_bytes(b"v17")
            with patch("luanti_real_arsenal_28.read_nodes",
                       return_value={"joints":{"j_gun","tag_weapon","j_main"}}),\
                 patch("luanti_real_arsenal_28.load_xanim",
                       return_value=FakeAnimation()):
                chosen,report=choose_source(root/"model_export",root/"xanim",
                                            ["viewmodel_m4"])
            self.assertIsNotNone(chosen)
            self.assertEqual(chosen[0].name,"viewmodel_m4_lod0.glb")
            self.assertEqual(set(chosen[1]),{"idle","ads","fire","reload"})
            self.assertGreaterEqual(report["minimum_common_bones"],2)

    def test_gold_deagle_source_model_can_reuse_native_base_xanim_with_rig_check(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            glb(root/"model_export/viewmodel_desert_eagle_gold_mp_lod0.glb")
            (root/"xanim").mkdir()
            for action in ("idle","ads_up","fire","reload"):
                (root/"xanim"/f"viewmodel_desert_eagle_{action}").write_bytes(b"original-xanim")
            with patch("luanti_real_arsenal_28.read_nodes",
                       return_value={"joints":{"j_gun","tag_weapon","j_main"}}),\
                 patch("luanti_real_arsenal_28.load_xanim",
                       return_value=FakeAnimation()):
                chosen,rec=choose_source(
                    root/"model_export",root/"xanim",
                    ["viewmodel_desert_eagle_gold"],
                    ["viewmodel_desert_eagle_gold","viewmodel_desert_eagle"])
            self.assertIsNotNone(chosen)
            self.assertTrue(chosen[0].name.startswith("viewmodel_desert_eagle_gold"))
            self.assertEqual(set(chosen[1]),{"idle","ads","fire","reload"})

    def test_reload_empty_does_not_replace_normal_reload(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            glb(root/"model_export/viewmodel_ak47_mp_lod0.glb")
            (root/"xanim").mkdir()
            for action in ("idle","ads_up","fire","reload_empty","reload"):
                (root/"xanim"/f"viewmodel_ak47_{action}").write_bytes(b"original-xanim")
            with patch("luanti_real_arsenal_28.read_nodes",
                       return_value={"joints":{"j_gun","tag_weapon","j_main"}}),\
                 patch("luanti_real_arsenal_28.load_xanim",
                       return_value=FakeAnimation()):
                chosen,rec=choose_source(root/"model_export",root/"xanim",["viewmodel_ak47"])
            self.assertIsNotNone(chosen)
            self.assertEqual(chosen[1]["reload"].name,"viewmodel_ak47_reload")
            self.assertEqual(chosen[1]["reload_empty"].name,"viewmodel_ak47_reload_empty")

    def test_only_empty_reload_cannot_pretend_normal_reload_exists(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            glb(root/"model_export/viewmodel_ak47_mp_lod0.glb")
            (root/"xanim").mkdir()
            for action in ("idle","ads_up","fire","reload_empty"):
                (root/"xanim"/f"viewmodel_ak47_{action}").write_bytes(b"original-xanim")
            with patch("luanti_real_arsenal_28.read_nodes",
                       return_value={"joints":{"j_gun","tag_weapon","j_main"}}),\
                 patch("luanti_real_arsenal_28.load_xanim",
                       return_value=FakeAnimation()):
                chosen,rec=choose_source(root/"model_export",root/"xanim",["viewmodel_ak47"])
            self.assertIsNone(chosen)

    def test_no_missing_source_can_produce_28_fake_models(self):
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/"dumps"
            (source/"common_mp/model_export").mkdir(parents=True)
            (source/"common_mp/xanim").mkdir()
            glb(source/"common_mp/model_export/viewmodel_base_viewhands_lod0.glb")
            weapons=[{"id":f"gun{i}", "name":f"Gun {i}", "category":"assault",
                      "model_aliases":[f"viewmodel_gun{i}"]}
                     for i in range(28)]
            result=build(source,{"weapons":weapons},Path(t)/"out")
            self.assertEqual(result["weapon_source_animated_pair_count"],0)
            self.assertFalse(result["android_runtime_playtested"])

    def test_reject_fake_shorter_catalog(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,"28 uniquely named"):
                build(Path(t),{"weapons":[{"id":"fake"}]},
                      Path(t)/"out")


if __name__ == "__main__":
    unittest.main()
