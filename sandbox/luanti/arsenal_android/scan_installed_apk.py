"""Conservative source-based tool inventory inside a *real* Luanti APK.

The APK may contain animated variant GLBs for only two weapon registrations.
Never claim a model, attachment, or configuration count is a playable gun.
Dynamic Lua registrations outside a known pattern are explicitly unresolved.
"""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import struct
from zipfile import ZipFile

MAX = 32 * 1024 * 1024


def registrations(lua_sources):
    ids, unresolved = set(), []
    for path, source in lua_sources.items():
        source = "\n".join(line for line in source.splitlines()
                           if not line.lstrip().startswith("--"))
        consts = dict(re.findall(
            r'\blocal\s+(\w+)\s*=\s*["\']([\w]+:[\w]+)["\']', source))
        defs = set()
        table = re.search(r'\blocal\s+definitions\s*=\s*\{(.*?)\n\s*\}',
                          source, re.S)
        if table:
            defs = {consts[k] for k in re.findall(
                r'\[\s*(\w+)\s*\]\s*=\s*\{', table.group(1))
                if k in consts}
        for match in re.finditer(
                r'\b(?:minetest|core)\.register_tool\s*\(\s*([^,\n]+)',
                source):
            arg = match.group(1).strip()
            literal = re.fullmatch(r'["\']([\w]+:[\w]+)["\']', arg)
            if literal:
                ids.add(literal.group(1))
            elif arg in consts:
                ids.add(consts[arg])
            elif arg in ("item_name", "weapon_name", "name") and defs and re.search(
                rf'for\s+{arg}\s*,?[^\n]*\s+in\s+pairs\s*\(\s*definitions\s*\)\s+do',
                source):
                ids.update(defs)
            else:
                unresolved.append({"file": path, "expression": arg})
    return sorted(ids), unresolved


def glb_clips(blob, name):
    if len(blob) < 20 or blob[:4] != b"glTF":
        raise ValueError(f"invalid GLB: {name}")
    ver, total = struct.unpack_from("<II", blob, 4)
    size, kind = struct.unpack_from("<I4s", blob, 12)
    if ver != 2 or total != len(blob) or kind != b"JSON" or size > len(blob)-20:
        raise ValueError(f"invalid GLB header: {name}")
    obj = json.loads(blob[20:20+size])
    if not obj.get("meshes"):
        raise ValueError(f"GLB has no mesh: {name}")
    return [a.get("name") for a in obj.get("animations", [])]


def scan(apk):
    with ZipFile(apk) as outer:
        names = outer.namelist()
        if "AndroidManifest.xml" not in names or "assets/assets.zip" not in names:
            raise ValueError("not a Luanti APK")
        arm64 = any(x.startswith("lib/arm64-v8a/") and x.endswith(".so")
                    for x in names)
        with ZipFile(BytesIO(outer.read("assets/assets.zip"))) as inner:
            names = inner.namelist()
            if len(names) != len(set(names)):
                raise ValueError("duplicate ZIP member")
            sources = {}
            models, textures, sounds = {}, [], []
            for name in names:
                if not name.startswith("games/") or "/mods/" not in name:
                    continue
                info = inner.getinfo(name)
                if info.is_dir():
                    continue
                if info.file_size > MAX and name.endswith((".glb", ".lua", ".png", ".ogg")):
                    raise ValueError("oversized mod media: "+name)
                if name.endswith(".lua"):
                    sources[name] = inner.read(name).decode("utf-8")
                if "/models/" in name and name.endswith(".glb"):
                    models[name] = glb_clips(inner.read(name), name)
                if "/textures/" in name and name.endswith(".png"):
                    textures.append(name)
                if "/sounds/" in name and name.endswith(".ogg"):
                    sounds.append(name)
            ids, dynamic = registrations(sources)
            ammo_files = [n for n in sources if n.endswith("/ammo.lua")]
            return {"apk_name": apk.name,
                    "sha256": hashlib.sha256(apk.read_bytes()).hexdigest(),
                    "arm64_library_present": arm64,
                    "registered_tool_ids_found": ids,
                    "registered_tool_count": len(ids) if not dynamic else None,
                    "unresolved_dynamic_registration": dynamic,
                    "glb_count": len(models),
                    "model_animation_names": models,
                    "png_count": len(textures), "ogg_count": len(sounds),
                    "ammo_lua_present": bool(ammo_files),
                    "configurations_verified": False,
                    "animations_played_on_device": False,
                    "device_fps_verified": False,
                    "commercial_licenses_verified": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("apk", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--require-tools", type=int)
    args = p.parse_args()
    try:
        data = scan(args.apk)
        if (args.require_tools is not None and
                data["registered_tool_count"] != args.require_tools):
            raise ValueError(f"requires {args.require_tools} tools; "
                             f"found {data['registered_tool_count']}")
    except (ValueError, OSError) as error:
        p.exit(2, f"ARSENAL_INVENTORY_FAILED: {error}\n")
    report = json.dumps(data, indent=2, sort_keys=True)+"\n"
    if args.output:
        args.output.write_text(report)
    print(f"Inventory: {data['registered_tool_count']} tool IDs, "
          f"{data['glb_count']} GLBs; not proof of device gameplay")


if __name__ == "__main__":
    main()
