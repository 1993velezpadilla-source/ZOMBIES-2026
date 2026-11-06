"""The inventory scanner reports actual GLB names; variants do not imply guns."""
import json
from io import BytesIO
from pathlib import Path
import struct
import tempfile
import unittest
from zipfile import ZipFile
from inventory_apk import scan


class InventoryTests(unittest.TestCase):
    def test_extract_real_nested_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            doc={'asset':{'version':'2.0'},'meshes':[{'primitives':[]}],
                 'animations':[{'name':'idle'},{'name':'reload'}]}
            raw=json.dumps(doc).encode('utf-8')
            raw+=b' '*(-len(raw)%4)
            glb=b'glTF'+struct.pack('<II',2,20+len(raw))+struct.pack('<I4s',len(raw),b'JSON')+raw
            assets=BytesIO()
            with ZipFile(assets,'w') as inner:
                inner.writestr('games/voxelibre/mods/ak47dev/models/m9.glb',glb)
                inner.writestr('games/voxelibre/mods/ak47dev/init.lua',
                               'local M9="ak47dev:m9"\nlocal definitions={[M9]={capacity=15}}\n')
            apk=root/'test.apk'
            with ZipFile(apk,'w') as outer:
                outer.writestr('assets/assets.zip',assets.getvalue())
                outer.writestr('lib/arm64-v8a/libmain.so',b'ELF')
            report=scan(apk)
            self.assertEqual(report['glb_model_count'],1)
            self.assertEqual(report['glb_models'][0]['animation_clips'],
                             ['idle','reload'])
            self.assertEqual(report['weapon_code_signals'][0]['explicit_definition_keys'],['M9'])
            self.assertEqual(report['weapon_code_signals'][0]['item_name_literals'],
                             ['ak47dev:m9'])
            self.assertIn('Model variants are NOT independent weapons.',
                          report['limitations'])

    def test_reject_missing_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            apk=Path(directory)/'no_assets.apk'
            with ZipFile(apk,'w') as z:
                z.writestr('AndroidManifest.xml',b'no')
            with self.assertRaisesRegex(ValueError,'missing Luanti'):
                scan(apk)


if __name__=='__main__':
    unittest.main()
