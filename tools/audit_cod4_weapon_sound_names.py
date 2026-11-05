#!/usr/bin/env python3
"""Read-only name-level audit of COD4 audio inside previously indexed original IWDs.

Do not copy/extract copyrighted sounds. This report infers likely events from names.
"""
import collections
import json
import re
from pathlib import Path

SOURCE = Path("docs/audit/c4-iwd-file-inventory.json")
OUT = Path("docs/audit/COD4_WEAPON_AUDIO_NAMES_20261105.md")

WEAPONS = {
  "AK-47": r"ak[ _-]?47",
  "AK-74u": r"ak[ _-]?74u?",
  "M4": r"(?<![a-z0-9])m4(?![a-z0-9])|m4a1",
  "M16": r"m16",
  "MP5": r"mp5",
  "P90": r"p90",
  "Uzi": r"uzi",
  "Skorpion": r"skorpion|skorp",
  "G36C": r"g36",
  "G3": r"(?<![a-z0-9])g3(?![a-z0-9])",
  "M14": r"m14",
  "M40A3": r"m40a3",
  "R700": r"r700|remington",
  "M21": r"m21",
  "Barrett": r"barrett|m82",
  "Dragunov": r"dragunov|svd",
  "M249": r"m249|saw",
  "M60": r"m60",
  "RPD": r"rpd",
  "W1200": r"w1200|winchester",
  "M1014": r"m1014|benelli",
  "USP": r"usp",
  "M9": r"m9(?![a-z0-9])|beretta",
  "M1911": r"1911|colt45",
  "Desert Eagle": r"desert[ _-]?eagle|deagle",
  "RPG": r"rpg",
  "Stinger": r"stinger",
  "MP40 (not COD4 stock)": r"mp40",
}
SIGNALS={
  "fire": r"fire|shoot|shot|gunshot|auto|burst|single|suppressed|silenc|unsupp",
  "reload": r"reload|magazine|mag_|_mag|clip|chamber|bolt|cock|slide|insert|eject",
  "handling": r"raise|lower|deploy|switch|ready|equip|putaway|fidget|pullout|pickup",
}
def normalized(path):
    return path.lower().replace("\\", "/")
def main():
    rows=json.loads(SOURCE.read_text(encoding="utf-8"))
    aud=[r for r in rows if Path(r["path"].lower()).suffix in {".wav",".mp3",".ogg",".flac"}]
    snd=[r for r in aud if normalized(r["path"]).startswith("sound/")]
    weapons_dir=[r for r in snd if normalized(r["path"]).startswith(("sound/weapons/", "sound/weapon/"))]
    sample_dir=collections.Counter("/".join(normalized(r["path"]).split("/")[:3]) for r in snd)
    checks={}
    for weapon,regex in WEAPONS.items():
        pattern=re.compile(regex, re.IGNORECASE)
        # Only match audio path itself: no duplicate container names.
        hits=[r for r in aud if pattern.search(normalized(r["path"]))]
        checks[weapon]={"total":len(hits)}
        for key,signal in SIGNALS.items():
            checks[weapon][key]=len([r for r in hits if re.search(signal, normalized(r["path"]))])
        checks[weapon]["samples"]=[r["path"] for r in hits[:4]]
    likely=re.compile(r"(fire|shot|shoot|reload|mag_|_mag|slide|bolt|silenc|unsupp|chamber|weapon|gun)",re.I)
    potential=[r for r in snd if likely.search(r["path"])]
    hints=[r["path"] for r in potential[:75]]
    lines=[
      "# COD4 original IWD sound filename audit (2026-11-05)","",
      "Read-only: no sound files are extracted, redistributed, or listened to.",
      "Only naming evidence from the previously verified original PC IWD inventory.",
      "Binary sound alias banks / FF assets may define events not visible in paths. Zero matches do not prove absence.","",
      f"- IWD files previously indexed: 22",
      f"- Total audio paths (WAV/MP3/OGG/FLAC): **{len(aud):,}**",
      f"- Under sound/: **{len(snd):,}**",
      f"- Under sound/weapons or sound/weapon: **{len(weapons_dir):,}**",
      f"- Weapon-like sound path names: **{len(potential):,}**","",
      "## Most common audio folders (sound/...)",
      "| Folder | Count |","|---|---:|",
      *[f"| `{k}` | {v} |" for k,v in sample_dir.most_common(35)],"",
      "## Explicit weapon tokens in filenames",
      "| Name | All matching audio files | Fire-ish names | Reload-ish names | Handling-ish |",
      "|---|---:|---:|---:|---:|",
      *[f"| {weapon} | {d['total']} | {d['fire']} | {d['reload']} | {d['handling']} |" for weapon,d in checks.items()],"",
      "## Examples for weapon matches (names only)",
      *[f"### {weapon}\n"+("\n".join("- `"+p+"`" for p in d["samples"]) if d["samples"] else "(No filename matches)")+"\n" for weapon,d in checks.items() if d["total"]],"",
      "## First 75 weapon-like filename paths",
      *[f"- `{x}`" for x in hints],"",
      "## Conclusion",
      "This is a filename-only audit, not a guarantee of complete fire/reload coverage per weapon.",
      "Original COD4 sounds remain proprietary, not commercial-use assets for our independent game.",""
    ]
    OUT.write_text("\n".join(lines),encoding="utf-8")
    print("COUNTS",json.dumps({"total_audio":len(aud),"sound_dir":len(snd),"weapon_dir":len(weapons_dir),"weaponish":len(potential)},ensure_ascii=False))
    print("TOP_AUDIO_FOLDERS",json.dumps(sample_dir.most_common(25),ensure_ascii=False))
    print("WEAPON_MATCHES",json.dumps({k:{a:b for a,b in v.items() if a!="samples"} for k,v in checks.items()},ensure_ascii=False))
    print("SAMPLE_WEAPON_AUDIO_FILENAMES",json.dumps(hints[:40],ensure_ascii=False))
    print("EXPLICIT_WEAPON_DIR_FILES",json.dumps([r["path"] for r in weapons_dir[:20]],ensure_ascii=False))
    print("GUN_SAMPLE_MATCHES",json.dumps({k:v["samples"] for k,v in checks.items() if v["total"]},ensure_ascii=False))
    print(f"Markdown report: {OUT}")

if __name__=="__main__":
    main()
