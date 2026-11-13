#!/usr/bin/env python3
"""FIX57 preflight: verify a LEGALLY ACQUIRED Dremorn GLB works with Luanti 5.18.

No third-party assets are bundled, transformed, uploaded, or emitted by this tool.
The JSON report contains only model metadata and no model bytes.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

REQUIRED = {"idle1", "walk", "run", "atack1", "atack2", "death1"}
HEADER = b"glTF"


def inspect(path):
    with open(path, "rb") as f:
        header = f.read(12)
        if len(header) != 12 or header[:4] != HEADER:
            raise ValueError("Not a binary glTF (.glb) file")
        _, version, total = struct.unpack("<4sII", header)
        if version != 2 or total != path.stat().st_size:
            raise ValueError("Invalid glTF2 version or file length")
        json_data = None
        while f.tell() < total:
            chunk_header = f.read(8)
            if len(chunk_header) != 8:
                raise ValueError("Truncated GLB chunk header")
            size, kind = struct.unpack("<I4s", chunk_header)
            if size % 4 or size > total - f.tell():
                raise ValueError("Corrupted GLB chunk length")
            if kind == b"JSON":
                if json_data is not None:
                    raise ValueError("Duplicate GLB JSON chunk")
                json_data = json.loads(f.read(size).decode("utf-8").rstrip(" \t\r\n\x00"))
            else:
                f.seek(size, 1)
        if not isinstance(json_data, dict):
            raise ValueError("GLB missing valid JSON scene")
    skins = json_data.get("skins", [])
    meshes = json_data.get("meshes", [])
    nodes = json_data.get("nodes", [])
    animations = json_data.get("animations", [])
    if not skins or not meshes:
        raise ValueError("Model has no rig/skins or no mesh; static OBJ conversion is not enough")
    if not any(isinstance(node, dict) and "skin" in node for node in nodes):
        raise ValueError("GLB skin exists but is not bound to a scene node")
    names = [anim.get("name", "") for anim in animations]
    missing = sorted(REQUIRED.difference(names))
    if missing:
        raise ValueError("Required Dremorn named tracks missing: " + ", ".join(missing)
                         + "; found " + ", ".join(names))
    if len(set(names)) != len(names):
        raise ValueError("Duplicate GLB animation names; cannot safely address tracks by name")
    durations = {}
    accessors = json_data.get("accessors", [])
    for anim in animations:
        lows, highs = [], []
        for sampler in anim.get("samplers", []):
            idx = sampler.get("input")
            if isinstance(idx, int) and 0 <= idx < len(accessors):
                inp = accessors[idx]
                if "min" in inp and "max" in inp and inp["min"] and inp["max"]:
                    lows.append(inp["min"][0])
                    highs.append(inp["max"][0])
        if lows and highs:
            durations[anim["name"]] = round(max(highs) - min(lows), 3)
    # Luanti's texture slots are supplied independently by obj:set_properties.
    # A model with multiple materials needs more than a single png binding.
    material_count = len(json_data.get("materials", []))
    if material_count > 1:
        raise ValueError(f"Model has {material_count} materials, but FIX57 currently"
                         " supports one body texture; export one material or add proper mappings")
    unsupported = {"KHR_draco_mesh_compression", "EXT_meshopt_compression",
                   "KHR_texture_basisu", "KHR_materials_variants"}
    bad = sorted(unsupported.intersection(json_data.get("extensionsRequired", [])))
    if bad:
        raise ValueError("GLB uses required extensions not validated for Luanti: " + ", ".join(bad))
    return {
        "format": "glTF 2.0 binary",
        "meshes": len(meshes), "skins": len(skins), "materials": material_count,
        "animations": names, "verified_required_tracks": sorted(REQUIRED),
        "animation_durations_seconds": durations,
        "warning": "Metadata validation only; geometry orientation, game renderer and licensing still require device testing"
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glb", type=Path, help="Private Dremorn FBX -> GLB conversion")
    parser.add_argument("--texture", type=Path, help="Converted PNG, required for deployment")
    parser.add_argument("--report", type=Path, help="Write JSON metadata only")
    opts = parser.parse_args()
    try:
        if opts.texture is None or not opts.texture.is_file():
            raise ValueError("Missing external body PNG; Luanti ignores glTF embedded textures")
        if opts.texture.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Body texture is not a PNG")
        data = inspect(opts.glb)
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        print("FAIL FIX57 Dremorn preflight:", exc, file=sys.stderr)
        return 1
    result = json.dumps(data, indent=2, ensure_ascii=False)
    print(result)
    if opts.report:
        opts.report.write_text(result + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
