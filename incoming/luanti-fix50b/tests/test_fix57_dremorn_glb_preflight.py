import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path('incoming/luanti-fix50b/tools/inspect_dremorn_glb.py')
spec=importlib.util.spec_from_file_location('validator',SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def build_glb(path,data):
    payload=json.dumps(data).encode('utf-8')
    payload+=b' '*((-len(payload))%4)
    length=12+8+len(payload)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,length)
        +struct.pack('<I4s',len(payload),b'JSON')+payload)


def scene():
    clips=['idle1','idle2','walk','run','rage','atack1','atack2','atack3',
           'atack4','gethit','death1','death2']
    return {'asset':{'version':'2.0'},'meshes':[{'primitives':[{'attributes':{}}]}],
     'skins':[{'joints':[1]}],'nodes':[{'mesh':0,'skin':0},{'name':'root'}],
     'materials':[{'name':'body'}], 'animations':[
      {'name':name,'samplers':[{'input':0,'output':1}],
       'channels':[{'sampler':0,'target':{'node':1,'path':'rotation'}}]}
       for name in clips],
     'accessors':[{'min':[0.0],'max':[2.0]},{'type':'VEC4'}]}


class DremornPreflight(unittest.TestCase):
    def test_exact_vendor_tracks_and_death_duration(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'zombie.glb'
            build_glb(path,scene())
            out=mod.inspect(path)
            self.assertEqual(out['skins'],1)
            self.assertEqual(out['materials'],1)
            self.assertEqual(len(out['animations']),12)
            self.assertEqual(out['animation_durations_seconds']['death1'],2.0)

    def test_missing_track_refuses_integration(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'invalid.glb'
            s=scene();s['animations']=[x for x in s['animations'] if x['name']!='atack1']
            build_glb(path,s)
            with self.assertRaisesRegex(ValueError,'atack1'):
                mod.inspect(path)

    def test_rig_is_mandatory(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'unrigged.glb'
            s=scene();s['skins']=[]
            build_glb(path,s)
            with self.assertRaisesRegex(ValueError,'no rig'):
                mod.inspect(path)

    def test_multiple_materials_require_explicit_texture_mapping(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'multimaterial.glb'
            s=scene();s['materials'].append({'name':'eyes'})
            build_glb(path,s)
            with self.assertRaisesRegex(ValueError,'2 materials'):
                mod.inspect(path)

    def test_not_glb(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'obj.glb';path.write_text('obj')
            with self.assertRaisesRegex(ValueError,'Not a binary glTF'):
                mod.inspect(path)


if __name__=='__main__':
    unittest.main()
