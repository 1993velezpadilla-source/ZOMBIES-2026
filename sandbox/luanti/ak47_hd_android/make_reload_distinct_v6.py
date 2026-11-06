"""V6: two truly DISTINCT, separately recorded rifle reload Foley sounds.

V5 was wrong: both files used GunLib ak47_reload.ogg, merely offset in time.
This module deliberately prohibits that. NORMAL gets an independent CC0
assault-rifle reload recording from SpringySpringo/OpenGameArt; EMPTY uses
the original CC0 GunLib AK-47 full magazine recording plus its bolt click.

Each sound is encoded at its NATURAL sample speed (no tempo/pitch shifting).
Output OGG length matches 83/30 and 106/30 seconds respectively.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen

import numpy as np
import soundfile as sf

from make_reload_audio import render_sequence as render_empty_sequence, TIMELINES

NORMAL_SOURCE_URL='https://opengameart.org/sites/default/files/assaultriflereload1_0.wav'
NORMAL_SOURCE_PAGE='https://opengameart.org/content/gun-reload-sounds'
NORMAL_AUTHOR='SpringySpringo'
NORMAL_LICENSE='CC0 1.0'
EMPTY_SOURCE_AUTHOR='serøutōnin--deprivəd / GunLib'
EMPTY_SOURCE_URL='https://raw.githubusercontent.com/Deases/GunLib/main/sounds/ak47_reload.ogg'
DURATIONS={'normal':83/30,'empty':106/30}
NORMAL_SOURCE_ENV='AK47_TACTICAL_NORMAL_WAV'
NORMAL_SOURCE_SHA256='efb2d724d634eabe6ba8d3065686abca848bb7497d4d43a5e4aed5e5ea23016f'
NORMAL_AUDIO_ONSET_S=.55  # place distinct 1.56s recording near mag manipulation
NATIVE_PEAK=0.98


def normal_source_bytes():
    """Download only the original, independently recorded NORMAL variant."""
    pinned=os.environ.get(NORMAL_SOURCE_ENV)
    if pinned:
        source=Path(pinned)
        data=source.read_bytes()
    else:
        request=Request(NORMAL_SOURCE_URL,headers={
            'User-Agent':'Mozilla/5.0 (compatible; private Luanti CC0 sound attribution test)',
            'Accept':'audio/wav,audio/x-wav,application/octet-stream,*/*'})
        with urlopen(request,timeout=45) as response:
            data=response.read(2_500_000)
    if len(data)<20_000 or len(data)>2_000_000 or data[:4]!=b'RIFF' or data[8:12]!=b'WAVE':
        raise ValueError('independent NORMAL CC0 sound was not a valid WAV; refusing to duplicate empty sound')
    digest=hashlib.sha256(data).hexdigest()
    if digest!=NORMAL_SOURCE_SHA256:
        raise ValueError('normal CC0 source WAV differs from pinned independent recording: '+digest)
    return data


def decoded_wav(data:bytes):
    from io import BytesIO
    samples,rate=sf.read(BytesIO(data),dtype='float32',always_2d=True)
    if len(samples)<int(rate*.4) or len(samples)>int(rate*12):
        raise ValueError('NORMAL WAV length out of plausible reload range')
    return samples,rate


def _peak_safe(data):
    peak=max(1.,float(np.max(np.abs(data)))/NATIVE_PEAK)
    return (data/peak).astype('float32')


def _fade_boundaries(data,rate):
    n=max(1,int(rate*.018))
    envelope=np.linspace(0.,1.,n,dtype=np.float32)
    data[:n]*=envelope[:,None]
    data[-n:]*=envelope[::-1,None]
    return data


def independent_normal(samples,rate):
    target=int(round(DURATIONS['normal']*rate))
    out=np.zeros((target,samples.shape[1]),dtype='float32')
    # There may be initial silence in the recorded airsoft reload.
    # Find the first substantial action. Trim dead air ONLY.
    loud=np.max(np.abs(samples),axis=1)
    threshold=max(.018,float(np.percentile(loud,98))*.10)
    activity=np.flatnonzero(loud>=threshold)
    onset=max(0,int(activity[0])-int(rate*.08)) if len(activity) else 0
    # The independent recording is 1.556s. Place it in the source 2.767s
    # tactical XANIM near magazine removal/insertion, with silent lead/tail.
    # Do not slow it down or shift pitch simply to fill the animation clock.
    first=int(round(NORMAL_AUDIO_ONSET_S*rate))
    chunk=samples[onset:onset+target-first]
    out[first:first+len(chunk)]=chunk
    _fade_boundaries(out,rate)
    return _peak_safe(out),{'original_start_seconds':round(onset/rate,5),
                           'animation_audio_onset_seconds':NORMAL_AUDIO_ONSET_S,
                           'source_duration_seconds':round(len(samples)/rate,5),
                           'played_source_frames':len(chunk),
                           'source_provenance':NORMAL_SOURCE_PAGE,
                           'source_name':'assaultriflereload1_0.wav',
                           'source_author':NORMAL_AUTHOR,'license':NORMAL_LICENSE,
                           'shared_source_with_empty':False,
                           'time_stretch_applied':False,'pitch_unchanged':True}


def _match_bolt_format(bolt,bolt_rate,mag,mag_rate):
    if mag_rate!=bolt_rate:
        desired=int(round(len(bolt)*mag_rate/bolt_rate))
        old=np.arange(len(bolt),dtype=np.float64)/bolt_rate
        new=np.arange(desired,dtype=np.float64)/mag_rate
        bolt=np.column_stack([np.interp(new,old,bolt[:,j])
                              for j in range(bolt.shape[1])]).astype('float32')
    if bolt.shape[1]!=mag.shape[1]:
        if bolt.shape[1]==1 and mag.shape[1]==2:bolt=np.repeat(bolt,2,axis=1)*.70710678
        elif bolt.shape[1]==2 and mag.shape[1]==1:bolt=bolt.mean(axis=1,keepdims=True)
        else:raise ValueError('unsupported bolt channel count')
    return bolt


def prepare(mod:Path):
    folder=mod/'sounds'
    wav=normal_source_bytes()
    original_wav_digest=hashlib.sha256(wav).hexdigest()
    normal_src,normal_rate=decoded_wav(wav)
    # The EMPTY sample is intentionally the GunLib AK AK reload used in V5.
    magpath=folder/'ak47dev_reload.ogg'
    boltpath=folder/'ak47dev_bolt.ogg'
    if not magpath.is_file() or not boltpath.is_file():
        raise FileNotFoundError('separate empty AK magazine/bolt recordings required')
    magazine,empty_rate=sf.read(str(magpath),dtype='float32',always_2d=True)
    bolt,bolt_rate=sf.read(str(boltpath),dtype='float32',always_2d=True)
    bolt=_match_bolt_format(bolt,bolt_rate,magazine,empty_rate)
    normal,n=independent_normal(normal_src,normal_rate)
    empty,e=render_empty_sequence(magazine,bolt,empty_rate,'empty')
    if n['source_provenance']==EMPTY_SOURCE_URL:
        raise ValueError('normal and empty reload source references must be different')
    if len(normal)!=round(DURATIONS['normal']*normal_rate):
        raise AssertionError('normal clip does not align with 83 XANIM frames')
    if len(empty)!=round(DURATIONS['empty']*empty_rate):
        raise AssertionError('empty clip does not align with 106 XANIM frames')
    # A check that catches exactly the V5 error, rather than merely checking
    # two different filenames, two different durations or an added bolt click.
    if original_wav_digest==hashlib.sha256(magpath.read_bytes()).hexdigest():
        raise ValueError('NORMAL audio equals EMPTY magazine sample')
    report={'source_normal':{'url':NORMAL_SOURCE_URL,'sha256':original_wav_digest,
                             'author':NORMAL_AUTHOR,'license':NORMAL_LICENSE},
            'source_empty':{'url':EMPTY_SOURCE_URL,'sha256':hashlib.sha256(magpath.read_bytes()).hexdigest(),
                            'author':EMPTY_SOURCE_AUTHOR,'license':'CC0'},
            'normal':n,'empty':e}
    for kind,pcm,sr in [('normal',normal,normal_rate),('empty',empty,empty_rate)]:
        filename=folder/f'ak47dev_reload_{kind}.ogg'
        sf.write(str(filename),pcm,sr,format='OGG',subtype='VORBIS')
        info=sf.info(str(filename))
        if abs(info.duration-DURATIONS[kind])>.04:raise ValueError(f'{kind}: sound/animation clock mismatch')
        if filename.stat().st_size<10_000:raise ValueError(f'{kind}: invalid compressed sound')
        report[kind].update({'duration_s':round(info.duration,5),'channels':info.channels,
                              'sample_rate':info.samplerate,'bytes':filename.stat().st_size})
    if report['normal']['source_name'].startswith('ak47_reload'):
        raise AssertionError('tactical uses old empty recording')
    (folder/'ak47dev_reload_audit_v6.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('TWO_INDEPENDENT_RELOAD_RECORDINGS_VERIFIED '+json.dumps(report,sort_keys=True))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mod',type=Path,nargs='?')
    parser.add_argument('--check-download',action='store_true')
    a=parser.parse_args()
    if a.check_download:
        data=normal_source_bytes()
        samples,rate=decoded_wav(data)
        print('INDEPENDENT_TACTICAL_WAV_READY '+json.dumps({
            'url':NORMAL_SOURCE_URL,'sha256':hashlib.sha256(data).hexdigest(),
            'bytes':len(data),'duration_s':len(samples)/rate,'rate':rate}))
    else:
        if a.mod is None:parser.error('mod directory required')
        prepare(a.mod)
