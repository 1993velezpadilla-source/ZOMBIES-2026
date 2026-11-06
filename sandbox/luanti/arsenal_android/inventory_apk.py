"""Read-only inventory of a real Luanti Android APK. Does not invent weapons."""
import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import struct
from zipfile import ZipFile


def scan(apk):
    apk=Path(apk)
    with ZipFile(apk) as outer:
        outer_names=outer.namelist()
        if 'assets/assets.zip' not in outer_names:
            raise ValueError('missing Luanti assets/assets.zip')
        with ZipFile(BytesIO(outer.read('assets/assets.zip'))) as z:
            files=z.namelist()
            models=[p for p in files if p.endswith('.glb')]
            model_info=[]
            for path in models:
                data=z.read(path)
                if len(data)<20 or data[:4]!=b'glTF':
                    raise ValueError(f'invalid GLB: {path}')
                version,total=struct.unpack_from('<II',data,4)
                length,kind=struct.unpack_from('<I4s',data,12)
                if version!=2 or total!=len(data) or kind!=b'JSON' or length+20>len(data):
                    raise ValueError(f'invalid GLB header: {path}')
                doc=json.loads(data[20:20+length].decode('utf-8'))
                model_info.append({
                    'path':path, 'bytes':len(data),
                    'mesh_count':len(doc.get('meshes',[])),
                    'animation_clips':[a.get('name','') for a in doc.get('animations',[])]
                })
            weapon_scripts=[]
            for path in files:
                if not path.startswith('games/voxelibre/mods/') or not path.endswith('/init.lua'):
                    continue
                if not any(t in path.lower() for t in ('ak47','arsenal','weapon')):
                    continue
                source=z.read(path).decode('utf-8','replace')
                declared=sorted(set(re.findall(r'\[([A-Z][A-Z0-9_]*)\]\s*=\s*\{\s*capacity\s*=',source)))
                names=sorted(set(re.findall(r'[A-Z][A-Z0-9_]*\s*=\s*["\']([a-z0-9_]+:[a-z0-9_]+)["\']',source)))
                weapon_scripts.append({
                    'path':path,
                    'explicit_definition_keys':declared,
                    'item_name_literals':names,
                    'register_tool_call_sites':source.count('minetest.register_tool(')
                })
    return {
        'filename':apk.name,
        'size_bytes':apk.stat().st_size,
        'sha256':sha256(apk.read_bytes()).hexdigest(),
        'nested_asset_entry_count':len(files),
        'glb_model_count':len(model_info),
        'glb_models':model_info,
        'weapon_code_signals':weapon_scripts,
        'arm64_libs':sorted(n for n in outer_names if n.startswith('lib/arm64-v8a/') and n.endswith('.so')),
        'weapon_audio_ogg_count':sum(x.startswith('games/voxelibre/mods/ak47dev/sounds/') and x.endswith('.ogg') for x in files),
        'limitations':[
            'Model variants are NOT independent weapons.',
            'Static inventory does not prove all weapon registration, firing or ADS.',
            'APK signature, device FPS, ammo crate and accessories require additional tests.',
            'Does not clear copyrighted assets for public distribution.'
        ]
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('apk',type=Path)
    p.add_argument('--report',type=Path)
    args=p.parse_args()
    result=scan(args.apk)
    output=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if args.report:
        args.report.write_text(output,encoding='utf-8')
    print(output,end='')


if __name__=='__main__':
    main()
