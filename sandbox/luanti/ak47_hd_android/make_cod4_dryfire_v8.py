"""Bake the exact original COD4 AK-47 EMPTY TRIGGER sound from user-owned common.ff.

COD4 AK47 MP weapon asset main/iw_11.iwd/weapons/mp/ak47_mp:
  emptyFireSoundPlayer = weap_dryfire_smg_plr
  emptyFireSound       = weap_dryfire_smg_npc
Player sound alias -> common.ff LoadedSound: sound/weapons/weap_dryfire_smg.wav
Original raw WAV SHA-256 verified in independent source audit.
No sound synthesized or changed in pitch/speed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import soundfile as sf
import numpy as np

ORIGINAL_WAV = 'weap_dryfire_smg.wav'
ORIGINAL_SHA = '561963bfb073ee2b765ed2d3a1b0f8b6722124b87a8950a5170b05727c284c3f'
PLAYER_ALIAS = 'weap_dryfire_smg_plr'
EXPECTED_SECONDS = 0.21626


def prepare(loaded_dir: Path, output_dir: Path) -> dict:
    original = list(loaded_dir.rglob(ORIGINAL_WAV))
    if len(original) != 1:
        raise FileNotFoundError(f'Original COD4 player dryfire WAV missing/ambiguous: {original}')
    source = original[0]
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_sha != ORIGINAL_SHA:
        raise ValueError(f'Wrong original COD4 empty-trigger sample: {source_sha}')
    original_samples, rate = sf.read(str(source), dtype='float32', always_2d=True)
    if not 8000 <= rate <= 192000:
        raise ValueError('Invalid COD4 empty trigger sound sample rate')
    if abs(len(original_samples)/rate - EXPECTED_SECONDS) > 0.01:
        raise ValueError('Incorrect original COD4 empty-trigger duration')
    if not np.all(np.isfinite(original_samples)):
        raise ValueError('Non-finite original COD4 dryfire audio')
    if np.max(np.abs(original_samples)) < .003:
        raise ValueError('Silent original COD4 empty trigger sound')
    # Retain original samplerate, number of samples and channels, preserve pitch.
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / 'ak47dev_dry.ogg'
    sf.write(str(dest), original_samples, rate, format='OGG', subtype='VORBIS')
    info = sf.info(str(dest))
    if abs(info.duration-len(original_samples)/rate) > .004:
        raise AssertionError('Dryfire sound duration changed during OGG encoding')
    if dest.stat().st_size < 1100:
        raise AssertionError('Invalid output OGG dryfire')
    report = {
        'source': 'user original COD4 zone/spanish/common.ff LoadedSound',
        'weapon_def': 'main/iw_11.iwd/weapons/mp/ak47_mp',
        'weapon_field': 'emptyFireSoundPlayer',
        'player_alias': PLAYER_ALIAS,
        'source_wav': 'sound/weapons/' + ORIGINAL_WAV,
        'source_wav_sha256': source_sha,
        'duration_seconds': round(info.duration, 5),
        'sample_rate': rate,
        'channels': info.channels,
        'source_samples': len(original_samples),
        'original_pitch': True,
        'time_stretch_applied': False,
        'output': dest.name,
        'output_sha256': hashlib.sha256(dest.read_bytes()).hexdigest(),
        'source_wav_bundled': False,
        'wav_total_bytes': source.stat().st_size,
    }
    (output_dir/'ak47dev_dry_audit_v8.json').write_text(
        json.dumps(report,sort_keys=True,indent=2)+'\\n')
    print('ORIGINAL_COD4_EMPTY_TRIGGER_READY ' + json.dumps(report,sort_keys=True), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--loaded',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    prepare(args.loaded,args.output)
