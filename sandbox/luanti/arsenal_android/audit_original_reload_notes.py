"""Audit ORIGINAL IW3 XANIM reload notetracks for each of the 28 weapons.

An original animation timing/alias plan is NOT an OGG audio export.
Do not swap empty-mag and tactical reload sounds or time-stretch whole
clips as a workaround. If distinct original notes cannot be demonstrated,
mark the sound as UNRESOLVED. No game assets leave the runner.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def source_match(stem, aliases):
    lower = stem.lower()
    return any(lower == alias.lower() or lower.startswith(alias.lower() + "_")
               for alias in aliases)


def _clip(paths, aliases, empty):
    candidates = []
    for path in paths:
        stem = path.stem.lower()
        if not source_match(stem, aliases):
            continue
        if empty:
            if "reload_empty" not in stem and "reloadempty" not in stem:
                continue
        else:
            if not (stem.endswith("_reload") or
                    stem.endswith("_reload_normal")):
                continue
        # Prefer shortest source clip to avoid attachment-specific variants
        candidates.append(path)
    return min(candidates, key=lambda p:(len(p.name),p.name)) if candidates else None


def _events(clip, decoder):
    if clip is None:
        return None
    animation = decoder(clip)
    fps = getattr(animation, "fps", None)
    frames = getattr(animation, "frame_count", None)
    if not isinstance(fps, int) or fps <= 0 or not isinstance(frames, int) or frames <= 0:
        raise ValueError("invalid actual IW3 XANIM duration")
    events = []
    for alias, frame in animation.notes:
        if not isinstance(alias, str) or not isinstance(frame, int) or frame < 0 or frame > frames:
            raise ValueError("invalid original source sound event")
        events.append({"alias":alias, "frame":frame, "second":round(frame/fps,5)})
    return {"animation":clip.name, "frames":frames, "fps":fps,
            "duration":round(frames/fps,5), "events":events}


def analyze(root: Path, manifest: dict, decoder) -> dict:
    weapons = manifest.get("weapons")
    if not isinstance(weapons, list) or len(weapons)!=28:
        raise ValueError("28 source weapon identities required")
    folder = root/"common_mp"/"xanim"
    if not folder.is_dir():
        raise FileNotFoundError("source original xanim/ folder is missing")
    paths = [p for p in folder.iterdir() if p.is_file()
             and p.suffix.lower()==".xanim_bin"]
    output = {}
    for weapon in weapons:
        aliases=weapon.get("model_aliases",[])
        normal=_clip(paths,aliases,False)
        empty=_clip(paths,aliases,True)
        record={"normal_found":normal is not None,
                "empty_found":empty is not None,
                "distinct_reload_verified":False,
                "sound_ogg_baked":False,
                "original_audio_wavs_verified":False}
        try:
            a=_events(normal,decoder)
            b=_events(empty,decoder)
            record.update({"normal":a, "empty":b})
            if a and b:
                an=[(n["alias"],n["frame"]) for n in a["events"]]
                bn=[(n["alias"],n["frame"]) for n in b["events"]]
                record["empty_only_notes"]=sorted(set(bn)-set(an))
                record["distinct_original_notetracks"]=a["duration"]!=b["duration"] or an!=bn
                record["distinct_reload_verified"]=bool(record["distinct_original_notetracks"])
        except (OSError,ValueError,OverflowError) as error:
            record["source_error"]=str(error)[:200]
        output[weapon["id"]]=record
    return {"expected_weapons":28,
            "both_original_reload_xanims_found":sum(
                r["normal_found"] and r["empty_found"] for r in output.values()),
            "native_sound_event_difference_confirmed":sum(
                r["distinct_reload_verified"] for r in output.values()),
            "actual_audio_rendered":False,
            "original_source_notetracks":output}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dumps",type=Path,required=True)
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    # Same verified decoder used in the historical AK47 V7 sound pass.
    from iw3_xanim_v17 import load_xanim
    r=analyze(a.dumps,json.loads(a.manifest.read_text()),load_xanim)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("SOURCE_28_RELOAD_NOTETRACK_COVERAGE",
          r["both_original_reload_xanims_found"],"/28;",
          "NATIVE_SOUND_DIFFERENCE",r["native_sound_event_difference_confirmed"],
          "/28; OGG RENDERED NO")


if __name__=="__main__":
    main()
