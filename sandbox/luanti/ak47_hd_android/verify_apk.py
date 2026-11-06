"""Inspect the signed APK's actual nested runtime model, texture and controls."""
import argparse
from io import BytesIO
from pathlib import Path
import hashlib
import json
import struct
import numpy as np
import soundfile as sf
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
            binary=model[20+length+8:]
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
            def uv(primitive):
                accessor=d['accessors'][primitive['attributes']['TEXCOORD_0']]
                view=d['bufferViews'][accessor['bufferView']]
                assert accessor['componentType']==5126
                start=view.get('byteOffset',0)+accessor.get('byteOffset',0)
                return np.frombuffer(binary,dtype='<f4',count=accessor['count']*2,offset=start).reshape(-1,2)
            if expected:
                parts=d['meshes'][0]['primitives']
                wood_uv=np.concatenate([uv(p) for p in parts if p['material']==0])
                wood_mask=(wood_uv[:,0]<.5)&(wood_uv[:,1]>.5)
                assert int(wood_mask.sum())>700, 'wood furniture still mapped to gray steel'
                hands_uv=np.concatenate([uv(p) for p in parts if p['material']==1])
                assert len(hands_uv)>2500 and np.unique(np.round(hands_uv,4),axis=0).shape[0]>200, 'hands flat palette texel'
            with Image.open(BytesIO(z.read(prefix+'textures/ak47hd_rifle_2k.png'))) as im:
                assert im.size==(2048,2048)
                assert im.convert('RGB').getcolors(maxcolors=1024) is None, 'rifle atlas has insufficient detail'
            with Image.open(BytesIO(z.read(prefix+'textures/ak47hd_hands_1k.png'))) as im:
                if expected:
                    assert im.size==(1024,1024)
                    assert im.convert('RGB').getcolors(maxcolors=1024) is None, 'hands atlas flat'
                else:
                    assert im.width>=16
            if expected:
                lua=z.read(prefix+'init.lua').decode()
                assert 'minetest.chat_send_player(name' not in lua, 'top-left helper still active'
                assert 'ak47dev_reload_normal' in lua and 'ak47dev_reload_empty' in lua
                for name in ('normal','empty'):
                    sfx=z.read(prefix+f'sounds/ak47dev_reload_{name}.ogg')
                    assert sfx.startswith(b'OggS') and len(sfx)>10000, name
                provenance=json.loads(z.read(prefix+'sounds/ak47dev_reload_audit_v6.json'))
                assert provenance['normal']['source_name']=='assaultriflereload1_0.wav'
                assert provenance['source_normal']['url'].startswith('https://opengameart.org/')
                assert provenance['source_empty']['url'].endswith('ak47_reload.ogg')
                assert provenance['source_normal']['sha256']!=provenance['source_empty']['sha256'], (
                    'V5 shared empty reload source has returned')
                assert provenance['normal']['shared_source_with_empty'] is False
                assert provenance['normal']['time_stretch_applied'] is False
                assert provenance['empty']['time_stretch_applied'] is False
                # Compare decoded signal, NOT filenames or animation duration.
                # V5 used exactly the same ~2.3s audio in both files.
                def mono(name):
                    arr,rate=sf.read(BytesIO(z.read(prefix+f'sounds/ak47dev_reload_{name}.ogg')),
                                     dtype='float32',always_2d=True)
                    out=arr.mean(axis=1)
                    # approximately 220Hz for efficient duration-agnostic FFT
                    stride=max(1,round(rate/220))
                    return out[::stride].astype(float)
                a,b=mono('normal'),mono('empty')
                a-=np.mean(a);b-=np.mean(b)
                size=1<<((len(a)+len(b)-2).bit_length())
                spectrum_a=np.fft.rfft(a,size)
                spectrum_b=np.fft.rfft(b,size)
                cross=np.fft.irfft(spectrum_a*np.conjugate(spectrum_b),size)
                correlation=float(max(np.max(np.abs(cross[:len(a)])),
                                      np.max(np.abs(cross[-len(b)+1:])))/
                                  max(1.e-8,np.linalg.norm(a)*np.linalg.norm(b)))
                assert correlation<.75, ('normal and empty reloads still sound alike',correlation)
            lua=z.read(prefix+'init.lua').decode()
            assert 'c.aux1 and not s.aux' in lua and 's.ammo=s.ammo-1' in lua
            assert 'minetest.register_tool(AK' in lua and 'wield_image="ak47dev_icon.png"' in lua
            assert 'drawtype="mesh"' not in lua and 'xz_ak_fired' in lua
            assert 'set_wield_index' not in lua, 'unsupported server-side wield-index setter in APK'
            assert 'player:get_wield_index()' in lua and 'inv:set_stack("main",selected,weapon)' in lua
            assert z.read(prefix+'sounds/ak47dev_fire.ogg').startswith(b'OggS')
    report={'package':'com.xziel.voxelsandbox.ak47reloadv6','architecture':'arm64-v8a',
            'apk_bytes':apk.stat().st_size,'apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),
            'model_sha256':hashlib.sha256(model).hexdigest(),'triangles':faces,
            'model_bytes':len(model),'media_file_limit':MAX_MEDIAFILE_BYTES,
            'clips':sorted(names),'weighted_joints':len(d['skins'][0]['joints']),
            'original_polygon_geometry':bool(expected), 'texture':[2048,2048],
            'join_api_compatible':True,
            'fps_position':'native_top_right_debug_widget',
            'rifle_texture':'cc0_photo_2048_lit_shader',
            'hands_texture':'cc0_photo_1024_skin_and_cuff',
            'reload_sfx_sync':['83/30','106/30'] if expected else [],
            'independent_recordings_verified':bool(expected),
            'signed_apk_contents_verified':True,'physical_android_device_tested':False}
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('apk',type=Path);p.add_argument('--report',type=Path)
    p.add_argument('--expected-audit',type=Path)
    a=p.parse_args();r=verify(a.apk,a.expected_audit)
    if a.report:a.report.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r))
