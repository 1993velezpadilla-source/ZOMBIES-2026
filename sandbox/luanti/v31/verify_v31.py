#!/usr/bin/env python3
"""V3.1 first-person visibility regression checks. Rendering requires Android test."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import re,struct,sys
HERE=Path(__file__).parent

def inspect_files(read):
    init=read("init.lua").decode("utf8")
    assert "minetest.register_node(AK,{" in init
    assert 'drawtype="mesh"' in init
    assert 'mesh="ak47dev_static.obj"' in init
    assert 'tiles={"ak47dev_atlas.png"}' in init
    assert "wield_image=" not in "\n".join(l for l in init.splitlines() if not l.lstrip().startswith("--"))
    assert "function make_viewmodel" in init
    assert 'minetest.register_chatcommand("akrig"' in init
    assert 'minetest.register_chatcommand("akdiag"' in init
    assert "rig_enabled=false" in init
    assert "set_animation" in init
    data=read("models/ak47dev_static.obj").decode("utf8")
    verts=[l for l in data.splitlines() if l.startswith("v ")]
    faces=[l for l in data.splitlines() if l.startswith("f ")]
    # 47 original cuboids, 8 vertices each, 12 triangles each.
    assert len(verts)==376,(len(verts),"vertices")
    assert len(faces)==564,(len(faces),"triangles")
    for f in faces:
        for token in f[2:].split():
            fields=token.split("/")
            assert len(fields)==3
            assert 1<=int(fields[0])<=len(verts)
            assert int(fields[1])>0 and 1<=int(fields[2])<=6
    png=read("textures/ak47dev_atlas.png")
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    assert struct.unpack(">II",png[16:24])==(64,16)
    assert read("models/ak47dev_animated.glb").startswith(b"glTF")
    assert read("sounds/ak47dev_fire.ogg").startswith(b"OggS")
    assert read("sounds/ak47dev_reload.ogg").startswith(b"OggS")
    print("V3.1 NATIVE 3D WIELD OK: node drawtype mesh + atlas, 47 pieces, "
          "376 vertices, 564 triangles, GLB kept for /akrig diagnostic")

def main():
    if len(sys.argv)!=2: raise SystemExit("verify_v31.py PATH_TO_MOD_OR_APK")
    p=Path(sys.argv[1])
    if p.suffix==".apk":
        with ZipFile(p) as a:
            with ZipFile(BytesIO(a.read("assets/assets.zip"))) as data:
                prefix="games/voxelibre/mods/ak47dev/"
                inspect_files(lambda filename:data.read(prefix+filename))
                assert "games/voxelibre/mods/zmapdev/init.lua" in data.namelist()
                assert "XXX Large" in data.read("builtin/mainmenu/dlg_zmap_world.lua").decode()
                print(f"V3.1 VERIFIED PACKAGED APK: {p.stat().st_size:,} bytes")
    else:
        inspect_files(lambda filename:(p/filename).read_bytes())
if __name__=="__main__":
    main()
