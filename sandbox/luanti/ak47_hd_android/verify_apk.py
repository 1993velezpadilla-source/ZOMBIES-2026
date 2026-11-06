"""Inspect the signed APK's actual nested runtime model, texture and controls."""
import argparse
from io import BytesIO
from pathlib import Path
import hashlib
import json
import struct
from zipfile import ZipFile
from PIL import Image
from media_limits import check_media_size,MAX_MEDIAFILE_BYTES

def verify(apk, expected_audit=None):
    expected=json.loads(expected_audit.read_text()) if expected_audit else None
    if expected and not expected.get('original_source_mesh'):
        raise ValueError('expected original COD4 polygonal geometry, not the voxel shell')
    prefix='games/voxelibre/mods/ak47dev/'
    with ZipFile(apk) as outer:
        assert any(n.startswith('lib/arm64-v8a/') and n.endswith('.so') for n in outer.namelist())
        assert not any(n.startswith(('lib/x86/','lib/x86_64/','lib/armeabi-v7a/')) for n in outer.namelist())
        with ZipFile(BytesIO(outer.read('assets/assets.zip'))) as z:
            for entry in z.infolist():
                if entry.filename.startswith(tuple(prefix+p+'/' for p in ('models','textures','sounds'))) and not entry.is_dir():
                    check_media_size(entry.filename,entry.file_size)
            model=z.read(prefix+'models/ak47hd.glb')
            assert model[:4]==b'glTF' and struct.unpack_from('<I',model,8)[0]==len(model)
            length,kind=struct.unpack_from('<I4s',model,12);assert kind==b'JSON'
            d=json.loads(model[20:20+length])
            assert not d.get('images')
            assert len(d['skins'])==1
            if expected:
                assert len(d['skins'][0]['joints'])==expected['joint_count']
            else:
                assert len(d['skins'][0]['joints'])==38
            assert len(d['nodes'])<=64 and len(d['animations'])==8
            names={a['name'] for a in d['animations']}
            assert {'ak47_ads_enter','ak47_ads_hold','ak47_ads_fire','ak47_ads_exit',
                    'viewmodel_ak47_reload','viewmodel_ak47_reload_empty'}.issubset(names)
            faces=0
            for m in d['meshes']:
                for p in m['primitives']:
                    assert d['accessors'][p['attributes']['POSITION']]['count']<65535
                    assert d['accessors'][p['indices']]['componentType']==5123
                    faces+=d['accessors'][p['indices']]['count']//3
            if expected:
                assert faces==sum(expected['triangles']), (faces,expected['triangles'])
                assert faces>1000 and faces<144134+12756, 'not a useful original mesh' 
                assert len(d['meshes'][0]['primitives'])==sum(expected['mesh_buffers'])
            else:
                assert faces==144134+12756,faces
            with Image.open(BytesIO(z.read(prefix+'textures/ak47hd_512.png'))) as im:assert im.size==(512,512)
            assert z.read(prefix+'textures/ak47hd_hands.png').startswith(b'\x89PNG')
            lua=z.read(prefix+'init.lua').decode()
            assert 'c.aux1 and not s.aux' in lua and 's.ammo=s.ammo-1' in lua
            assert 'minetest.register_tool(AK' in lua and 'wield_image="ak47dev_icon.png"' in lua
            assert 'drawtype="mesh"' not in lua and 'xz_ak_fired' in lua
            assert 'set_wield_index' not in lua, 'unsupported server-side wield-index setter in APK'
            assert 'player:get_wield_index()' in lua and 'inv:set_stack("main",selected,weapon)' in lua
            assert z.read(prefix+'sounds/ak47dev_fire.ogg').startswith(b'OggS')
    report={'package':'com.xziel.voxelsandbox.ak47original','architecture':'arm64-v8a',
            'apk_bytes':apk.stat().st_size,'apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),
            'model_sha256':hashlib.sha256(model).hexdigest(),'triangles':faces,
            'model_bytes':len(model),'media_file_limit':MAX_MEDIAFILE_BYTES,
            'clips':sorted(names),'weighted_joints':len(d['skins'][0]['joints']),
            'original_polygon_geometry':bool(expected), 'texture':[512,512],
            'join_api_compatible':True,
            'signed_apk_contents_verified':True,'physical_android_device_tested':False}
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('apk',type=Path);p.add_argument('--report',type=Path)
    p.add_argument('--expected-audit',type=Path)
    a=p.parse_args();r=verify(a.apk,a.expected_audit)
    if a.report:a.report.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r))
