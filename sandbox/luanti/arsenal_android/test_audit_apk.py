"""Synthetic APK fixtures: missing content must fail, not turn GREEN."""
from io import BytesIO
import json
from pathlib import Path
import struct
import tempfile
import unittest
from zipfile import ZipFile
from audit_apk import AuditError, inspect


def glb(animation_names=('idle', 'reload')):
    data = json.dumps({
        'asset': {'version': '2.0'},
        'meshes': [{'primitives': []}],
        'animations': [{'name': a} for a in animation_names]
    }, separators=(',', ':')).encode()
    data += b' ' * ((-len(data)) % 4)
    return (b'glTF' + struct.pack('<II', 2, 20 + len(data)) +
            struct.pack('<I4s', len(data), b'JSON') + data)


def create_fixture(root, *, missing_model=False, missing_animation=False):
    model = 'games/voxelibre/mods/arsenal/models/m9.glb'
    catalog = {
        'schema_version': 1,
        'weapons': [{'id': 'm9', 'category': 'pistol', 'model': model,
                     'animations': ['idle', 'reload']}],
        'models': [model],
        'configurations': [{'id': 'm9.base', 'weapon': 'm9',
                            'attachments': []}]
    }
    nested = BytesIO()
    with ZipFile(nested, 'w') as z:
        if not missing_model:
            z.writestr(model, glb(('idle',) if missing_animation
                                  else ('idle', 'reload')))
    apk = root / 'arsenal.apk'
    with ZipFile(apk, 'w') as z:
        z.writestr('AndroidManifest.xml', b'\x03\x00')
        z.writestr('lib/arm64-v8a/libmain.so', b'ELF')
        z.writestr('assets/assets.zip', nested.getvalue())
    return apk, catalog


class APKVerifierTests(unittest.TestCase):
    def test_valid_synthetic_apk(self):
        with tempfile.TemporaryDirectory() as d:
            apk, cat = create_fixture(Path(d))
            result = inspect(apk, cat, 1, 1, 1)
            self.assertEqual(result['static_apk_structure'], 'PASS')
            self.assertFalse(result['device_fps_verified'])
            self.assertFalse(result['universal_ammo_refill_verified'])

    def test_reject_claimed_28_without_28(self):
        with tempfile.TemporaryDirectory() as d:
            apk, cat = create_fixture(Path(d))
            with self.assertRaisesRegex(AuditError, 'expected 28'):
                inspect(apk, cat)

    def test_reject_absent_model(self):
        with tempfile.TemporaryDirectory() as d:
            apk, cat = create_fixture(Path(d), missing_model=True)
            with self.assertRaisesRegex(AuditError, 'missing models'):
                inspect(apk, cat, 1, 1, 1)

    def test_reject_missing_reload_animation(self):
        with tempfile.TemporaryDirectory() as d:
            apk, cat = create_fixture(Path(d), missing_animation=True)
            with self.assertRaisesRegex(AuditError, 'missing declared animation clips'):
                inspect(apk, cat, 1, 1, 1)

    def test_reject_duplicate_configuration(self):
        with tempfile.TemporaryDirectory() as d:
            apk, cat = create_fixture(Path(d))
            cat['configurations'].append(cat['configurations'][0].copy())
            with self.assertRaisesRegex(AuditError, 'duplicate ids'):
                inspect(apk, cat, 1, 1, 2)

    def test_reject_zip_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            apk, cat = create_fixture(Path(d))
            cat['models'] = ['../bad.glb']
            with self.assertRaisesRegex(AuditError, 'unsafe asset path'):
                inspect(apk, cat, 1, 1, 1)

    def test_reject_unknown_weapon_config(self):
        with tempfile.TemporaryDirectory() as d:
            apk, cat = create_fixture(Path(d))
            cat['configurations'][0]['weapon'] = 'missing'
            with self.assertRaisesRegex(AuditError, 'unknown weapon'):
                inspect(apk, cat, 1, 1, 1)


if __name__ == '__main__':
    unittest.main()
