#!/usr/bin/env python3
"""Produce a side-by-side FIX50B test APK while preserving all FIX49C content.

The rebuilt Luanti Android app must have a DIFFERENT applicationId from FIX49C.
This script combines the actually compiled native app with the original FIX49C
game archive and the FIX50B Lua + native USE control PNG. The result is UNSIGNED:
CI must zipalign, sign with a disposable test key, and verify before distribution.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import lzma
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

GAME_PATH = "games/voxelibre/mods/xz_zombies_classic/init.lua"
COMBAT_PATH = "games/voxelibre/mods/ak47dev/combat.lua"
DIRECTOR_PATH = "games/voxelibre/mods/xz_zombies_classic/round_director.lua"
BUTTON_PATH = "textures/base/pack/xz_use_btn.png"
COMPRESSED_ENTRY = "luanti-assets.zip.xz"
OUTER_PATH = "assets/assets.zip"


def copy_stream(src, dest):
    shutil.copyfileobj(src, dest, length=8 * 1024 * 1024)


def hash_file(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def assert_unique_archive(z, name):
    names = z.namelist()
    if names.count(name) != 1:
        raise RuntimeError(f"{name}: expected one item, found {names.count(name)}")


def patch_cod4_projectile_hit(source):
    """Add a post-hit score callback without modifying the weapon's original punch."""
    old = source.decode("utf-8")
    signature = "local function projectile_hit(target,shooter,damage,direction)\n"
    old_body = ("  damage_groups={fleshy=math.max(1,math.floor(damage+.5)),cod4_projectile=1}},direction)\n")
    if old.count(signature) != 1 or old.count(old_body) != 1:
        raise RuntimeError("COD4 combat.lua does not match the exact known-good bullet source")
    new = old.replace(signature, signature +
        " local v26_before=target.get_hp and target:get_hp() or nil\n")
    new = new.replace(old_body, old_body +
        " if v26_before then\n"
        "  local ok,v26_after=pcall(function() return target:get_hp() end)\n"
        "  if not ok then v26_after=0 end\n"
        "  local api=rawget(_G,'xz_zombies_classic')\n"
        "  if api and api.on_cod4_impact then\n"
        "   api.on_cod4_impact(shooter,target,v26_before,v26_after)\n"
        "  end\n"
        " end\n")
    if new.count("target:punch(shooter,1,{full_punch_interval=1,") != 1:
        raise RuntimeError("Original COD4 damage body changed")
    return new.encode("utf-8")



def extend_existing_cod4_v26_hit_hook(source):
    """Extend FIX53's verified ORIGINAL hit hook with damage + actual raycast point.

    We do not alter target:punch, original 28 weapon definitions, ranges,
    velocities, ADS, or animations. These three strings came from a dump of
    the ACTUAL FIX53 combat.lua inside the signed Android APK.
    """
    old = source.decode("utf-8")
    changes = {
        "local function projectile_hit(target,shooter,damage,direction)\n":
        "local function projectile_hit(target,shooter,damage,direction,intersection)\n",
        "api.on_cod4_impact(shooter,target,v26_before,v26_after)\n":
        "api.on_cod4_impact(shooter,target,v26_before,v26_after,damage,intersection)\n",
        "projectile_hit(hit.ref,shooter,damage,normal(b.velocity))\n":
        "projectile_hit(hit.ref,shooter,damage,normal(b.velocity),hit.intersection_point)\n",
    }
    if any(old.count(k)!=1 for k in changes):
        raise RuntimeError("Live FIX53 combat.lua changed: refusing uncertain weapon edit")
    if old.count("target:punch(shooter,1,{full_punch_interval=1,")!=1:
        raise RuntimeError("Original COD4 punch source not exactly intact")
    result=old
    for a,b in changes.items(): result=result.replace(a,b)
    assert result.count("target:punch(shooter,1,{full_punch_interval=1,")==1
    return result.encode("utf-8")


def rebuild_inner(old_zip, new_zip, lua_file, btn_file, director_file=None, overlay_dir=None, cod4_hit_hook=False, v26_original_hit_details=False):
    original = set()
    changed = {}
    with zipfile.ZipFile(old_zip) as old, zipfile.ZipFile(new_zip, "w", allowZip64=True) as new:
        old_names = old.namelist()
        if len(old_names) != len(set(old_names)):
            raise RuntimeError("FIX49C game assets contain duplicate paths")
        assert_unique_archive(old, GAME_PATH)
        if cod4_hit_hook and v26_original_hit_details: raise RuntimeError('Select ONE COD4 patch mode')
        if cod4_hit_hook or v26_original_hit_details: assert_unique_archive(old, COMBAT_PATH)
        original = {i.filename: (i.CRC, i.file_size) for i in old.infolist()}
        new.comment = old.comment
        changes = {GAME_PATH: lua_file.read_bytes()}
        if btn_file is not None:
            changes[BUTTON_PATH] = btn_file.read_bytes()
        if director_file is not None:
            changes[DIRECTOR_PATH] = director_file.read_bytes()
        overlay_files = {}
        if overlay_dir is not None:
            if not overlay_dir.is_dir():
                raise RuntimeError('Missing staged v26 overlay directory')
            for file in sorted(overlay_dir.rglob('*')):
                if not file.is_file():
                    continue
                relative = file.relative_to(overlay_dir).as_posix()
                if relative.startswith('/') or '..' in Path(relative).parts:
                    raise RuntimeError('Unsafe v26 resource path: ' + relative)
                inner_path = 'games/voxelibre/mods/xz_zombies_classic/' + relative
                if inner_path in changes:
                    raise RuntimeError('Duplicate overlay file: ' + inner_path)
                overlay_files[inner_path] = file.read_bytes()
            if not overlay_files:
                raise RuntimeError('Empty v26 resource overlay')
            changes.update(overlay_files)
        for info in old.infolist():
            data = changes.pop(info.filename, None)
            if info.filename == COMBAT_PATH and (cod4_hit_hook or v26_original_hit_details):
                if data is not None: raise RuntimeError("Combat cannot be doubly overwritten")
                data = (patch_cod4_projectile_hit(old.read(info.filename))
                    if cod4_hit_hook else extend_existing_cod4_v26_hit_hook(old.read(info.filename)))
                changed[info.filename] = "replaced"
            if data is None:
                with old.open(info) as stream:
                    data = stream.read()
            else:
                changed[info.filename] = "replaced"
            new.writestr(copy.copy(info), data, compress_type=info.compress_type)
        for path, data in changes.items():
            new.writestr(path, data, compress_type=zipfile.ZIP_STORED)
            changed[path] = "added"
    with zipfile.ZipFile(new_zip) as new:
        names = new.namelist()
        if len(names) != len(set(names)):
            raise RuntimeError("FIX50B duplicate asset")
        for name, (crc, size) in original.items():
            if name not in changed:
                actual = new.getinfo(name)
                if (actual.CRC, actual.file_size) != (crc, size):
                    raise RuntimeError("Regression in untouched FIX49C asset " + name)
        if new.read(GAME_PATH) != lua_file.read_bytes():
            raise RuntimeError("FIX50B Lua was not packaged")
        if btn_file is not None and new.read(BUTTON_PATH) != btn_file.read_bytes():
            raise RuntimeError("Native USE button image was not packaged")
        if director_file is not None and new.read(DIRECTOR_PATH) != director_file.read_bytes():
            raise RuntimeError("Round Director Lua was not packaged")
        for key, raw in overlay_files.items():
            if new.read(key) != raw:
                raise RuntimeError('v26 source asset was altered: '+key)
    return {"baseline_asset_count": len(original), "candidate_asset_count": len(names), "changed": changed}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fix49c", type=Path, required=True)
    p.add_argument("--rebuilt", type=Path, required=True)
    p.add_argument("--lua", type=Path, required=True)
    p.add_argument("--button", type=Path)
    p.add_argument("--director", type=Path)
    p.add_argument("--overlay-dir", type=Path)
    p.add_argument("--cod4-hit-hook", action="store_true")
    p.add_argument("--v26-original-hit-details", action="store_true")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {}
    with tempfile.TemporaryDirectory(prefix="fix50b-test-") as scratch:
        temp = Path(scratch)
        original_outer = temp / "old-assets.zip"
        old_inner_xz = temp / "old-inner.zip.xz"
        old_inner = temp / "old-inner.zip"
        new_inner = temp / "new-inner.zip"
        new_inner_xz = temp / "new-inner.zip.xz"
        new_outer = temp / "new-assets.zip"

        with zipfile.ZipFile(args.fix49c) as oldapk:
            assert_unique_archive(oldapk, OUTER_PATH)
            if "lib/arm64-v8a/libluanti.so" not in oldapk.namelist():
                raise RuntimeError("FIX49C native library is absent")
            with oldapk.open(OUTER_PATH) as src, original_outer.open("wb") as dest:
                copy_stream(src, dest)
        with zipfile.ZipFile(original_outer) as oldouter:
            assert_unique_archive(oldouter, COMPRESSED_ENTRY)
            if not oldouter.comment.startswith(b"XZ-ASSETS-1:"):
                raise RuntimeError("FIX49C compact archive marker missing")
            with oldouter.open(COMPRESSED_ENTRY) as src, old_inner_xz.open("wb") as dest:
                copy_stream(src, dest)
        with lzma.open(old_inner_xz, "rb") as src, old_inner.open("wb") as dest:
            copy_stream(src, dest)
        report["assets"] = rebuild_inner(old_inner, new_inner, args.lua, args.button, args.director, args.overlay_dir, args.cod4_hit_hook, args.v26_original_hit_details)
        with new_inner.open("rb") as src, lzma.open(new_inner_xz, "wb", format=lzma.FORMAT_XZ, preset=3) as dest:
            copy_stream(src, dest)
        with zipfile.ZipFile(new_outer, "w", allowZip64=True) as outer:
            outer.write(new_inner_xz, COMPRESSED_ENTRY, compress_type=zipfile.ZIP_STORED)
            outer.comment = f"XZ-ASSETS-1:{report['assets']['candidate_asset_count']}".encode()
        with zipfile.ZipFile(args.rebuilt) as candidate, zipfile.ZipFile(args.output, "w", allowZip64=True) as output:
            assert_unique_archive(candidate, OUTER_PATH)
            names = candidate.namelist()
            if len(names) != len(set(names)):
                raise RuntimeError("Candidate has duplicate APK paths")
            if "lib/arm64-v8a/libluanti.so" not in names:
                raise RuntimeError("Candidate lacks compiled native Luanti")
            report["baseline_app_files"] = len(names)
            for info in candidate.infolist():
                # Remove old signatures, if any, and sign final APK afresh.
                if re.match(r"^META-INF/[^/]+\.(?:RSA|DSA|SF|EC)$", info.filename, re.I):
                    continue
                if info.filename == OUTER_PATH:
                    # Original entry properties are retained except CRC/size.
                    output.write(new_outer, OUTER_PATH, compress_type=zipfile.ZIP_STORED)
                else:
                    with candidate.open(info) as src:
                        output.writestr(copy.copy(info), src.read(), compress_type=info.compress_type)
        with zipfile.ZipFile(args.output) as final:
            if final.testzip() is not None:
                raise RuntimeError("Corrupt uncompressed entry in full test APK")
            with zipfile.ZipFile(args.rebuilt) as rebuilt:
                if final.getinfo("lib/arm64-v8a/libluanti.so").CRC != rebuilt.getinfo("lib/arm64-v8a/libluanti.so").CRC:
                    raise RuntimeError("Native rebuilt library has been altered")
            if final.getinfo(OUTER_PATH).file_size != new_outer.stat().st_size:
                raise RuntimeError("Packed game assets missing")
        report["unsigned_apk_sha256"] = hash_file(args.output)
        report["unsigned_apk_bytes"] = args.output.stat().st_size
    (args.output.parent / "packaging_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
