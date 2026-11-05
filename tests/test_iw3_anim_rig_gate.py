from __future__ import annotations
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from iw3_anim_rig_gate import parse_xanim_header, review


def raw_xanim(path,frames=16,bones=("tag_weapon","tag_clip"),flags=0):
    path.parent.mkdir(parents=True,exist_ok=True)
    header=struct.pack("<HHHBBH",17,frames,len(bones),flags,0,30)
    bitmasks=b"\x00"*(2*((len(bones)+7)//8))
    names=b"".join(name.encode()+b"\x00" for name in bones) if not flags & 2 else b""
    path.write_bytes(header + bitmasks + names)


class AnimGateTests(unittest.TestCase):
    def test_raw_header_bones(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"reload"
            raw_xanim(p)
            v=parse_xanim_header(p)
            self.assertEqual(v["version"],17)
            self.assertEqual(v["bone_count"],2)
            self.assertEqual(v["bone_name_parse"],"ok")
            self.assertEqual(v["bone_names_sample"],["tag_weapon","tag_clip"])
            self.assertEqual(v["frame_rate"],30)

    def test_action_matrix_is_evidence_not_godot_success(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"common_mp"/"xanim"
            for name in ("viewmodel_m4_idle","viewmodel_m4_ads_up",
                         "viewmodel_m4_fire","viewmodel_m4_reload",
                         "viewmodel_ak47_reload","viewmodel_mp5_sprint_in"):
                raw_xanim(p/name)
            r=review(Path(d))
            self.assertEqual(r["valid_headers"],6)
            self.assertEqual(r["invalid_headers"],0)
            self.assertTrue(all(r["action_presence"]["M4"].values()))
            self.assertEqual(r["families"]["AK47"]["action_counts"]["reload"],1)
            self.assertFalse(r["action_presence"]["MP5"]["reload"])
            self.assertFalse(r["full_rig_animation_verified"])

    def test_invalid_header_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x"
            p.write_bytes(b"HELLO")
            with self.assertRaises(ValueError):
                parse_xanim_header(p)


if __name__ == "__main__":
    unittest.main()
