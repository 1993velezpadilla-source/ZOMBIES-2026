"""Two separately synchronized reload OGGs from our existing private sample.

Uses SoundFile + a NumPy phase vocoder to stretch temporal duration without
shifting the sound's pitch. No ffmpeg binary needed on GitHub Actions.
The two COD4 XANIM clocks are 83 frames and 106 frames at 30 FPS.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import soundfile as sf

DURATIONS={'normal':83/30, 'empty':106/30}
TOLERANCE=0.08

def stretch_channel(samples:np.ndarray, ratio:float, target_n:int) -> np.ndarray:
    """STFT phase vocoder: ratio = source length / output length."""
    nfft=2048;hop=512
    samples=np.pad(samples.astype(np.float64),(nfft,nfft))
    wnd=np.hanning(nfft)
    positions=np.arange(0,len(samples)-nfft+1,hop,dtype=int)
    spec=np.fft.rfft(np.stack([samples[p:p+nfft]*wnd for p in positions]),axis=1)
    phase_advance=2*np.pi*hop*np.arange(spec.shape[1])/nfft
    phase=np.angle(spec[0])
    steps=np.arange(0,len(spec)-1,ratio)
    out=np.zeros(int(len(steps)*hop+nfft),dtype=np.float64)
    weights=np.zeros_like(out)
    for i,t in enumerate(steps):
        left=int(t);a=t-left
        f0,f1=spec[left],spec[left+1]
        amp=(1-a)*np.abs(f0)+a*np.abs(f1)
        frame=np.fft.irfft(amp*np.exp(1j*phase),nfft)
        k=i*hop
        out[k:k+nfft]+=frame*wnd
        weights[k:k+nfft]+=wnd*wnd
        advance=np.angle(f1)-np.angle(f0)-phase_advance
        advance=(advance+np.pi)%(2*np.pi)-np.pi
        phase+=phase_advance+advance
    out/=np.maximum(weights,1e-4)
    # Trim initial pad (scaled duration) and enforce exact clip end.
    pad_out=int(nfft/ratio)
    clip=out[pad_out:pad_out+target_n]
    if len(clip)<target_n:clip=np.pad(clip,(0,target_n-len(clip)))
    return np.clip(clip,-.99,.99).astype('float32')

def prepare(mod:Path):
    folder=mod/'sounds'
    file=folder/'ak47dev_reload.ogg'
    if not file.is_file():raise FileNotFoundError(file)
    original,rate=sf.read(str(file),dtype='float32',always_2d=True)
    source_sec=len(original)/rate
    if abs(source_sec-2.318481)>.3:raise ValueError(f'unexpected reload source duration {source_sec}')
    result={'source_sec':source_sec,'variants':{}}
    for name,target_sec in DURATIONS.items():
        ratio=source_sec/target_sec
        target_n=int(round(target_sec*rate))
        stretched=np.column_stack([stretch_channel(original[:,channel],ratio,target_n)
                                   for channel in range(original.shape[1])])
        outfile=folder/f'ak47dev_reload_{name}.ogg'
        sf.write(str(outfile),stretched,rate,format='OGG',subtype='VORBIS')
        actual=sf.info(str(outfile)).duration
        if abs(actual-target_sec)>TOLERANCE:
            raise ValueError(f'{name}: {actual:.3f}s instead of {target_sec:.3f}s')
        if outfile.stat().st_size<10000:raise ValueError(f'{name}: very small file')
        result['variants'][name]={'seconds':round(actual,5),'animation_seconds':round(target_sec,5),
                                  'drift_seconds':round(actual-target_sec,5)}
    print('RELOAD_AUDIO_XANIM_SYNC: '+json.dumps(result,sort_keys=True))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mod',type=Path)
    prepare(p.parse_args().mod)
