#!/usr/bin/env python3
"""Find ORIGINAL COD4 AK-47 tactical(nonempty)/empty reload source files in user's archive.

Read only, no game audio files are uploaded, committed, converted or distributed.
Reports precise IWD paths/sizes/SHAs and candidate IW3 alias names. Intended to
settle whether CoD4 exposes separate clips or layer-based sound aliases rather
than manufacturing a "normal" track from the same GunLib recording.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import zipfile

from audit_releases import SplitReader, SOURCE_ZIP_BYTES

PREFIX="Call of Duty 4 Modern Warfare/"
AUDIO={".wav",".mp3",".ogg",".wma"}
IWD_RE=re.compile(r"^main/(?:localized_[a-z]+_)?iw_\d{2}\.iwd$",re.I)
KEY=re.compile(r"ak.?47|ak.?_?47|weap_ak|reload|clipout|clipin|chamber|weapon|soundalias",re.I)
EXACT=re.compile(r"ak.?47|ak.?_?47|weap_ak",re.I)
RELOAD=re.compile(r"reload|clipout|clipin|chamber|mag(out|in)|magazine",re.I)

def filehash(fh,max_size:int):
    h=hashlib.sha256()
    n=0
    while True:
        b=fh.read(1024*1024)
        if not b:break
        n+=len(b)
        if n>max_size:raise ValueError("candidate file too large")
        h.update(b)
    return h.hexdigest()

def scan(parts_dir:Path,report_path:Path):
    parts=sorted(parts_dir.glob("C4-Mocs.zip.part-*"))
    if len(parts)!=4 or sum(x.stat().st_size for x in parts)!=SOURCE_ZIP_BYTES:
        raise ValueError("the owned 7GB COD4 release ZIP is missing/incomplete")
    src=SplitReader(parts)
    records=[]
    outer_candidates=[]
    stats=[]
    audio_index=[]
    ak47_weapon_defs=[]
    try:
        with zipfile.ZipFile(src) as outer:
            members={p.filename.removeprefix(PREFIX):p for p in outer.infolist()
                     if p.filename.startswith(PREFIX) and not p.is_dir()}
            iwds=sorted((name,m) for name,m in members.items() if IWD_RE.fullmatch(name))
            print("OWNED_COD4_ORIGINAL_ARCHIVE_FOUND",len(members),
                  "outer members and",len(iwds),"IWD archives",flush=True)
            for name,m in members.items():
                if not name.lower().endswith(".iwd") and KEY.search(name):
                    outer_candidates.append({"archive_path":name,"size":m.file_size})
            for relative,outer_member in iwds:
                with tempfile.TemporaryFile() as tmp:
                    # bounded extraction of only ONE IWD at a time; no 7GB local copy
                    copied=0
                    with outer.open(outer_member) as reader:
                        while b:=reader.read(4*1024*1024):
                            copied+=len(b)
                            if copied>450*1024*1024:
                                raise ValueError("IWD over safe per-file audit limit: "+relative)
                            tmp.write(b)
                    tmp.seek(0)
                    with zipfile.ZipFile(tmp) as z:
                        count=0; candidates=0; audio_count=0
                        found=[]
                        if relative=="main/iw_11.iwd":
                            for weapon in ("weapons/mp/ak47_mp","weapons/sp/ak47"):
                                if weapon in z.namelist():
                                    data=z.read(weapon).decode('latin1',errors='replace').replace('\x00','')
                                    tokens=data.split('\\')
                                    # Original IW3 weapon definitions are WEAPONFILE\\key\\value pairs.
                                    fields={}
                                    for k in range(1,len(tokens)-1,2):
                                        fields[tokens[k].strip()]=tokens[k+1].strip()
                                    selected={k:v[:350] for k,v in fields.items()
                                              if any(word in k.lower() for word in
                                                     ('reload','notetrack','clip','chamber','sound'))}
                                    ak47_weapon_defs.append({"source":relative+"/"+weapon,
                                                              "field_count":len(fields),
                                                              "fields":selected,
                                                              "text_head":data[:110]})
                                    print("ORIGINAL_AK47_WEAPON_FIELD_SOURCE",
                                          relative+"/"+weapon,flush=True)
                                    for key,value in selected.items():
                                        if "reload" in key.lower() or "notetrack" in key.lower() or "emptyfire" in key.lower() or "lastshot" in key.lower() or "fireSound" in key:
                                            print("AK47_ORIGINAL_DEF",key,repr(value[:210]),flush=True)
                        for item in z.infolist():
                            if item.is_dir():continue
                            count+=1
                            path=item.filename.replace("\\","/")
                            ext=Path(path).suffix.lower()
                            is_audio=ext in AUDIO
                            if is_audio:
                                audio_count+=1
                                audio_index.append({"iwd":relative,"path":path,"bytes":item.file_size})
                                if relative in ("main/iw_08.iwd","main/iw_10.iwd","main/iw_11.iwd") and (
                                    audio_count<=15 or re.search(r"weap|rifle|reload|ak47|clip|mag|cham",path,re.I)):
                                    print("AUDIO_FILE_INDEX",relative,path,flush=True)
                            # Categorize likely actual source AUDIO and alias config
                            relevance="AK47" if EXACT.search(path) else (
                                "reload_audio" if RELOAD.search(path) and is_audio else (
                                "aliases" if "soundalias" in path.lower() or
                                (path.lower().endswith(".csv") and
                                 "sound" in path.lower()) else None))
                            if relevance:
                                candidates+=1
                                row={"original_iwd":relative,
                                     "entry":path,"bytes":item.file_size,
                                     "type":relevance}
                                if is_audio and item.file_size<15*1024*1024:
                                    with z.open(item) as payload:
                                        row["sha256"]=filehash(payload,15*1024*1024)
                                found.append(row)
                        print("IWD_SCAN",relative,"all",count,"audio",audio_count,
                              "AK47/reload candidates",candidates,flush=True)
                        if found:
                            for row in found[:55]:
                                print("ORIGINAL_COD4_SOUND_CANDIDATE",
                                      relative,row["entry"],"size",row["bytes"],flush=True)
                        records.extend(found[:1000])
                        stats.append({"iwd":relative,"members":count,"audio":audio_count,
                                      "matched":candidates})
            print("AK47_ORIGINAL_IWD_CANDIDATE_TOTAL",len(records),flush=True)
    finally:
        src.close()
    report={"archive":"ZOMBIES-2026 release gofile-p2DdQHsz / C4-Mocs.zip",
            "ownership":"user-supplied original COD4 files",
            "status":"IWD filenames only; soundalias names are not proof of gameplay sound",
            "iwd_inventory":stats,"candidate_entries":records,
            "original_ak47_weapon_definitions":ak47_weapon_defs,
            "all_original_audio_paths":audio_index,
            "outer_candidates":outer_candidates[:100],
            "copyright_data_uploaded":False,
            "found_tactical_audio_files":[r for r in records if r["type"] in ("AK47","reload_audio")
                                            and Path(r["entry"]).suffix.lower() in AUDIO]}
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("ORIGINAL_COD4_TACTICAL_RELOAD_SEARCH_DONE",
          len(report["found_tactical_audio_files"]),"audio matches",flush=True)
    return report

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("Usage: find_cod4_ak47_reload_sound.py PARTS_DIR REPORT.json")
    scan(Path(sys.argv[1]),Path(sys.argv[2]))
