#!/usr/bin/env python3
"""Validate V2 editor code and APK contents, without pretending this is gameplay testing."""
from io import BytesIO
from pathlib import Path
import re
import struct
import sys
from zipfile import ZipFile

SIZES = [64, 128, 256, 384, 512, 768, 1024]
HERE = Path(__file__).resolve().parent

def source_checks():
    dialog = (HERE/"dlg_zmap_world.lua").read_text(encoding="utf8")
    mod = (HERE/"zmapdev/init.lua").read_text(encoding="utf8")
    for n in SIZES:
        if not re.search(r"width\s*=\s*" + str(n) + r"\b", dialog):
            raise AssertionError(f"Missing template width {n}")
        if not re.search(r"\[" + str(n) + r"\]\s*=\s*true", mod):
            raise AssertionError(f"Size {n} not accepted by boundary generator")
    assert "XXX Large" in dialog
    assert "singlenode" in dialog
    assert "register_on_generated" in mod
    assert "register_globalstep" in mod
    assert "register_node" in mod
    assert "xz_map_template" in dialog and "xz_map_template" in mod
    assert 'return' in mod
    print("SOURCE V2 OK: 7 widths, single-node mapgen, on-generated terrain, physical + server-side walls")

def apk_checks(path):
    with ZipFile(path) as apk:
        assert any(n.endswith(".so") and n.startswith("lib/arm64-v8a/") for n in apk.namelist())
        with ZipFile(BytesIO(apk.read("assets/assets.zip"))) as a:
            names = set(a.namelist())
            required = [
                "builtin/mainmenu/dlg_zmap_world.lua",
                "builtin/mainmenu/tab_local.lua",
                "games/voxelibre/mods/zmapdev/init.lua",
                "games/voxelibre/mods/zmapdev/mod.conf",
                "games/voxelibre/mods/zmapdev/textures/zmapdev_red_boundary.png",
                "games/voxelibre/game.conf",
            ]
            for p in required:
                assert p in names, f"Missing {p}"
            dlg = a.read(required[0]).decode()
            menu = a.read(required[1]).decode()
            mod = a.read(required[2]).decode()
            assert "XXX Large" in dlg and "width = 1024" in dlg
            assert "zmap_create;Create Map" in menu
            assert "world_create;Survival (New)" in menu
            assert "zmapdev:red_boundary" in mod
            assert "mcl_core:dirt_with_grass" in mod
            texture = a.read(required[4])
            assert texture.startswith(b"\x89PNG\r\n\x1a\n")
            assert struct.unpack(">II", texture[16:24]) == (16, 16)
            print(f"APK V2 CONTENT OK: red RGBA PNG, 7 templates, full VoxeLibre, size={path.stat().st_size}")

def main():
    source_checks()
    if len(sys.argv)>1:
        apk_checks(Path(sys.argv[1]))

if __name__=="__main__":
    main()
