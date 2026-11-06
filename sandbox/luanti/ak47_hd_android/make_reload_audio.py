"""Synchronize the two supplied reload sound clips to native COD4 XANIM.

Uses licensed/test source audio already present in the private working mod.
Sound is STRETCHED with ffmpeg's atempo filter (preserves pitch), not simply
pitched down. Durations are sourced from IW3 weapon clocks: 83/30, 106/30.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess

SOURCE_SECONDS = 2.318481  # measured by ffprobe from bundled private mod audio
DURATIONS = {'normal': 83/30, 'empty': 106/30}
TOLERANCE = 0.09

def call(*args):
    return subprocess.run(args,check=True,capture_output=True,text=True).stdout

def duration(file):
    out=call('ffprobe','-v','error','-show_entries','format=duration',
             '-of','default=nw=1:nk=1',str(file))
    return float(out.strip())

def prepare(mod: Path):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise EnvironmentError('ffmpeg and ffprobe are required for original reload sound synchronization')
    folder=mod/'sounds'
    source=folder/'ak47dev_reload.ogg'
    if not source.exists(): raise FileNotFoundError(source)
    measured=duration(source)
    if abs(measured-SOURCE_SECONDS)>0.30:
        raise ValueError(f'original reload sample changed: {measured:.3f}s')
    report={'source_duration':measured,'variants':{}}
    for name,target in DURATIONS.items():
        output=folder/f'ak47dev_reload_{name}.ogg'
        tempo=measured/target
        # Apply pitch-preserving tempo scaling. apad + atrim assure the
        # timeline is long enough without smearing the final animation event.
        call('ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(source),
             '-filter:a',f'atempo={tempo:.8f},apad,atrim=duration={target:.6f}',
             '-c:a','libvorbis','-qscale:a','5',str(output))
        actual=duration(output)
        if abs(actual-target)>TOLERANCE:
            raise ValueError(f'{name} audio drift {actual:.3f}s vs animation {target:.3f}s')
        report['variants'][name]={'audio_sec':round(actual,5),'animation_sec':round(target,5),
                                 'drift_sec':round(actual-target,5),'path':output.name}
    print('RELOAD_AUDIO_XANIM_SYNC '+json.dumps(report,sort_keys=True))
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('mod',type=Path)
    prepare(ap.parse_args().mod)
