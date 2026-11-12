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


def rebuild_inner(old_zip, new_zip, lua_file, btn_file):
    original = set()
    changed = {}
    with zipfile.ZipFile(old_zip) as old, zipfile.ZipFile(new_zip, "w", allowZip64=True) as new:
        old_names = old.namelist()
        if len(old_names) != len(set(old_names)):
            raise RuntimeError("FIX49C game assets contain duplicate paths")
        assert_unique_archive(old, GAME_PATH)
        original = {i.filename: (i.CRC, i.file_size) for i in old.infolist()}
        new.comment = old.comment
        changes = {GAME_PATH: lua_file.read_bytes(), BUTTON_PATH: btn_file.read_bytes()}
        for info in old.infolist():
            data = changes.pop(info.filename, None)
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
        if new.read(BUTTON_PATH) != btn_file.read_bytes():
            raise RuntimeError("Native USE button image was not packaged")
    return {"baseline_asset_count": len(original), "candidate_asset_count": len(names), "changed": changed}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fix49c", type=Path, required=True)
    p.add_argument("--rebuilt", type=Path, required=True)
    p.add_argument("--lua", type=Path, required=True)
    p.add_argument("--button", type=Path, required=True)
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
        report["assets"] = rebuild_inner(old_inner, new_inner, args.lua, args.button)
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
