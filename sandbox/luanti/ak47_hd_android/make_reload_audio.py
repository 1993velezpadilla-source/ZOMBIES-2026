"""Two natural-pitch reload Foley sequences with *different* XANIM cue sheets.

There is only ONE CC0 AK magazine recording in the public GunLib source,
not two COD4 reload recordings. Never claim otherwise. We preserve its
decoded samples unchanged (no phase vocoder, no sample-rate shift).
Empty reload adds a separate, original-pitch CC0 AK mechanical bolt click.
Each final file is the exact native animation duration to make event timing
verifiable: 83 frames / 30 FPS and 106 frames / 30 FPS.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

FPS = 30
TIMELINES = {
    "normal": {"animation_frames":83, "magazine_onset_s":0.28, "bolt_onset_s":None},
    "empty": {"animation_frames":106, "magazine_onset_s":0.47, "bolt_onset_s":2.93},
}
EXPECTED_MAG_DURATION=2.318481

def clip_to_size(audio, frames):
    if len(audio)>frames:
        return audio[:frames]
    if len(audio)<frames:
        return np.pad(audio,((0,frames-len(audio)),(0,0)))
    return audio

def render_sequence(magazine:np.ndarray, bolt:np.ndarray, rate:int, kind:str):
    if kind not in TIMELINES: raise ValueError("unknown reload variant")
    spec=TIMELINES[kind]
    if rate<8000 or magazine.ndim!=2 or bolt.ndim!=2:
        raise ValueError("expected decoded multichannel PCM")
    channels=magazine.shape[1]
    if bolt.shape[1]!=channels:
        raise ValueError("reload and bolt channel mismatch")
    frames=int(round(spec['animation_frames']/FPS*rate))
    result=np.zeros((frames,channels),dtype=np.float64)
    def mix(source:np.ndarray, offset_s:float, gain:float):
        first=int(round(offset_s*rate))
        count=min(len(source),frames-first)
        if count<=0:raise ValueError("source sound begins after animation end")
        result[first:first+count] += source[:count]*gain
        return first,count
    mag_offset,mag_count=mix(magazine,spec['magazine_onset_s'],0.93)
    bolt_count=0
    if spec['bolt_onset_s'] is not None:
        _,bolt_count=mix(bolt,spec['bolt_onset_s'],0.85)
    # Avoid clipping, but no stretch / pitch shift / interpolation.
    peak=max(1.0,float(np.max(np.abs(result)))/0.96)
    result=np.float32(result/peak)
    return result,{
        'kind':kind,'magazine_offset_samples':mag_offset,
        'magazine_unchanged_samples':mag_count,
        'extra_bolt_samples':bolt_count,'animation_frames':spec['animation_frames'],
        'animation_seconds':round(frames/rate,5), 'gain_safety':round(1/peak,6),
        'pitch_unchanged':True, 'time_stretch_applied':False,
        'source_provenance':'CC0 GunLib ak47_reload.ogg + ak47_click.ogg'
    }

def prepare(mod:Path):
    folder=mod/'sounds'
    magfile=folder/'ak47dev_reload.ogg'
    boltfile=folder/'ak47dev_bolt.ogg'
    if not magfile.is_file() or not boltfile.is_file():
        raise FileNotFoundError('two existing CC0 components required: ak47dev_reload.ogg and ak47dev_bolt.ogg')
    magazine,rate=sf.read(str(magfile),dtype='float32',always_2d=True)
    bolt,bolt_rate=sf.read(str(boltfile),dtype='float32',always_2d=True)
    if rate!=bolt_rate:
        raise ValueError('source sample rates differ, do not silently resample pitch')
    seconds=len(magazine)/rate
    if abs(seconds-EXPECTED_MAG_DURATION)>.25:
        raise ValueError(f'AK source changed unexpectedly ({seconds:.3f}s)')
    report={'source_duration':seconds,'variants':{}}
    for kind in TIMELINES:
        result,evidence=render_sequence(magazine,bolt,rate,kind)
        outfile=folder/f'ak47dev_reload_{kind}.ogg'
        sf.write(str(outfile),result,rate,format='OGG',subtype='VORBIS')
        actual=sf.info(str(outfile)).duration
        if abs(actual-evidence['animation_seconds'])>.035:
            raise ValueError(f'{kind} sound/animation length mismatch: {actual:.4f}s')
        evidence.update({'encoded_duration':round(actual,5),'bytes':outfile.stat().st_size})
        if evidence['bytes']<9000:raise ValueError('unusually small OGG')
        report['variants'][kind]=evidence
    if report['variants']['normal']['extra_bolt_samples']!=0 or report['variants']['empty']['extra_bolt_samples']==0:
        raise AssertionError('empty-only bolt cue not correctly assigned')
    print('RELOAD_NATIVE_PITCH_CUES '+json.dumps(report,sort_keys=True))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mod',type=Path)
    prepare(parser.parse_args().mod)
