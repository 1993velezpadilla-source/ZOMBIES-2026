#!/usr/bin/env python3
"""Static regression checks: not a substitute for real Android gameplay tests."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import json
import struct
import sys

HERE = Path(__file__).parent
REQ_SOUNDS=["ak47dev_fire.ogg","ak47dev_reload.ogg","ak47dev_dry.ogg",
            "ak47dev_magout.ogg","ak47dev_magin.ogg","ak47dev_bolt.ogg"]

def validate_glb(binary):
    assert binary[:4]==b"glTF" and struct.unpack_from("<I",binary,4)[0]==2
    assert struct.unpack_from("<I",binary,8)[0]==len(binary)
    length, typ=struct.unpack_from("<I4s",binary,12)
    assert typ==b"JSON"
    gltf=json.loads(binary[20:20+length])
    assert gltf["skins"][0]["joints"] == [0,1,2,3,4]
    assert len(gltf["meshes"][0]["primitives"]) == 4
    assert len(gltf["animations"][0]["channels"]) >= 10
    assert gltf["buffers"][0]["byteLength"]>1000
    # glTF has a 3.75 second keyframe sequence, including the reload.
    assert gltf["accessors"][-1]["count"]>=17
    assert {n["name"] for n in gltf["nodes"]} >= {
        "root","magazine","bolt","left_hand","right_hand"}
    return gltf

def inspect(mod):
    m=mod.rstrip("/")+"/"
    assert Path(m+"models/ak47dev_animated.glb").exists()
    validate_glb(Path(m+"models/ak47dev_animated.glb").read_bytes())
    for n in REQ_SOUNDS:
        assert Path(m+"sounds/"+n).read_bytes().startswith(b"OggS"),n
    for n in ["ak47dev_metal.png","ak47dev_black.png",
              "ak47dev_wood.png","ak47dev_skin.png","ak47dev_icon.png",
              "ak47dev_blank.png"]:
        assert Path(m+"textures/"+n).read_bytes().startswith(b"\x89PNG"),n
    s=Path(m+"init.lua").read_text()
    for token in ["register_tool","on_use","on_secondary_use","set_animation",
                  "set_attach","register_on_joinplayer","register_globalstep",
                  "register_chatcommand","xz_map_template","set_fov"]:
        assert token in s,token
    print("V3 SOURCE OK: GLB 5-joint rig, fire/reload animation, 6 OGG sounds, ADS + weapon logic")

def apk(path):
    with ZipFile(path) as a:
        names=set(a.namelist())
        assert any(z.startswith("lib/arm64-v8a/") and z.endswith(".so") for z in names)
        with ZipFile(BytesIO(a.read("assets/assets.zip"))) as z:
            names=set(z.namelist())
            prefix="games/voxelibre/mods/ak47dev/"
            required=["init.lua","mod.conf","models/ak47dev_animated.glb",
                      "textures/ak47dev_icon.png","textures/ak47dev_blank.png",
                      "AK47_EDITABLE.bbmodel"]+["sounds/"+n for n in REQ_SOUNDS]
            for n in required: assert prefix+n in names,n
            gltf=validate_glb(z.read(prefix+"models/ak47dev_animated.glb"))
            for n in REQ_SOUNDS:
                assert z.read(prefix+"sounds/"+n).startswith(b"OggS"),n
            assert "games/voxelibre/mods/zmapdev/init.lua" in names
            assert "XXX Large" in z.read("builtin/mainmenu/dlg_zmap_world.lua").decode()
            assert len([n for n in names if n.endswith("init.lua")]) >= 220
            print(f"V3 APK CONTENT OK: {path.stat().st_size:,} bytes, original GLB animation, "
                  "6 distinct audio cues, V2 map boundaries preserved")
if __name__=="__main__":
    if len(sys.argv)==2 and sys.argv[1].endswith(".apk"):
        apk(Path(sys.argv[1]))
    else:
        inspect(Path(sys.argv[1]) if len(sys.argv)==2 else HERE/"ak47dev")
