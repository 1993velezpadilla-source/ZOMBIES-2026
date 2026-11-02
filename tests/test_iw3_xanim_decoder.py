#!/usr/bin/env python3
"""Synthetic XANIM version-17 parser tests; contains no game material."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from iw3_xanim_v17 import load_xanim, AnimFormatError, duration
from iw3_anim_correlation import read_nodes

def make_anim(filename, *, flags=0, numframes=30, small=False):
    raw=bytearray(struct.pack("<HHHBBH",17,numframes,2,flags,0,30))
    if flags & 2:
        raw += struct.pack("<HHH",1,0,1)
        raw += struct.pack("<fff",0.,0.,0.)
    raw += b"\x00"  # flip quat mask
    raw += b"\x02"  # second bone half-quat
    raw += b"tag_weapon\x00tag_clip\x00"
    raw += struct.pack("<H",2)
    raw += struct.pack("<BB",0,30)
    raw += struct.pack("<hhh",0,0,0)
    raw += struct.pack("<hhh",0,0,16383)
    raw += struct.pack("<Hfff",1,0.0,2.0,3.0)
    raw += struct.pack("<Hh",1,8191)
    raw += struct.pack("<H",0)
    raw += struct.pack("<B",1)
    raw += b"reload\x00"+struct.pack("<H",28)
    filename.write_bytes(raw)

class XAnimV17Test(unittest.TestCase):
    def test_keyframe_tracks_and_bones(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"viewmodel_m4_reload"
            make_anim(p)
            x=load_xanim(p)
            self.assertEqual(len(x.bones),2)
            self.assertEqual(x.bones[0].name, "tag_weapon")
            self.assertEqual(x.bones[0].rotations.indices,[0,30])
            self.assertEqual(x.bones[0].translations.values,[(0.0,2.0,3.0)])
            self.assertEqual(x.bones[1].rotation_type,"half")
            self.assertEqual(x.notes,[("reload",28)])
            self.assertEqual(duration(x),1.0)

    def test_delta_reader(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"viewmodel_mp5_idle"
            make_anim(p,flags=2)
            x=load_xanim(p)
            self.assertEqual(x.delta_trans.values[0],(0.,0.,0.))
            self.assertFalse(x.looping)

    def test_reject_wrong_version(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"anim"
            make_anim(p)
            data=bytearray(p.read_bytes())
            data[0]=18
            p.write_bytes(data)
            with self.assertRaisesRegex(AnimFormatError,"unsupported"):
                load_xanim(p)

    def test_reject_trailing(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"anim"
            make_anim(p)
            with p.open("ab") as f: f.write(b"MORE")
            with self.assertRaisesRegex(AnimFormatError,"trailing"):
                load_xanim(p)

    def test_correlation_node_joint_read(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"m4.glb"
            document={"asset":{"version":"2.0"}, "nodes":[{"name":"tag_weapon"},{"name":"tag_clip"}],
                      "skins":[{"joints":[0,1]}]}
            b=json.dumps(document).encode()
            b+=b" "*((-len(b))%4)
            p.write_bytes(struct.pack("<4sIIII",b"glTF",2,20+len(b),len(b),0x4e4f534a)+b)
            self.assertEqual(read_nodes(p)["joints"],{"tag_weapon","tag_clip"})

if __name__=="__main__":
    unittest.main()
