"""Adversarial tests for a real GLB + real COD4 WeaponDef runtime package."""
from __future__ import annotations
import json
from pathlib import Path
import struct
import tempfile
import unittest

from build_private_arsenal import source_profile, source_seconds, stage


def valid_glb(path, *, clips=("idle","ads","fire","reload","reload_empty"), skin=True):
    path.parent.mkdir(parents=True,exist_ok=True)
    doc={"asset":{"version":"2.0"}, "meshes":[{"primitives":[]}],
         "skins":[{"joints":[]} ] if skin else [],
         "animations":[{"name":x,"channels":[{"sampler":0,"target":{}}]}
                       for x in clips]}
    payload=json.dumps(doc).encode()
    payload+=b" "*((-len(payload))%4)
    path.write_bytes(struct.pack("<4sIIII",b"glTF",2,20+len(payload),
                                 len(payload),0x4e4f534a)+payload)


def fixture(complete=True, empty=True):
    identities=[
        {"id":f"gun{i}","name":f"Gun {i}","category":"assault"} for i in range(28)
    ]
    animation={
        "target_unique_weapon_count":28,
        "result":{"gun0":{"source_glb_generated":True,
                           "source_hands_generated":True}}
    }
    original={
        "weapons":{"gun0":{
            "has_required_timing_and_ammo":complete,
            "source_definition_name":"real_gun0_mp",
            "numeric":{
                "clipSize":30,"maxAmmo":210,"fireTime":0.085,
                "reloadTime":2.5,"reloadEmptyTime":3.25,"damage":40},
            "strings":{"fireType":"Full Auto"}
        }}
    }
    return {"weapons":identities}, animation, original


class PrivateArsenalTests(unittest.TestCase):
    def test_one_real_pair_is_not_falsely_called_28(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            expected,animated,original=fixture()
            for suffix in ("real_source_experimental", "hands_source_experimental"):
                valid_glb(root/"source"/f"gun0_{suffix}.glb")
            package=stage(expected,animated,original,root/"source",root/"out")
            self.assertEqual(package["native_models_verified_by_original_binary"],1)
            self.assertEqual(package["gameplay_logic_with_original_stats_and_empty_reload"],1)
            self.assertEqual(package["native_model_ids"],["gun0"])
            self.assertFalse(package["runtime_pose_verified"])
            self.assertFalse(package["runtime_sounds_verified"])
            self.assertTrue((root/"out/models/arsenal_gun0_hands.glb").exists())
            self.assertTrue((root/"out/models/arsenal_gun0_gun.glb").exists())
            self.assertEqual((root/"out/textures/arsenal_flat_metal.png").read_bytes()[:8],
                             b"\x89PNG\r\n\x1a\n")

    def test_real_source_with_missing_stats_is_preview_only(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            expected,animated,original=fixture(complete=False)
            for suffix in ("real_source_experimental","hands_source_experimental"):
                valid_glb(root/"source"/f"gun0_{suffix}.glb")
            result=stage(expected,animated,original,root/"source",root/"out")
            self.assertEqual(result["native_models_verified_by_original_binary"],1)
            self.assertEqual(result["gameplay_logic_with_original_stats_and_empty_reload"],0)
            self.assertFalse(result["weapons"][0]["gameplay_logic_enabled"])

    def test_empty_reload_track_never_faked(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            expected,animated,original=fixture()
            for suffix in ("real_source_experimental","hands_source_experimental"):
                valid_glb(root/"source"/f"gun0_{suffix}.glb",
                          clips=("idle","ads","fire","reload"))
            result=stage(expected,animated,original,root/"source",root/"out")
            self.assertFalse(result["weapons"][0]["distinct_empty_reload_animation"])
            self.assertTrue(result["weapons"][0]["gameplay_logic_enabled"])
            self.assertTrue(result["weapons"][0]["original_stats_verified"])

    def test_no_real_model_raises_instead_of_faking_28(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            expected,animated,original=fixture()
            with self.assertRaisesRegex(ValueError,"no genuine native model"):
                stage(expected,animated,original,root/"source",root/"out")

    def test_missing_rig_source_is_refused(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            expected,animated,original=fixture()
            for suffix in ("real_source_experimental","hands_source_experimental"):
                valid_glb(root/"source"/f"gun0_{suffix}.glb",skin=False)
            with self.assertRaisesRegex(ValueError,"no genuine native model"):
                stage(expected,animated,original,root/"source",root/"out")

    def test_real_cod4_weapon_def_times_are_already_seconds(self):
        self.assertAlmostEqual(source_seconds(.085),.085)
        self.assertAlmostEqual(source_seconds(2.5),2.5)
        self.assertAlmostEqual(source_seconds(3.25),3.25)
        self.assertIsNone(source_seconds(100))
        self.assertIsNone(source_seconds(0))

    def test_real_cod4_firetype_strings_are_preserved(self):
        _,_,original=fixture()
        row=original["weapons"]["gun0"]
        for source_type,expect in [
                ("Full Auto","auto"),("Single Shot","semi"),
                ("3-Round Burst","burst")]:
            row["strings"]["fireType"]=source_type
            result=source_profile({},row)
            self.assertIsNotNone(result)
            self.assertEqual(result["fire_mode"],expect)

    def test_unsupported_fire_type_is_not_invented(self):
        _,_,original=fixture()
        row=original["weapons"]["gun0"]
        row["strings"]["fireType"]="unknown"
        self.assertIsNone(source_profile({},row))


if __name__=="__main__":
    unittest.main()
