"""Synthetic tests for staged COD4 texture references; no proprietary files."""
from pathlib import Path
import json
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from iw3_stage_weapon_textures import collect_required, gather

def glb(path,uris):
    d={"asset":{"version":"2.0"},"buffers":[{"byteLength":0}],
       "images":[{"uri":s} for s in uris]}
    raw=json.dumps(d).encode()
    raw+=b" "*((-len(raw))%4)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(struct.pack("<4sIIII",b"glTF",2,20+len(raw)+8,len(raw),0x4e4f534a)
                     +raw+struct.pack("<II",0,0x004e4942))


class TextureGateTests(unittest.TestCase):
    def test_no_path_traversal_staging_and_reports_missing(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            glb(root/"animated_preview"/"ak47_animated_experimental.glb",
                ["../images/weapon_ak47_c.dds","../../../../../etc/passwd",
                 "../images/unavailable.dds"])
            p=root/"dumps"/"common_mp"/"images"/"weapon_ak47_c.dds"
            p.parent.mkdir(parents=True)
            p.write_bytes(b"synthetic DDS only")
            (root/"main").mkdir()
            with zipfile.ZipFile(root/"main"/"iw_02.iwd","w") as z:
                z.writestr("images/irrelevant.iwi",b"fake")
            req=collect_required(root/"animated_preview")
            self.assertEqual(req,{"weapon_ak47_c.dds","unavailable.dds"})
            result=gather(root/"animated_preview",root,root/"godot_sandbox"/"images",
                          root/"does-not-exist")
            self.assertEqual(result["required_images"],2)
            self.assertEqual(result["existing_dds"],1)
            self.assertEqual(result["missing_images"],["unavailable.dds"])
            self.assertFalse(result["all_dependencies_available"])


if __name__=="__main__":unittest.main()
