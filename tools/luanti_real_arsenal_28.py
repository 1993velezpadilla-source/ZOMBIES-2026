#!/usr/bin/env python3
"""Produce REAL experimental first-person weapon/hands GLBs from owner's COD4.

This tool is designed for an ephemeral GitHub runner. The original model, bone
tracks and game meshes are NEVER committed or uploaded. A counted gun must have
a skinned source mesh, valid source XANIM clips and matching animation channels
in the resulting GLB. This DOES NOT assert usable first-person placement,
proper grip, ADS alignment, smooth mobile FPS, or commercial permission.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

# This pre-existing, tested native IW3 converter is provided by the checked-out
# private source pipeline via PYTHONPATH. No third-party game bytes in git.
from iw3_gltf_animation_bridge import attach, read_glb
from iw3_anim_correlation import read_nodes
from iw3_xanim_v17 import load_xanim

ACTIONS = {
    "idle": re.compile(r"(?:^|_)idle(?:_|$)", re.I),
    "ads": re.compile(r"(?:^|_)(?:ads|aim)(?:_|$)", re.I),
    "fire": re.compile(r"(?:^|_)(?:fire|shoot)(?:_|$)", re.I),
    "reload": re.compile(r"(?:^|_)reload(?:_|$)", re.I),
}
LOD0 = re.compile(r"_lod0\.glb$", re.I)
SKIP_PARTS = ("grenadier", "acog", "reflex", "scope", "silenced", "gold")
MAX_MODELS_PER_WEAPON = 24
MAX_ANIMS_PER_WEAPON = 80


def match(stem: str, aliases: list[str]) -> bool:
    s = stem.lower()
    if s.endswith(".xanim_bin"):
        s = s[:-len(".xanim_bin")]
    if s.endswith("_lod0"):
        s = s[:-len("_lod0")]
    return any(s == a or s.startswith(a + "_") for a in aliases)


def metadata_valid(path: Path, *, required=frozenset(ACTIONS)) -> bool:
    doc, _ = read_glb(path)
    return bool(doc.get("meshes")) and bool(doc.get("skins")) and all(
        any(a.get("name") == label and a.get("channels")
            for a in doc.get("animations", []))
        for label in required
    )


def choose_source(model_dir: Path, xanim_dir: Path, aliases: list[str], animation_aliases: list[str] | None = None):
    animation_aliases = animation_aliases or aliases
    models = sorted((p for p in model_dir.glob("*.glb") if
                     LOD0.search(p.name) and match(p.stem, aliases)),
                    key=lambda p:(sum(t in p.stem.lower() for t in SKIP_PARTS),
                                  len(p.name),p.name))[:MAX_MODELS_PER_WEAPON]
    animation_candidates = [
        p for p in sorted(xanim_dir.iterdir()) if p.is_file() and
        match(p.stem, animation_aliases)
    ][:MAX_ANIMS_PER_WEAPON] if xanim_dir.exists() else []
    if not models or not animation_candidates:
        return None, {"candidate_models":len(models),
                      "candidate_xanim":len(animation_candidates),
                      "missing":"source model or xanim"}
    decoded = {}
    errors = 0
    for p in animation_candidates:
        try:
            decoded[p] = load_xanim(p)
        except (ValueError, OSError, OverflowError):
            errors += 1
    candidates = []
    for model in models:
        try:
            joints = read_nodes(model)["joints"]
        except (ValueError, OSError, IndexError, KeyError):
            continue
        if not joints:
            continue
        chosen, overlap = {}, {}
        for action, regex in ACTIONS.items():
            options = []
            for p, x in decoded.items():
                if not regex.search(p.stem):
                    continue
                common = len(joints & {bone.name.casefold() for bone in x.bones})
                # Reject xanim with only unrelated root/weapon tag overlap.
                if common >= 2:
                    options.append((common, len(p.name), p.name, p))
            if options:
                options.sort(key=lambda x:(-x[0],x[1],x[2]))
                overlap[action] = options[0][0]
                chosen[action] = options[0][3]
        if len(chosen) == len(ACTIONS):
            candidates.append((min(overlap.values()),sum(overlap.values()),
                               len(joints),model,chosen,overlap))
    candidates.sort(key=lambda x:(-x[0],-x[1],-x[2],len(x[3].name)))
    diagnostics = {"candidate_models":len(models),
                   "candidate_xanim":len(animation_candidates),
                   "xanim_decode_errors":errors,
                   "compatible_source_pairs":len(candidates)}
    if not candidates:
        return None, diagnostics
    min_score,total,joints,model,animations,overlap = candidates[0]
    diagnostics.update({"source_model":model.name,
                        "minimum_common_bones":min_score,
                        "common_bones_by_action":overlap})
    return (model,animations), diagnostics


def build(original: Path, manifest: dict, destination: Path) -> dict:
    weapons = manifest.get("weapons", [])
    if len(weapons)!=28 or len({w["id"] for w in weapons})!=28:
        raise ValueError("requires 28 uniquely named source weapon identities")
    src = original/"common_mp"
    model_dir = src/"model_export"
    anim_dir = src/"xanim"
    hands = model_dir/"viewmodel_base_viewhands_lod0.glb"
    if not model_dir.is_dir() or not anim_dir.is_dir():
        raise FileNotFoundError("real COD4 model and XANIM dumps are missing")
    if not hands.is_file():
        raise FileNotFoundError("original COD4 viewhands source unavailable")
    destination.mkdir(parents=True,exist_ok=True)
    results = {}
    for w in weapons:
        id = w["id"]
        chosen, report = choose_source(model_dir,anim_dir,w["model_aliases"],
                                       w.get("animation_aliases"))
        report.update({"category":w["category"],
                       "source_glb_generated":False,
                       "source_hands_generated":False,
                       "android_gameplay_verified":False})
        if not chosen:
            results[id] = report
            continue
        model,animations = chosen
        out = destination/f"{id}_real_source_experimental.glb"
        hand_out = destination/f"{id}_hands_source_experimental.glb"
        try:
            gun_info = attach(model,animations,out)
            hand_info = attach(hands,animations,hand_out)
            # Read the bytes back from real generated files. An XANIM list alone
            # cannot pass this gate.
            valid_gun = metadata_valid(out)
            valid_hand = metadata_valid(hand_out)
            if not(valid_gun and valid_hand):
                raise ValueError("source XANIM clips missing actual GLB channels")
            report.update({
                "source_glb_generated":True, "source_hands_generated":True,
                "source_glb_bytes":out.stat().st_size,
                "source_hands_bytes":hand_out.stat().st_size,
                "gun_channel_counts":{k:v["channels"] for k,v in gun_info["tracks"].items()},
                "hand_channel_counts":{k:v["channels"] for k,v in hand_info["tracks"].items()},
                "animations_rig_compatible_structurally":True
            })
        except (OSError,ValueError,KeyError,IndexError) as error:
            report["error"] = str(error)[:250]
            out.unlink(missing_ok=True)
            hand_out.unlink(missing_ok=True)
        results[id] = report
    return {
        "game":"COD4 IW3", "target_unique_weapon_count":28,
        "weapon_source_animated_pair_count":sum(
            r["source_glb_generated"] and r["source_hands_generated"]
            for r in results.values()),
        "weapon_categories":dict(Counter(w["category"] for w in weapons)),
        "rendered_and_ads_calibrated":False,
        "android_runtime_playtested":False,
        "legal_to_publish_original_assets":False,
        "result":results
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dumps",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--private-output",type=Path,required=True)
    p.add_argument("--metadata",type=Path,required=True)
    a=p.parse_args()
    r=build(a.dumps,json.loads(a.manifest.read_text()),a.private_output)
    a.metadata.parent.mkdir(parents=True,exist_ok=True)
    a.metadata.write_text(json.dumps(r,indent=2)+"\n")
    print("ORIGINAL_COD4_28_PRIVATE_ANIMATED_VIEWMODELS",
          r["weapon_source_animated_pair_count"],
          "of 28; Android gameplay NOT proved; no binary published.")


if __name__=="__main__":
    main()
