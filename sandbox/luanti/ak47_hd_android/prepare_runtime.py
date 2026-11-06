"""Build all private runtime assets from the existing native conversion."""
import argparse
from pathlib import Path
import numpy as np
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'iw3_blockstyle'))
from render_pose_sequence import PoseScene
from ads_pipeline import calibrate,bake,IDLE,UP,FIRE,verify_export
from export_viewmodel import export
from weapon_params import write_recoil_header

def prepare(blockstyle,weapon,out,*,original_geometry=False):
    out.mkdir(parents=True,exist_ok=True)
    rifle=blockstyle/'AK47_COD4_BLOCKSTYLE_ALL_XANIM_PRIVATE.glb'
    hands=blockstyle/'AK47_COD4_HANDSONLY_ALL_XANIM_PRIVATE.glb'
    block_r=PoseScene(rifle);block_h=PoseScene(hands)
    if original_geometry:
        rifle=blockstyle/'AK47_COD4_ORIGINAL_ALL_XANIM_PRIVATE.glb'
        hands=blockstyle/'AK47_COD4_ORIGINAL_HANDS_ALL_XANIM_PRIVATE.glb'
    r=PoseScene(rifle);h=PoseScene(hands)
    # The only allowed change is the geometry; native skin/joint animation
    # must match the already calibrated blockstyle motion at fixed source times.
    if original_geometry:
        for reference,source in ((block_r,r),(block_h,h)):
            for name in ('viewmodel_ak47_idle','viewmodel_ak47_reload','viewmodel_ak47_reload_empty'):
                if abs(reference.duration(name)-source.duration(name))>1e-6:
                    raise ValueError('original and block XANIM durations disagree')
                for t in (0.,source.duration(name)*.5,source.duration(name)):
                    old=reference.world(name,t);new=source.world(name,t)
                    if len(old)!=len(new) or max(float(np.max(np.abs(x-y))) for x,y in zip(old,new))>1e-5:
                        raise ValueError('native polygonal XANIM/coordinate mismatch: '+name)
    fields=weapon.read_text(encoding='latin-1').split('\\');fields=dict(zip(fields[1::2],fields[2::2]))
    duration={'hip':1.,'enter':float(fields['adsTransInTime']),'hold':1.,
              'fire':min(r.duration(FIRE),h.duration(FIRE)),'exit':float(fields['adsTransOutTime'])}
    config=calibrate(block_r,block_h);rd=out/'RIFLE_BAKED_PRIVATE.glb';hd=out/'HANDS_BAKED_PRIVATE.glb'
    bake(rifle,rd,hands=False,config=config,durations=duration)
    bake(hands,hd,hands=True,config=config,durations=duration)
    verify_export(r,h,PoseScene(rd),PoseScene(hd),{'calibration':config,'playback_durations':duration})
    report=export(rd,hd,out,original_geometry=original_geometry)
    write_recoil_header(weapon,out/'ak47_weapon_params.h')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--blockstyle',type=Path,required=True)
    p.add_argument('--weapon',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--original-source',action='store_true')
    a=p.parse_args();prepare(a.blockstyle,a.weapon,a.output,original_geometry=a.original_source)
