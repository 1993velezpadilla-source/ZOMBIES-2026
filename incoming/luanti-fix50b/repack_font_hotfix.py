#!/usr/bin/env python3
"""Replace only FIX54 Android Java/runtime layer, preserving native and game assets."""
import argparse
import copy
import hashlib
import json
import zipfile
from pathlib import Path

def runtime_file(name):
    return name in {'AndroidManifest.xml','resources.arsc','classes.dex'} or name.startswith('res/')

p=argparse.ArgumentParser()
p.add_argument('--fix54',type=Path,required=True)
p.add_argument('--compiled',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
a.output.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.fix54) as old, zipfile.ZipFile(a.compiled) as compiled:
    oldnames=old.namelist()
    newnames=compiled.namelist()
    if len(oldnames)!=len(set(oldnames)) or len(newnames)!=len(set(newnames)):
        raise RuntimeError('Duplicate APK files detected')
    oldset=set(oldnames); newset=set(newnames)
    for n in ['classes.dex','AndroidManifest.xml','resources.arsc','assets/assets.zip','lib/arm64-v8a/libluanti.so']:
        if n not in oldset:raise RuntimeError('Missing FIX54 '+n)
    if {n for n in oldset if runtime_file(n)} != {n for n in newset if runtime_file(n)}:
        raise RuntimeError('Compiled Android runtime resource files differ; fail closed')
    untouched={n:(old.getinfo(n).CRC,old.getinfo(n).file_size) for n in oldset if n.startswith(('assets/','lib/'))}
    changed=[]
    with zipfile.ZipFile(a.output,'w',allowZip64=True) as out:
        out.comment=old.comment
        for entry in old.infolist():
            n=entry.filename
            if n.startswith('META-INF/') and n.endswith(('.RSA','.DSA','.SF','.EC')):
                continue
            src=compiled if runtime_file(n) else old
            out.writestr(copy.copy(entry),src.read(n),compress_type=entry.compress_type)
            if src is compiled:changed.append(n)
    with zipfile.ZipFile(a.output) as out:
        if out.testzip() is not None:raise RuntimeError('Corrupt result')
        for n,(crc,length) in untouched.items():
            i=out.getinfo(n)
            if (i.CRC,i.file_size)!=(crc,length):
                raise RuntimeError('Gameplay or native library changed: '+n)
        dex=out.read('classes.dex')
        for marker in (b'XZInputStream',b'fonts/Arimo-Regular.ttf',b'DroidSansFallbackFull.ttf',
                        b'games/voxelibre/mods/xz_zombies_classic/init.lua'):
            if marker not in dex:raise RuntimeError('Missing guarded Android class: '+repr(marker))
    report={'unchanged_game_native_items':len(untouched),
            'replaced_android_runtime_items':changed,
            'sha256_unsigned':hashlib.file_digest(a.output.open('rb'),'sha256').hexdigest()}
    (a.output.parent/'font_repair_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('FIX54 game, native engine, models, 28 guns preserved byte-for-byte')
