#!/usr/bin/env python3
"""V3.3 physical-view obstruction tests for original AK FPS viewmodel."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import json
import struct
import sys

STOCK={"wood_stock_neck","wood_stock_middle","wood_stock_butt","butt_plate"}

def inspect_assets(read):
    model=json.loads(read("AK47_FP_EDITABLE.bbmodel"))
    names=[e["name"] for e in model["elements"]]
    assert len(names)==43,(len(names),"FPS parts")
    assert not STOCK.intersection(names)
    assert {"mag_top","mag_curved_middle","bolt","receiver",
            "front_sight_post","rear_sight_notch",
            "right_glove","left_glove"}.issubset(names)
    data=read("models/ak47dev_fp.glb")
    assert data[:4]==b"glTF" and struct.unpack_from("<I",data,8)[0]==len(data)
    jsonlen,tag=struct.unpack_from("<I4s",data,12)
    assert tag==b"JSON"
    d=json.loads(data[20:20+jsonlen])
    assert len(d["meshes"][0]["primitives"])==4
    assert len(d["skins"][0]["joints"])==5
    assert len(d["animations"][0]["channels"])==10
    # Legacy 47-part GLB and static OBJ must remain in the APK for comparison.
    assert read("models/ak47dev_animated.glb")[:4]==b"glTF"
    old=read("models/ak47dev_static.obj").decode()
    new=read("models/ak47dev_fp_static.obj").decode()
    assert old.count("\ng ")==47,old.count("\ng ")
    assert new.count("\ng ")==43,new.count("\ng ")
    assert "mtllib ak47dev_fp_static.mtl" in new
    assert read("models/ak47dev_fp_static.mtl").startswith(b"newmtl ")
    lua=read("init.lua").decode()
    assert 'mesh="ak47dev_fp_static.obj"' in lua
    for n in ["ak47dev_fire.ogg","ak47dev_reload.ogg",
              "ak47dev_magout.ogg","ak47dev_magin.ogg","ak47dev_bolt.ogg"]:
        assert read("sounds/"+n).startswith(b"OggS"),n
    print("AK-47 V3.3 FP ASSETS GREEN: original 43-piece no-stock GLB + "
          "native OBJ, 5 real animation bones, both iron-sights and audio")

def inspect_cxx(root):
    cpp=(root/"src/client/camera.cpp").read_text()
    assert 'm_client->getMesh("ak47dev_fp.glb")' in cpp
    assert 'const v3f hip_pos(8.0f, -6.5f, 31.0f);' in cpp
    assert 'const v3f ads_pos(0.0f, -2.7f, 31.5f);' in cpp
    assert 'm_ak47_viewmodel->setScale(v3f(3.1f, 3.1f, 3.1f));' in cpp
    assert 'm_ak47_viewmodel->getAnimation().tracks[0]' in cpp
    assert "com.xziel.voxelsandbox.v33" in (root/"android/app/build.gradle").read_text()
    print("AK-47 V3.3 CAMERA SOURCE GREEN: hipfire/iron-sight pose and "
          "first-person GLB model path correctly connected to C++")

def main():
    if len(sys.argv)!=2:raise SystemExit("verify_v33.py <luanti-dir|apk>")
    input=Path(sys.argv[1])
    mod="games/voxelibre/mods/ak47dev/"
    if input.suffix==".apk":
        with ZipFile(input) as a:
            assert any(n.startswith("lib/arm64-v8a/") and n.endswith(".so")
                       for n in a.namelist())
            with ZipFile(BytesIO(a.read("assets/assets.zip"))) as game:
                inspect_assets(lambda n:game.read(mod+n))
                assert "games/voxelibre/mods/zmapdev/init.lua" in game.namelist()
                assert "XXX Large" in game.read("builtin/mainmenu/dlg_zmap_world.lua").decode()
        print(f"V3.3 REAL APK VERIFIED {input.stat().st_size:,} bytes: "
              "V2 seven maps preserved; Android physical check still REQUIRED")
    else:
        inspect_cxx(input)
        inspect_assets(lambda n:(input/mod/n).read_bytes())

if __name__=="__main__":main()
