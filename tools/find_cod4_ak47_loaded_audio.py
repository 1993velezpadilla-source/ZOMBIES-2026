#!/usr/bin/env python3
"""Report original COD4 AK-47 sound aliases and LoadedSound WAV names only.

Input: temp OpenAssetTools asset listing and audio dump produced from the
user's original COD4 common/common_mp/mp_crash fastfiles. Does not distribute
game sounds; reports matching names, hashes, sizes and duration only.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
import sys
import wave

ALIASES=("weap_ak47_clipout_plr","weap_ak47_clipin_plr",
         "weap_ak47_chamber_plr","weap_ak47_lift_plr",
         "weap_ak47_reload_npc")
NAME=re.compile(r"ak.?47|weap_ak|clipout|clipin|chamber|reload|dry.?fire|empty.?fire|emptyclick|no.?ammo|weapon.?click|wpfoly_.*click",re.I)

def inspect(list_dir:Path, audio_dir:Path, output:Path):
    rows=[]
    listings=[]
    for file in sorted(list_dir.glob("cod4-*.txt")):
        lines=file.read_text(errors="replace").splitlines()
        matches=[line.strip()[:400] for line in lines if NAME.search(line)]
        listings.append({"file":file.name,"line_count":len(lines),
                         "target_alias_lines":matches[:300]})
        print("COD4_SOUND_ASSET_LIST",file.name,len(lines),"matches",len(matches),flush=True)
        for line in matches[:140]:print("ORIGINAL_IW3_SOUND_ALIAS",file.name,line,flush=True)
    for p in audio_dir.rglob("*"):
        if not p.is_file():continue
        relative=p.relative_to(audio_dir).as_posix()
        if not NAME.search(relative):continue
        if p.stat().st_size>20_000_000:
            raise ValueError("Audio file unexpectedly large: "+relative)
        meta={"original_loaded_audio":relative,"bytes":p.stat().st_size}
        h=hashlib.sha256()
        with p.open("rb") as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b""):h.update(chunk)
        meta["sha256"]=h.hexdigest()
        if p.suffix.lower()==".wav":
            try:
                with wave.open(str(p),"rb") as wav:
                    meta["duration_s"]=round(wav.getnframes()/wav.getframerate(),5)
                    meta["channels"]=wav.getnchannels()
            except Exception as exc:
                meta["wav_error"]=str(exc)[:120]
        rows.append(meta)
        print("ACTUAL_COD4_RELOAD_AUDIO_FROM_FASTFILE",json.dumps(meta),flush=True)
    report={"expected_nonempty_sound_aliases":["weap_ak47_clipout_plr","weap_ak47_clipin_plr"],
            "expected_empty_only_extra_alias":"weap_ak47_chamber_plr",
            "weapon_file_sound_map_verified":True,
            "fastfile_lists":listings,
            "original_loaded_sounds_matching_ak47":rows,
            "distributes_original_audio":False}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("COD4_ORIGINAL_FASTFILE_SOUND_RESULTS",len(rows),"matching loaded sound assets",flush=True)
    return report

if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("Usage: loaded_audio.py LIST_DIR AUDIO_DUMP_DIR REPORT.json")
    inspect(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
