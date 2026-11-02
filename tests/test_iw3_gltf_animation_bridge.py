"""Synthetic animation GLB injection tests; no COD assets."""
from pathlib import Path
import json
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from iw3_gltf_animation_bridge import attach,read_glb
from iw3_xanim_v17 import load_xanim


def model(path):
    data={"asset":{"version":"2.0"},"nodes":[{"name":"tag_weapon"},{"name":"tag_clip"}],
          "scenes":[{"nodes":[0,1]}],"scene":0,"skins":[{"joints":[0,1]}],
          "buffers":[{"byteLength":0}]}
    encoded=json.dumps(data).encode()
    encoded+=b" "*((-len(encoded))%4)
    path.write_bytes(struct.pack("<4sIIII",b"glTF",2,20+len(encoded)+8,len(encoded),0x4e4f534a)
                     + encoded + struct.pack("<II",0,0x004e4942))


def xanim(path):
    # Full rotation for tag_weapon; half quaternion for tag_clip.
    raw=bytearray(struct.pack("<HHHBBH",17,30,2,0,0,30))
    raw+=b"\x00\x02tag_weapon\x00tag_clip\x00"
    raw+=struct.pack("<H",2)+bytes([0,29])
    raw+=struct.pack("<hhh",0,0,0)+struct.pack("<hhh",0,0,10000)
    raw+=struct.pack("<Hfff",1,0.0,2.0,3.0)
    raw+=struct.pack("<Hh",1,8191)+struct.pack("<H",0)
    raw+=b"\x00"
    path.write_bytes(raw)


class BridgeTests(unittest.TestCase):
    def test_build_and_read_back_four_animations(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)
            base=p/"model.glb"
            model(base)
            path=p/"viewmodel_m4_idle"
            xanim(path)
            out=p/"animated.glb"
            report=attach(base,{a:path for a in ("idle","ads","fire","reload")},out)
            self.assertTrue(report["glb_animated"])
            self.assertFalse(report["animation_pose_verified"])
            doc,binary=read_glb(out)
            self.assertEqual(len(doc["animations"]),4)
            self.assertEqual([a["name"] for a in doc["animations"]],
                             ["ads","fire","idle","reload"])
            self.assertEqual(len(doc["animations"][0]["channels"]),3)
            self.assertEqual(doc["buffers"][0]["byteLength"],len(binary))

    def test_reject_glb_without_bone_skin(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)
            base=p/"model.glb"
            model(base)
            data,_=read_glb(base)
            data["skins"]=[]
            raw=json.dumps(data).encode()
            raw+=b" "*((-len(raw))%4)
            base.write_bytes(struct.pack("<4sIIII",b"glTF",2,20+len(raw)+8,len(raw),0x4e4f534a)
                             +raw+struct.pack("<II",0,0x004e4942))
            path=p/"anim"
            xanim(path)
            with self.assertRaisesRegex(ValueError,"without skin"):
                attach(base,{"idle":path},p/"out.glb")


if __name__=="__main__":
    unittest.main()
