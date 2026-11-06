"""Use the player's actual COD4 IW3 audio + raw XANIM notetracks.

NOT the two old fake whole-mag recordings. The owned common.ff carries FOUR
separately recorded foley samples: lift, clipout, clipin, chamber. Raw
viewmodel_ak47_reload and reload_empty XANIMs carry precise sound events.
Their authoritative event frame indices are 0,19,57 and additional 77 on
empty. Render two native-pitch OGGs; no time stretching.

This script runs ONLY inside a transient build runner with the source files
extracted from the user's own COD4 release. No original WAV bytes in git.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import soundfile as sf

from iw3_xanim_v17 import load_xanim

SOUNDS={
 'weap_ak47_lift_plr':('wpfoly_ak47_reload_lift_v4.wav',
        '0d29856c9f9063fba5b56d6e468d18f6e52025caf51d35bb40cd732c5901f7a3'),
 'weap_ak47_clipout_plr':('wpfoly_ak47_reload_clipout_v5.wav',
        '5b7fe9e5e588bbed9efb78da9c8a04e6c4c3050e464cd5bbcbe667a034e17e7c'),
 'weap_ak47_clipin_plr':('wpfoly_ak47_reload_clipin_v4.wav',
        '6bc27dea15268628cb6404e2ee4ded951792c792faf8184f980171567c26d44d'),
 'weap_ak47_chamber_plr':('wpfoly_ak47_reload_chamber_v4.wav',
        'b19d3d85fd3820f73aa88bd92619dd8b4ee6c6462721a0a10989877c175301ac'),
}
EXPECTED={
 'normal':('viewmodel_ak47_reload',83,
      [('weap_ak47_lift_plr',0),('weap_ak47_clipout_plr',19),('weap_ak47_clipin_plr',57)]),
 'empty':('viewmodel_ak47_reload_empty',106,
      [('weap_ak47_lift_plr',0),('weap_ak47_clipout_plr',19),
       ('weap_ak47_clipin_plr',57),('weap_ak47_chamber_plr',77)])
}
RATE=44100


def _original_sample_dir(root:Path):
    matches=[]
    for original in SOUNDS.values():
        samples=list(root.rglob(original[0]))
        if len(samples)!=1:
            raise ValueError(f'original COD4 {original[0]}: expected exactly one extracted WAV, got {len(samples)}')
        path=samples[0]
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=original[1]:
            raise ValueError('wrong/modified COD4 foley source '+str(path)+' got '+digest)
        matches.append(path)
    return dict(zip(SOUNDS,matches))


def _resample_only_rate(source:np.ndarray,rate:int,out_rate:int):
    """Change sample count for PCM sample rate; preserve *real time* + pitch."""
    if rate==out_rate:return source
    total=round(len(source)*out_rate/rate)
    times=np.arange(total,dtype=np.float64)/out_rate
    original=np.arange(len(source),dtype=np.float64)/rate
    return np.interp(times,original,source).astype(np.float32)


def _decode(original_path:Path,rate:int=RATE):
    audio,oldrate=sf.read(str(original_path),dtype='float32',always_2d=True)
    if oldrate<8000 or oldrate>192000 or not .05<len(audio)/oldrate<4:
        raise ValueError('original source WAV duration/rate invalid: '+str(original_path))
    mono=np.mean(audio,axis=1,dtype=np.float64).astype(np.float32)
    return _resample_only_rate(mono,oldrate,rate)


def _animation(root:Path,name:str):
    # Find only the original source, not retargeted glTF.
    matched=[p for p in root.rglob('*') if p.is_file() and p.stem.lower()==name]
    if len(matched)!=1:
        raise ValueError('expected exactly one original XANIM '+name+' got '+str(len(matched)))
    return load_xanim(matched[0])


def _render(samples,animation,events,frames):
    out=np.zeros(round(frames/animation.fps*RATE),dtype=np.float64)
    notes=[]
    for alias,frame in events:
        src=samples[alias]
        offset=round(frame/animation.fps*RATE)
        if offset>=len(out):
            raise ValueError('sound event begins beyond animation: '+alias)
        count=min(len(src),len(out)-offset)
        if count<len(src)-round(.04*RATE):
            raise ValueError('COD4 event clipped more than 40ms by animation: '+alias)
        out[offset:offset+count]+=src[:count].astype(np.float64)
        notes.append({'alias':alias,'frame':frame,'second':round(frame/animation.fps,5),
                      'source_duration':round(len(src)/RATE,5),'samples_kept':count})
    peak=np.max(np.abs(out))
    if not np.isfinite(peak) or peak<.005:
        raise ValueError('original COD4 audio mixed silence/corrupt source')
    # Only normalize headroom on complete mix; never slow, pitch-shift or cut.
    out=np.float32(out*(.94/max(.94,peak)))
    return out,notes


def prepare(audio_root:Path,xanim_root:Path,output:Path):
    output.mkdir(parents=True,exist_ok=True)
    originals=_original_sample_dir(audio_root)
    samples={alias:_decode(path) for alias,path in originals.items()}
    report={'source':'original user COD4 zone/spanish/common.ff',
            'version':'COD4_IW3_ORIGINAL_SOUND_NOTETRACK_V7',
            'sample_rate':RATE,'source_files':{},
            'animations':{},'original_source_wavs_in_apk':False,
            'time_stretched':False,'pitch_changed':False}
    for alias,path in originals.items():
        report['source_files'][alias]={'original_file':path.name,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'decoded_seconds':round(len(samples[alias])/RATE,5)}
    tracks={}
    for kind,(name,frames,expected_notes) in EXPECTED.items():
        anim=_animation(xanim_root,name)
        actual=[(event,frame) for event,frame in anim.notes if event in SOUNDS]
        if anim.fps!=30 or anim.frame_count!=frames or actual!=expected_notes:
            raise AssertionError('COD4 '+name+' events changed: '+repr((anim.fps,anim.frame_count,actual)))
        if any(event not in SOUNDS for event,_ in anim.notes):
            raise AssertionError('Unexpected unhandled sound notify on '+name+': '+repr(anim.notes))
        audio,notes=_render(samples,anim,actual,frames)
        outfile=output/f'ak47dev_reload_{kind}.ogg'
        sf.write(str(outfile),audio,RATE,format='OGG',subtype='VORBIS')
        duration=sf.info(str(outfile)).duration
        if abs(duration-frames/30)>.005:raise AssertionError('OGG/XANIM time mismatch')
        if outfile.stat().st_size<10000:raise AssertionError('source OGG suspiciously small')
        report['animations'][kind]={'name':name,'frames':frames,'fps':30,
            'duration_s':round(duration,5),'events':notes,
            'ogg_sha256':hashlib.sha256(outfile.read_bytes()).hexdigest(),
            'bytes':outfile.stat().st_size}
        tracks[kind]=audio
        print('TRUE_ORIGINAL_COD4_RELOAD_TRACK',kind,json.dumps(report['animations'][kind],sort_keys=True),flush=True)
    if 'weap_ak47_chamber_plr' in [x['alias'] for x in report['animations']['normal']['events']]:
        raise AssertionError('normal tactical reload mistakenly contains empty chamber click')
    if 'weap_ak47_chamber_plr' not in [x['alias'] for x in report['animations']['empty']['events']]:
        raise AssertionError('empty mag reload missing chamber click')
    # The first three native COD4 foley events are genuinely the SAME cues
    # on BOTH original animations. The empty-only CHAMBER at frame 77 is
    # the real acoustic difference: never lie that it is different base Foley.
    if not np.allclose(tracks['normal'][:round(2.5*RATE)],
                       tracks['empty'][:round(2.5*RATE)],atol=1.e-6):
        raise AssertionError('expected identical first 3 native event samples in both COD4 source timelines')
    # Compare event region near chamber in empty.
    if np.max(abs(tracks['empty'][round(2.6*RATE):round(2.85*RATE)]))<.001:
        raise AssertionError('no empty-only chamber noise on original timing')
    audit=output/'ak47dev_reload_audit_v7.json'
    audit.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('ORIGINAL_COD4_NOTETRACK_RELOAD_READY',str(audit),flush=True)
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--loaded',required=True,type=Path)
    ap.add_argument('--anims',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    a=ap.parse_args()
    prepare(a.loaded,a.anims,a.output)
