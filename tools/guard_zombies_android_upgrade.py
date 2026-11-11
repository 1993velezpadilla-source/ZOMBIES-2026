#!/usr/bin/env python3
"""Fail closed before shipping a Luanti-based Android upgrade.

Check the native COD4 viewmodel bridge and Android's asset update condition.
Use before signing or uploading every new APK.
"""
import argparse
import zipfile

CRITICAL_NATIVE_MARKERS = (
    b'[weapon_bridge]',
    b'ak47_hip_idle',
    b'getWeaponCrosshairOpacity',
    b'isAK47Aiming',
)
GAME_MOD='games/voxelibre/mods/xz_zombies_classic/init.lua'


def assess(baseline: str, candidate: str):
    with zipfile.ZipFile(baseline) as old, zipfile.ZipFile(candidate) as new:
        errors=[]
        old_names=set(old.namelist()); new_names=set(new.namelist())
        if old_names!=new_names:
            errors.append(f'Android entry set changed without explicit review: old={len(old_names)} new={len(new_names)}')
        native = new.read('lib/arm64-v8a/libluanti.so')
        for marker in CRITICAL_NATIVE_MARKERS:
            if marker in old.read('lib/arm64-v8a/libluanti.so') and marker not in native:
                errors.append('Missing original COD4 native feature: '+marker.decode())
        if new.getinfo('assets/assets.zip').CRC != old.getinfo('assets/assets.zip').CRC:
            # The original Java MainActivity only extracts updated assets when
            # BuildConfig.VERSION_CODE differs or existing installation is invalid.
            if new.read('AndroidManifest.xml')==old.read('AndroidManifest.xml'):
                errors.append('Changed bundled assets but same Android manifest/versionCode')
            if new.read('classes.dex')==old.read('classes.dex'):
                errors.append('Changed bundled assets but same Java BuildConfig.VERSION_CODE; cached game files may persist')
        return errors

if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('known_good_apk'); a.add_argument('candidate_apk'); args=a.parse_args()
    bad=assess(args.known_good_apk,args.candidate_apk)
    if bad:
        print('BLOCK RELEASE: '+str(len(bad))+' critical regressions')
        for issue in bad: print(' - '+issue)
        raise SystemExit(1)
    print('PASS: native COD4 compatibility and Android asset-update conditions')