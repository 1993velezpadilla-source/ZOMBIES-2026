#!/usr/bin/env python3
"""Fail CI if APK lacks the actual VoxeLibre game, native ARM64 engine, or APK files."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import sys


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify_apk.py /path/to/APK")
    apk = Path(sys.argv[1])
    if not apk.is_file() or apk.stat().st_size < 10_000_000:
        raise RuntimeError(f"Missing or implausibly small Android APK: {apk}")
    with ZipFile(apk) as z:
        files = z.namelist()
        assert "classes.dex" in files, "Android DEX missing"
        assert any(n.startswith("lib/arm64-v8a/") and n.endswith(".so") for n in files), "ARM64 native binaries missing"
        assets_zip = next((n for n in files if n.endswith("/assets.zip")), None)
        if not assets_zip:
            raise RuntimeError("Engine's bundled assets.zip not found in APK")
        with ZipFile(BytesIO(z.read(assets_zip))) as assets:
            names = set(assets.namelist())
            assert "games/voxelibre/game.conf" in names, "VoxeLibre game.conf not bundled"
            mods = [n for n in names if n.startswith("games/voxelibre/mods/") and n.endswith("init.lua")]
            textures = [n for n in names if n.startswith("games/voxelibre/") and n.endswith(".png")]
            assert len(mods) >= 20, f"Expected full game mods, got {len(mods)}"
            assert len(textures) >= 100, f"Expected full game textures, got {len(textures)}"
            print(f"APK OK: {apk.name} ({apk.stat().st_size:,} bytes); "
                  f"{len(mods)} mod entrypoints, {len(textures)} PNGs; "
                  f"bundled {assets_zip}")


if __name__ == "__main__":
    main()
