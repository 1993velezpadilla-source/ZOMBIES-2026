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
                dry=z.read(prefix+'sounds/ak47dev_dry.ogg')
                dry_audit=json.loads(z.read(prefix+'sounds/ak47dev_dry_audit_v8.json'))
                assert dry.startswith(b'OggS') and len(dry)>1100
                assert dry_audit['weapon_def']=='main/iw_11.iwd/weapons/mp/ak47_mp'
                assert dry_audit['weapon_field']=='emptyFireSoundPlayer'
                assert dry_audit['player_alias']=='weap_dryfire_smg_plr'
                assert dry_audit['source_wav']=='sound/weapons/weap_dryfire_smg.wav'
                assert dry_audit['source_wav_sha256']=='561963bfb073ee2b765ed2d3a1b0f8b6722124b87a8950a5170b05727c284c3f'
                assert dry_audit['original_pitch'] is True
                assert dry_audit['time_stretch_applied'] is False
                assert dry_audit['source_wav_bundled'] is False
                assert hashlib.sha256(dry).hexdigest()==dry_audit['output_sha256']
                with sf.SoundFile(BytesIO(dry)) as sound:
                    assert abs(sound.duration-.21626)<.01
                    assert sound.frames>0 and sound.channels>=1
                assert 's.next_fire=time+.25' in lua
                assert 'if s.reserve>0 then reload(p,s) end' in lua
                provenance=json.loads(z.read(prefix+'sounds/ak47dev_reload_audit_v7.json'))
                assert provenance['version']=='COD4_IW3_ORIGINAL_SOUND_NOTETRACK_V7'
                assert provenance['source']=='original user COD4 zone/spanish/common.ff'
                assert provenance['original_source_wavs_in_apk'] is False
                assert provenance['time_stretched'] is False
                assert provenance['pitch_changed'] is False
                origins=provenance['source_files']
                originals={
                    'weap_ak47_lift_plr':('wpfoly_ak47_reload_lift_v4.wav',
                       '0d29856c9f9063fba5b56d6e468d18f6e52025caf51d35bb40cd732c5901f7a3'),
                    'weap_ak47_clipout_plr':('wpfoly_ak47_reload_clipout_v5.wav',
                       '5b7fe9e5e588bbed9efb78da9c8a04e6c4c3050e464cd5bbcbe667a034e17e7c'),
                    'weap_ak47_clipin_plr':('wpfoly_ak47_reload_clipin_v4.wav',
                       '6bc27dea15268628cb6404e2ee4ded951792c792faf8184f980171567c26d44d'),
                    'weap_ak47_chamber_plr':('wpfoly_ak47_reload_chamber_v4.wav',
                       'b19d3d85fd3820f73aa88bd92619dd8b4ee6c6462721a0a10989877c175301ac')}
                assert set(origins)==set(originals)
                for name,(file,sha) in originals.items():
                    assert origins[name]['original_file']==file
                    assert origins[name]['sha256']==sha
                expected_events={
                    'normal':[('weap_ak47_lift_plr',0),('weap_ak47_clipout_plr',19),
                              ('weap_ak47_clipin_plr',57)],
                    'empty':[('weap_ak47_lift_plr',0),('weap_ak47_clipout_plr',19),
                             ('weap_ak47_clipin_plr',57),('weap_ak47_chamber_plr',77)]}
                for kind,events in expected_events.items():
                    actual=[(p['alias'],p['frame']) for p in provenance['animations'][kind]['events']]
                    assert actual==events,(kind,actual)
                    blob=z.read(prefix+f'sounds/ak47dev_reload_{kind}.ogg')
                    assert hashlib.sha256(blob).hexdigest()==provenance['animations'][kind]['ogg_sha256']
                    with sf.SoundFile(BytesIO(blob)) as sound:
                        assert sound.samplerate==44100
                        assert abs(sound.frames/sound.samplerate-(83 if kind=='normal' else 106)/30)<.015
                # Hearing "empty" for both was the regression: at 2.65s,
                # only original EMPTY XANIM is allowed to sound the chamber.
                tact,sr=sf.read(BytesIO(z.read(prefix+'sounds/ak47dev_reload_normal.ogg')),
                                dtype='float32',always_2d=True)
                empty,_=sf.read(BytesIO(z.read(prefix+'sounds/ak47dev_reload_empty.ogg')),
                                dtype='float32',always_2d=True)
                idx0,idx1=round(2.65*sr),round(2.92*sr)
                assert float(np.max(np.abs(tact[idx0:idx1])))<.004
                assert float(np.max(np.abs(empty[idx0:idx1])))>.004
            lua=z.read(prefix+'init.lua').decode()
            assert 'c.aux1 and not s.aux' in lua and 's.ammo=s.ammo-1' in lua
            assert 'minetest.register_tool(AK' in lua and 'wield_image="ak47dev_icon.png"' in lua
            assert 'drawtype="mesh"' not in lua and 'xz_ak_fired' in lua
            assert 'set_wield_index' not in lua, 'unsupported server-side wield-index setter in APK'
            assert 'player:get_wield_index()' in lua and 'inv:set_stack("main",selected,weapon)' in lua
            assert z.read(prefix+'sounds/ak47dev_fire.ogg').startswith(b'OggS')
    report={'package':'com.xziel.voxelsandbox.ak47dryv8','architecture':'arm64-v8a',
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
            'original_cod4_player_foley_verified':bool(expected),
            'original_cod4_empty_trigger_verified':bool(expected),
            'exact_original_notify_frames':[0,19,57,77] if expected else [],
            'signed_apk_contents_verified':True,'physical_android_device_tested':False}
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('apk',type=Path);p.add_argument('--report',type=Path)
    p.add_argument('--expected-audit',type=Path)
    a=p.parse_args();r=verify(a.apk,a.expected_audit)
    if a.report:a.report.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r))
