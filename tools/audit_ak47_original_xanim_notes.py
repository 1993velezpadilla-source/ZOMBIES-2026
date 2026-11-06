#!/usr/bin/env python3
"""Extract ONLY event metadata (never XANIM tracks) for owned COD4 AK reloads."""
from pathlib import Path
import argparse
import json
from iw3_xanim_v17 import load_xanim

KINDS=('viewmodel_ak47_reload','viewmodel_ak47_reload_empty')

def collect(root):
    allfiles=[p for p in root.rglob('*') if p.is_file()]
    result={}
    for name in KINDS:
        matches=[p for p in allfiles if p.stem.lower()==name]
        if not matches:
            raise FileNotFoundError('Original native XANIM missing: '+name)
        anims=[]
        for p in matches:
            anim=load_xanim(p)
            if anim.fps<1 or anim.frame_count<1 or anim.frame_count>250:
                raise ValueError('invalid source XANIM timeline')
            notes=[{'event':event,'frame':frame,
                    'second':round(frame/anim.fps,5)}
                   for event,frame in anim.notes]
            for e in notes:
                if e['frame']>anim.frame_count+1:
                    raise ValueError('out-of-range XANIM note: '+str(e))
            res={'name':name,'zone':next((part for part in p.parts if part in
                     ('common_mp','common','mp_crash')),'unknown'),
                 'file':p.name,'frames':anim.frame_count,'fps':anim.fps,
                 'duration_s':round(anim.frame_count/anim.fps,5),
                 'notetracks':notes}
            print('AUTHENTIC_COD4_RELOAD_XANIM_NOTETRACK',json.dumps(res,sort_keys=True),flush=True)
            anims.append(res)
        result[name]=anims
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('input',type=Path)
    ap.add_argument('output',type=Path)
    args=ap.parse_args()
    report={'original_source':'User owned COD4 original FastFile assets',
            'reload_animations':collect(args.input)}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
