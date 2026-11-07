"""Restore original COD4 Beretta/M9 fire + distinct magazine Foley, not AK reuse.

Derived from owner-held COD4 common.ff. All seven genuine WAVs must match
the SHA-256 bytes previously verified in working Bridge V12. No proprietary
WAV/OGG is checked into GitHub; outputs stay in the private Android runner.
The two XANIM notetracks have DIFFERENT aliases and exact frame times.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import soundfile as sf

from make_original_cod4_reload_v7 import _decode, _animation, RATE

FILES={
 "weap_m9_fire_plr":("weap_beretta_slst_3c.wav",
       "09e57b78ec5a3b6a94b118ec378fa204b7a0b80213590f4c570dbd6c66829f3c"),
 "weap_dryfire_pistol_plr":("weap_dryfire_pistol.wav",
       "08dbc2a84b08cae7dd78e3ac79f26a77cdfe7e5c9499a4ff3950488e58cc0c61"),
 "weap_usp45sd_fire_plr":("weap_usp45sd_slst_y1.wav",
       "2914ee2a90b70299b889433e66ee66ba9504a37ab2ae52355008ead20b024c2c"),
 "weap_m9_clipout_plr":("wpfoly_beretta9mm_reload_clipout_v2.wav",
       "77bc604f8723971af68835e9d98f00d54581c9c5ced2c512aa11815fc9488810"),
 "weap_m9_clipin_plr":("wpfoly_beretta9mm_reload_clipin_v2.wav",
       "43b8e4f8e3360ce99158c0e657fe8a9e0a4997bd956e8d0402634fe051c0dbf4"),
 "weap_m9_chamber_plr":("wpfoly_beretta9mm_reload_chamber_v2.wav",
       "873f4ba5b42cbdbaa36b3bbaf7d3589c54db6a80668d81cab0c430571e6a437c"),
 "weap_usp45_clipin_plr":("wpfoly_usp_reload_clipin_v1.wav",
       "027816465b3f6df6d8f5bd41d919545d2052cbd50b2693f6b0a2acb9ec365e4d"),
}
NOTES={
 "normal": ("viewmodel_beretta_reload", 49,
            [("weap_m9_clipout_plr",9),("weap_m9_clipin_plr",32)]),
 "empty": ("viewmodel_beretta_reload_empty2",58,
           [("weap_m9_clipout_plr",7),("weap_usp45_clipin_plr",32),
            ("weap_m9_chamber_plr",44)]),
}

def original_samples(folder: Path) -> tuple[dict,dict]:
    sound={}
    evidence={}
    for alias,(filename,digest) in FILES.items():
        candidates=[p for p in folder.rglob(filename) if p.is_file()]
        if len(candidates)!=1:
            raise ValueError("Original COD4 M9 source WAV missing/ambiguous: "+filename)
        p=candidates[0]
        received=hashlib.sha256(p.read_bytes()).hexdigest()
        if received!=digest:
            raise ValueError("Original COD4 M9 WAV hash mismatch: "+filename)
        sample=_decode(p)
        sound[alias]=sample
        evidence[alias]={"filename":filename,"sha256":received,
                         "seconds":round(len(sample)/RATE,5)}
    return sound,evidence

def write_ogg(dest:Path,audio,report:dict):
    if not np.all(np.isfinite(audio)) or np.max(np.abs(audio))<.001:
        raise ValueError("source M9 audio silent or corrupt")
    dest.parent.mkdir(parents=True,exist_ok=True)
    sf.write(str(dest),audio,RATE,format="OGG",subtype="VORBIS")
    if dest.stat().st_size<2000:
        raise ValueError("source M9 OGG output empty")
    report[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()

def render_native_notes(samples:dict,anim,events:list[tuple[str,int]],frames:int):
    # The ORIGINAL M9 clip-in/chamber Foley ends AFTER the corresponding
    # 49/58-frame XANIM. Preserve every PCM sample; do not truncate, stretch,
    # or misrepresent the unchanged recorded pitch.
    full_size=max(round(frames/anim.fps*RATE),
        max(round(frame/anim.fps*RATE)+len(samples[alias])
            for alias,frame in events))
    mixed=np.zeros(full_size,dtype=np.float64)
    note_report=[]
    for alias,frame in events:
        offset=round(frame/anim.fps*RATE)
        data=samples[alias]
        mixed[offset:offset+len(data)]+=data
        note_report.append({"alias":alias,"frame":frame,
            "second":round(frame/anim.fps,5),
            "samples_kept":len(data)})
    peak=np.max(np.abs(mixed))
    if not np.isfinite(peak) or peak<.005:
        raise ValueError("Original M9 Foley mixed silence")
    mixed=np.float32(mixed*(.94/max(.94,peak)))
    return mixed,note_report


def build(loaded:Path,anims:Path,output:Path):
    tracks,evidence=original_samples(loaded)
    output.mkdir(parents=True,exist_ok=True)
    hashes={}
    for name,alias in [
        ("fire","weap_m9_fire_plr"),
        ("dry","weap_dryfire_pistol_plr"),
        ("silenced_fire","weap_usp45sd_fire_plr")]:
        wav=tracks[alias].astype(np.float32)
        write_ogg(output/f"arsenal_m9_{name}.ogg",wav,hashes)
    report={"source":"owner COD4 IW3 common.ff original LoadedSound",
            "time_stretched":False,"pitch_changed":False,
            "verified_original_wavs":evidence,"original_animations":{},
            "source_ogg_sha256":hashes}
    for kind,(clip,frames,events) in NOTES.items():
        anim=_animation(anims,clip)
        actual=[(alias,frame) for alias,frame in anim.notes if alias in FILES]
        if anim.fps!=30 or anim.frame_count!=frames or actual!=events:
            raise ValueError("M9 ORIGINAL "+clip+" XANIM notetrack mismatch")
        if len(actual)!=len(anim.notes):
            raise ValueError("M9 original XANIM contains unhandled sound event")
        track,notes=render_native_notes(tracks,anim,events,frames)
        out=output/f"arsenal_m9_reload_{kind}.ogg"
        write_ogg(out,track,hashes)
        report["original_animations"][kind]={"clip":clip,"frames":frames,
                "fps":anim.fps,"events":notes}
    if report["original_animations"]["normal"]["events"]==report["original_animations"]["empty"]["events"]:
        raise ValueError("M9 normal/empty sound tracks incorrectly identical")
    (output/"arsenal_m9_sound_audit.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("COD4_ORIGINAL_M9_REAL_RELOAD_AUDIO=YES",
          "NORMAL_VS_EMPTY_DISTINCT=YES","SOUND_FILES",len(hashes))
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--loaded",type=Path,required=True)
    p.add_argument("--anims",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    build(a.loaded,a.anims,a.output)

if __name__=="__main__":
    main()
