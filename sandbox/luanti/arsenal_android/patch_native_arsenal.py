#!/usr/bin/env python3
"""Connect REAL owner-derived gun/hands GLBs to the already-working AK HD client.

Prerequisite: the pinned V3.3 + original AK HD private patch is applied.
This script modifies ONLY an ephemeral Luanti checkout; no game assets in git.
The emitted native renderer is experimental: not a 28-gun gameplay signoff.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
ID = re.compile(r"^[a-z0-9_]{1,24}$")


def replace_once(path: Path, original: str, replacement: str) -> None:
    text = path.read_text(encoding="utf8")
    matches = text.count(original)
    if matches != 1:
        raise ValueError(f"{path}: expected one anchor, found {matches}: {original[:85]!r}")
    path.write_text(text.replace(original, replacement), encoding="utf8")


def patch(root: Path, source_mod: Path, manifest: Path) -> dict:
    header = root / "src/client/camera.h"
    cpp = root / "src/client/camera.cpp"
    if not header.is_file() or not cpp.is_file():
        raise FileNotFoundError("Luanti C++ checkout absent")
    if "void Camera::updateAK47Viewmodel(f32 frametime)" not in cpp.read_text():
        raise ValueError("AK HD patch must run first; unchanged original bridge")
    data = json.loads(manifest.read_text(encoding="utf8"))
    eligible = data.get("native_model_ids")
    if not isinstance(eligible, list) or not eligible or len(eligible) != len(set(eligible)):
        raise ValueError("need non-empty verified unique native weapon IDs")
    if any(not isinstance(x, str) or not ID.fullmatch(x) for x in eligible):
        raise ValueError("unsafe native weapon ID")
    for weapon in eligible:
        for suffix in ("gun", "hands"):
            file = source_mod / "models" / f"arsenal_{weapon}_{suffix}.glb"
            if not file.is_file() or file.stat().st_size < 100:
                raise FileNotFoundError(f"missing real native model: {file}")
    for texture in ("arsenal_flat_metal.png", "arsenal_flat_hands.png"):
        if not (source_mod / "textures" / texture).is_file():
            raise FileNotFoundError(f"missing authored fallback texture: {texture}")
    if not (source_mod / "init.lua").is_file():
        raise FileNotFoundError("arsenal init.lua is missing")

    replace_once(header, "\tvoid updateAK47Viewmodel(f32 frametime);",
                 "\tvoid updateAK47Viewmodel(f32 frametime);\n"
                 "\tvoid updateArsenalViewmodel(f32 frametime);")
    key = "\tu32 m_ak47_last_fired=0;"
    replace_once(header, key, key + """
	// Original COD4 source pairs: use only the equipped gun on demand.
	scene::AnimatedMeshSceneNode *m_arsenal_gun = nullptr;
	scene::AnimatedMeshSceneNode *m_arsenal_hands = nullptr;
	std::string m_arsenal_id;
	std::string m_arsenal_last_event;
	std::string m_arsenal_action;
	std::string m_arsenal_clip;
	f32 m_arsenal_retry = 0.0f;
	f32 m_arsenal_clock = 0.0f;
	f32 m_arsenal_ads_alpha = 0.0f;
	f32 m_arsenal_action_remaining = 0.0f;
	f32 m_arsenal_action_duration = 0.0f;
""".rstrip("\n"))
    key = "void Camera::wield(const ItemStack &item, bool animate)\n{"
    insert = (HERE / "native_arsenal_camera.cpp.inc").read_text(encoding="utf8")
    replace_once(cpp, key, insert + "\n" + key)

    key = """    const f32 dt = std::max(0.0f, frametime);
    if (m_wield_item_next.name != "ak47dev:ak47" || m_camera_mode != CAMERA_MODE_FIRST) {"""
    replacement = """    const f32 dt = std::max(0.0f, frametime);
    if (m_wield_item_next.name.compare(0, 8, "arsenal:") == 0) {
        updateArsenalViewmodel(frametime);
        return;
    }
    // Cleanly hide the previous source arsenal before returning to AK or tools.
    updateArsenalViewmodel(frametime);
    if (m_wield_item_next.name != "ak47dev:ak47" || m_camera_mode != CAMERA_MODE_FIRST) {"""
    replace_once(cpp, key, replacement)
    key = 'if (m_wield_item_next.name == "ak47dev:ak47" && m_ak47_viewmodel) {'
    replace_once(cpp, key, 'if ((m_wield_item_next.name == "ak47dev:ak47" && m_ak47_viewmodel) ||\n'
                             '            (m_wield_item_next.name.compare(0, 8, "arsenal:") == 0 && m_arsenal_gun)) {')
    key = 'if (item.name == "ak47dev:ak47" &&\n\t\t\t\tm_wield_item_next.name == item.name) {'
    replace_once(cpp, key, 'if ((item.name == "ak47dev:ak47" ||\n'
                           '\t\t\t\titem.name.compare(0, 8, "arsenal:") == 0) &&\n'
                           '\t\t\t\tm_wield_item_next.name == item.name) {')
    mod = root / "games/voxelibre/mods/arsenal"
    if mod.exists():
        raise ValueError("arsenal mod already exists: refusing overwrite")
    shutil.copytree(source_mod, mod)
    # Separate test package: never overwrite the owner's installed AK bridge.
    new_package = "com.xziel.voxelsandbox.arsenaltest"
    old_package = "com.xziel.voxelsandbox.ak47dryv8"
    app = root / "android/app"
    for path in (app/"build.gradle",
                 app/"src/main/AndroidManifest.xml",
                 app/"src/main/java/net/minetest/minetest/GameActivity.java"):
        content = path.read_text(encoding="utf8")
        if old_package not in content:
            raise ValueError(f"required old package ID missing: {path}")
        path.write_text(content.replace(old_package, new_package), encoding="utf8")
    strings = app/"src/main/res/values/strings.xml"
    content = strings.read_text(encoding="utf8")
    if "AK47 COD4 Dry Fire V8" not in content:
        raise ValueError("wrong AK native patch base app label")
    strings.write_text(content.replace("AK47 COD4 Dry Fire V8",
                                       "COD4 Arsenal Native Preview"), encoding="utf8")
    return {"native_model_count": len(eligible),
            "native_ids": sorted(eligible),
            "legacy_ak_preserved": True,
            "package": new_package,
            "native_armature_render_tested": False,
            "ads_aim_verified": False,
            "android_fps_verified": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source-mod", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    args = p.parse_args()
    result = patch(args.root, args.source_mod, args.manifest)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
