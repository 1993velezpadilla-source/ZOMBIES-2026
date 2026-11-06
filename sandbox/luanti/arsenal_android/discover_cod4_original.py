"""Fail-closed audit of original COD4 animated weapon source availability.

Inputs: private OAT model GLB exports and separate XANIM files.
No source/derived meshes, audio, textures or screenshot data leave this process.
Names and coarse counts alone do not demonstrate working in-game animation.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import struct
from collections import Counter

_LOD = re.compile(r"_lod[0-9]+$", re.I)
_ACTION = {
    "idle": (r"(^|_)(idle|stand|sprint_idle)($|_)",),
    "fire": (r"(^|_)(fire|shoot|shot)($|_)",),
    "reload": (r"(^|_)reload($|_)", r"(^|_)reload_(empty|quick)($|_)"),
    "ads": (r"(^|_)(ads|aim|raise)($|_)",),
}
_MAX_GLB_JSON = 32 * 1024 * 1024
_TAGS = ("viewhands", "viewmodel_base_viewhands")


def source_glb_metadata(path: Path) -> dict:
    with path.open("rb") as inp:
        h = inp.read(20)
        if len(h) != 20:
            raise ValueError(f"GLB truncated: {path}")
        magic, version, total, json_length, kind = struct.unpack("<4sIIII", h)
        if (magic != b"glTF" or version != 2 or total != path.stat().st_size
                or kind != 0x4E4F534A or json_length > _MAX_GLB_JSON
                or json_length % 4):
            raise ValueError(f"GLB corrupt: {path}")
        doc = json.loads(inp.read(json_length).decode("utf-8").strip())
        return {
            "meshes": len(doc.get("meshes", [])),
            "skins": len(doc.get("skins", [])),
            "animations_embedded": len(doc.get("animations", []))
        }


def normalized(stem: str) -> str:
    return _LOD.sub("", stem.lower())


def source_match(stem: str, aliases: list[str]) -> bool:
    stem = normalized(stem)
    return any(stem == a or stem.startswith(a + "_") for a in aliases)


def discover(root: Path, manifest: dict) -> dict:
    weapons = manifest.get("weapons")
    if (manifest.get("schema_version") != 1 or not isinstance(weapons, list)
            or len(weapons) != manifest.get("target_weapon_count")):
        raise ValueError("expected source-manifest contract invalid")
    ids = [x.get("id") for x in weapons]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate weapon ids")
    if not root.is_dir():
        raise FileNotFoundError(root)
    model_files = sorted(root.rglob("model_export/*.glb"))
    if not model_files:
        # OAT layout is zone/model_export/name.glb, some exporters use nested dirs.
        model_files = sorted(p for p in root.rglob("*.glb")
                             if "model_export" in p.parts)
    anim_files = sorted(
        p for p in root.rglob("*") if p.is_file() and
        "xanim" in p.parts and p.suffix.lower() in
        {".xanim_bin", ".xanim_export", ".anim", ".json"})
    entries = []
    bad_glb = []
    for item in weapons:
        aliases = [a.lower() for a in item["model_aliases"]]
        if not aliases or not all(a.startswith("viewmodel_") for a in aliases):
            raise ValueError("invalid original viewmodel candidate aliases")
        candidate_paths = [p for p in model_files if source_match(p.stem, aliases)]
        selected = []
        for path in candidate_paths[:16]:
            try:
                md = source_glb_metadata(path)
                selected.append({"source": path.relative_to(root).as_posix(), **md})
            except (ValueError, OSError, json.JSONDecodeError) as error:
                bad_glb.append({"file": path.relative_to(root).as_posix(),
                                "reason": str(error)[:160]})
        # No fake model selection: original mesh and skin must be real.
        chosen = next((x for x in selected if x["meshes"] > 0 and x["skins"] > 0), None)
        animations = sorted(
            p.relative_to(root).as_posix() for p in anim_files
            if source_match(p.stem, aliases))
        found_actions = {
            action: any(re.search(pattern, Path(p).stem.lower())
                        for pattern in patterns for p in animations)
            for action, patterns in _ACTION.items()
        }
        # A variant has NOT been animated, placed or tested simply because
        # its source XANIM exists separately from the source model.
        entries.append({
            "id": item["id"], "name": item["name"],
            "category": item["category"], "fire_mode": item["fire_mode"],
            "source_model_found": chosen is not None,
            "source_model_candidate": chosen["source"] if chosen else None,
            "source_models_found": len(selected),
            "xanim_files_found": len(animations),
            "source_xanim_categories": found_actions,
            "source_animation_coverage": all(found_actions.values()),
            "glb_animation_retargeted": False,
            "source_textures_verified": False,
            "source_sounds_verified": False,
            "luanti_runtime_implemented": False,
            "android_playtest_confirmed": False
        })
    skinned = sum(x["source_model_found"] for x in entries)
    coverage = sum(x["source_animation_coverage"] for x in entries)
    return {
        "game": "COD4 IW3 owner-supplied source", "manifest_target": len(weapons),
        "source_glb_files_scanned": len(model_files),
        "source_xanim_files_scanned": len(anim_files),
        "unique_weapon_identities_with_skinned_model": skinned,
        "unique_weapon_identities_with_xanim_name_coverage": coverage,
        "full_arsenal_playable": False,
        "model_errors": bad_glb[:20],
        "categories": dict(Counter(x["category"] for x in entries)),
        "weapons": entries,
        "notice": "This scan establishes ORIGINAL source evidence only. External XANIM names are not embedded animation clips. Never upload asset binaries in public artifacts."
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--dumps", required=True, type=Path)
    cli.add_argument("--manifest", required=True, type=Path)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--require-source", type=int, default=0)
    args = cli.parse_args()
    data = discover(args.dumps, json.loads(args.manifest.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(f"COD4_REAL_SOURCE_GATE: {data['unique_weapon_identities_with_skinned_model']}/"
          f"{data['manifest_target']} skinned models; "
          f"{data['unique_weapon_identities_with_xanim_name_coverage']}/"
          f"{data['manifest_target']} XANIM filename groups. "
          "REAL ANDROID PLAYABLE: NO.")
    if data["unique_weapon_identities_with_skinned_model"] < args.require_source:
        cli.exit(2, "COD4_REAL_SOURCE_GATE: insufficient source models\n")


if __name__ == "__main__":
    main()
