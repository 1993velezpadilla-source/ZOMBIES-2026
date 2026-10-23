#!/usr/bin/env python3
"""Static inspection of launch references and expected external COD4 content.
Read-only. Does not load, execute, patch, or bypass any software.
"""
import json
import re
import zipfile
from pathlib import Path
from collections import Counter

APK=Path("_release_assets/cod4/COD4.apk")
OUT=Path("docs/audit")
OUT.mkdir(parents=True,exist_ok=True)

CATEGORIES={
    "game_data":["main/","zone/","iw_","localized_","mod.ff",".iwd",".ff",".pak","basepath","fs_basepath","fs_homepath","fs_game","cod4x","raw/"],
    "filesystem":["/storage/","/sdcard/","Android/data/","Android/obb/","getexternalfilesdir","getexternalstoragedirectory","/data/user/","/data/data/","filesdir","externalstoragedir","storage/emulated","SAF","documentfile","assets/"],
    "graphics":["vulkan","opengl","egl","gles","angle","turnip","panvk","adreno","mali","renderer","driver","vk_"],
    "controls":["touch","joystick","gamepad","mouse","gyroscope","gyro","inputevent","keycode","ads","aim","move_forward","cg_fov","sensitivity","reload","crouch","sprint"],
    "game_modes":["singleplayer","campaign","multiplayer","zombie","nacht","perk","mp_","sp_","dedicated","server"],
}
# Keep only entries relevant to the requested path/port compatibility audit.
BAD=re.compile(r"(api[_-]?key|bearer |authorization|password|secret|token|https?://)",re.I)
ASCII=re.compile(rb"[\x20-\x7e]{8,280}")
UTF16=re.compile(rb"(?:[\x20-\x7e]\x00){8,180}")

def inspect(data):
    groups={k:[] for k in CATEGORIES}
    seen={k:set() for k in CATEGORIES}
    # This is a string-existence audit: entries are not proof of reachable behavior.
    for pat,enc in ((ASCII,"ascii"),(UTF16,"utf-16-le")):
        for m in pat.finditer(data):
            raw=m.group(0)
            try:
                value=raw.decode(enc).strip()
            except UnicodeDecodeError:
                continue
            low=value.lower()
            if BAD.search(value) or len(value)>200:
                continue
            # Trim printable binary concatenations; keep bounded representative samples.
            for k,terms in CATEGORIES.items():
                if any(t.lower() in low for t in terms):
                    if value not in seen[k]:
                        seen[k].add(value)
                        if len(groups[k])<1000:
                            groups[k].append(value)
    return {k: sorted(v,key=lambda s:s.lower())[:220] for k,v in groups.items()}

def main():
    results={}
    with zipfile.ZipFile(APK) as z:
        for i in z.infolist():
            name=i.filename
            if name=="classes.dex" or name.startswith("lib/arm64-v8a/") and name.endswith(".so"):
                print("Scanning",name,i.file_size,flush=True)
                d=z.read(i)
                found=inspect(d)
                results[name]={"bytes":len(d),"hit_counts":{k:len(v) for k,v in found.items()},"samples":found}
    (OUT/"apk-runtime-strings.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n")
    lines=[
        "# COD4.apk — runtime path and feature reference audit",
        "",
        "Read-only inspection of printable strings in `classes.dex` and native Android `.so` files. "
        "**A string match is evidence of a literal being present in compiled binary data, not proof the feature works.**",
        "",
        "| Binary | Bytes | Game content path refs | Storage refs | Graphics refs | Controls refs | Modes refs |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name,v in results.items():
        c=v["hit_counts"]
        lines.append(f"| `{name}` | {v['bytes']:,} | {c['game_data']} | {c['filesystem']} | {c['graphics']} | {c['controls']} | {c['game_modes']} |")
    lines += ["","## External storage and game data strings (candidate references, not verified runtime paths)"]
    for name,v in results.items():
        matches=v["samples"]["filesystem"]+v["samples"]["game_data"]
        if matches:
            lines += [f"### `{name}`"]
            for m in matches[:60]:
                lines.append(f"- `{m.replace(chr(96), chr(39))}`")
    lines += ["", "## Limitations",
              "- Native dynamic behavior, function call graphs and actual file lookups are NOT tested.",
              "- Strings may include errors, log labels, debug-only code, and unused legacy data.",
              "- Download and archive validation do not establish APK safety or rights to redistribute proprietary game assets.",
              "- Do not treat a Windows install archive as a ready-made Godot project or assume asset path compatibility.",
              "- Full machine-readable match list: [apk-runtime-strings.json](apk-runtime-strings.json)."]
    (OUT/"APK_RUNTIME_AUDIT.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({name:v["hit_counts"] for name,v in results.items()},indent=2),flush=True)
if __name__=="__main__":
    main()
