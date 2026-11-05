#!/usr/bin/env python3
"""Patch a disposable Luanti+VoxeLibre Android tree for Voxel Sandbox V2.

Requires sandbox/luanti/prepare.py to have been applied first.
Keeps the working V1 APK / package completely separate.
"""
from pathlib import Path
import shutil
import struct
import sys
import zlib

REPO = Path(__file__).resolve().parents[3]

def checked(path, before, after):
    original = path.read_text(encoding="utf8")
    if original.count(before) != 1:
        raise RuntimeError(f"{path}: expected one anchor {before!r}, got {original.count(before)}")
    path.write_text(original.replace(before, after), encoding="utf8")

def png_chunk(kind, content):
    return struct.pack(">I", len(content)) + kind + content + struct.pack(
        ">I", zlib.crc32(kind + content) & 0xffffffff
    )

def red_boundary_png(path):
    # Translucent red grid plus diagonal signal stripes, 16x16 RGBA.
    raw = bytearray()
    for y in range(16):
        raw.append(0)  # PNG filter: None
        for x in range(16):
            stripe = ((x + y) % 8) < 2
            edge = x == 0 or y == 0
            raw += bytes((255, 30 if stripe else 18, 32, 145 if edge or stripe else 84))
    ihdr = struct.pack(">IIBBBBB", 16, 16, 8, 6, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) +
           png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
           png_chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python patch_v2.py /path/to/luanti")
    root = Path(sys.argv[1]).resolve()
    app = root / "android/app"
    game = root / "games/voxelibre"
    if not (game / "game.conf").is_file():
        raise RuntimeError("VoxeLibre absent; run prepare.py first")

    checked(app/"build.gradle", "applicationId 'com.xziel.voxelsandbox'",
            "applicationId 'com.xziel.voxelsandbox.v2'")
    checked(app/"src/main/AndroidManifest.xml",
            "com.xziel.voxelsandbox.fileprovider",
            "com.xziel.voxelsandbox.v2.fileprovider")
    checked(app/"src/main/AndroidManifest.xml",
            "com.xziel.voxelsandbox.documents",
            "com.xziel.voxelsandbox.v2.documents")
    checked(app/"src/main/java/net/minetest/minetest/GameActivity.java",
            '"com.xziel.voxelsandbox.fileprovider"',
            '"com.xziel.voxelsandbox.v2.fileprovider"')
    checked(app/"src/main/res/values/strings.xml",
            '<string name="label">Voxel Sandbox Dev</string>',
            '<string name="label">Voxel Sandbox V2</string>')

    menu = root / "builtin/mainmenu"
    marker = 'dofile(menupath .. DIR_DELIM .. "dlg_create_world.lua")'
    checked(menu/"init.lua", marker,
            marker + '\ndofile(menupath .. DIR_DELIM .. "dlg_zmap_world.lua")')
    shutil.copyfile(REPO/"sandbox/luanti/v2/dlg_zmap_world.lua", menu/"dlg_zmap_world.lua")

    tab = menu/"tab_local.lua"
    checked(tab,
            'button[6.65,0;3.225,0.8;world_create;".. fgettext("New") .. "]"',
            'button[6.65,0;3.225,0.8;world_create;Survival (New)]"')
    checked(tab,
            '\n\treturn retval\nend\n\nlocal function main_button_handler',
            '\n\tretval = retval .. "button[0.375,6.0;4.55,0.85;zmap_create;Create Map]"' +
            '\n\treturn retval\nend\n\nlocal function main_button_handler')
    marker = '\tif fields["world_create"] ~= nil then'
    checked(tab, marker,
            '\tif fields["zmap_create"] ~= nil then\n' +
            '\t\tlocal dlg = create_zmap_world_dlg()\n' +
            '\t\tdlg:set_parent(this)\n' +
            '\t\tthis:hide()\n' +
            '\t\tdlg:show()\n' +
            '\t\treturn true\n' +
            '\tend\n\n' + marker)

    newmod = game / "mods/zmapdev"
    newmod.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO/"sandbox/luanti/v2/zmapdev/mod.conf", newmod/"mod.conf")
    shutil.copyfile(REPO/"sandbox/luanti/v2/zmapdev/init.lua", newmod/"init.lua")
    red_boundary_png(newmod/"textures/zmapdev_red_boundary.png")

    assert "XXX Large" in (menu/"dlg_zmap_world.lua").read_text()
    assert (newmod/"textures/zmapdev_red_boundary.png").stat().st_size > 80
    print("Voxel Sandbox V2 prepared: seven maps 64..1024, separate APK ID, red boundaries")

if __name__ == "__main__":
    main()
