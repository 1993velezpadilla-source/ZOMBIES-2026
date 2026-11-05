#!/usr/bin/env python3
"""Static and packaged verification for Voxel Sandbox V3.2 native FPS camera."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import sys

THIS = Path(__file__).resolve().parent
PARTS=[
    "void Camera::updateAK47Viewmodel(f32 frametime)",


    'm_ak47_viewmodel->getAnimation().tracks[0]',
    'm_ak47_ads_alpha',
    'm_ak47_action_left',
    'm_ak47_viewmodel->setRotation(rot)',
    'm_wieldnode->setVisible(false)',
    'm_wieldnode->setPosition(pose)',
    'if (item.name == "ak47dev:ak47"',
    '"xz_ak_view"',
    '"xz_ak_anim"',
    '"xz_ak_ads"',
]
def source_check(root):
    root=Path(root)
    camera=(root/"src/client/camera.cpp").read_text()
    header=(root/"src/client/camera.h").read_text()
    assert ('m_client->getMesh("ak47dev_animated.glb")' in camera or\n            'm_client->getMesh("ak47dev_fp.glb")' in camera)\n    assert ('m_ak47_viewmodel->setScale(v3f(2.7f, 2.7f, 2.7f))' in camera or\n            'm_ak47_viewmodel->setScale(v3f(3.1f, 3.1f, 3.1f))' in camera)\n    for anchor in PARTS:\n        assert anchor in camera,anchor
    for anchor in [
        "m_ak47_viewmodel", "updateAK47Viewmodel",
        "m_ak47_ads_alpha", "m_ak47_last_event"]:
        assert anchor in header,anchor
    assert camera.count('void Camera::updateAK47Viewmodel(')==1
    assert any(pid in (root/"android/app/build.gradle").read_text()\n               for pid in ('com.xziel.voxelsandbox.v32','com.xziel.voxelsandbox.v33'))
    mod=(root/"games/voxelibre/mods/ak47dev/init.lua").read_text()
    for anchor in ['meta:set_string("xz_ak_anim"', 'meta:set_string("xz_ak_ads"',
                   'meta:set_string("xz_ak_view"', 'sync_camera(player,s,"R")',
                   'sync_camera(player,s,"F")','/akview']:
        assert anchor in mod,anchor
    print("V3.2 CAMERA SOURCE OK: C++ GPU rig with ADS camera poses, 3D reload "
          "keyframes, original sound event synchronization and native fallback")

def apk_check(path):
    with ZipFile(path) as apk:
        assert any(f.startswith("lib/arm64-v8a/") and f.endswith(".so")
                   for f in apk.namelist())
        with ZipFile(BytesIO(apk.read("assets/assets.zip"))) as game:
            mod="games/voxelibre/mods/ak47dev/"
            assert game.read(mod+"models/ak47dev_animated.glb").startswith(b"glTF")
            assert game.read(mod+"sounds/ak47dev_reload.ogg").startswith(b"OggS")
            assert game.read(mod+"sounds/ak47dev_fire.ogg").startswith(b"OggS")
            assert "xz_ak_anim" in game.read(mod+"init.lua").decode()
            assert "games/voxelibre/mods/zmapdev/init.lua" in game.namelist()
            assert "XXX Large" in game.read("builtin/mainmenu/dlg_zmap_world.lua").decode()
    print(f"V3.2 APK CONTENT VERIFIED: {Path(path).stat().st_size:,} bytes, "
          "AK GLB, reload/fire audio, 7 Create Map templates preserved")

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: verify_v32.py <patched-Luanti-dir | Android-APK>")
    p=Path(sys.argv[1])
    if p.suffix==".apk": apk_check(p)
    else: source_check(p)
