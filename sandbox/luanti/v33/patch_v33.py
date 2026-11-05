#!/usr/bin/env python3
"""V3.3 AK-47 Android patch: FPS-only model + corrected camera transforms.

The V3.2 APK has been physically tested on Android: gun visible and ADS moves,
but huge stock obstructs the screen and hip position clips into hotbar.
This patch does NOT claim to solve animation quality before a device test.
"""
from pathlib import Path
import subprocess
import sys

REPO=Path(__file__).resolve().parents[3]

def checked(path,old,new):
    s=path.read_text(encoding="utf8")
    n=s.count(old)
    if n!=1:
        raise RuntimeError(f"{path} found {n} occurrences of {old!r} (need one)")
    path.write_text(s.replace(old,new),encoding="utf8")

def main():
    if len(sys.argv)!=2:
        raise SystemExit("Usage: patch_v33.py /path/to/luanti")
    root=Path(sys.argv[1]).resolve()
    mod=root/"games/voxelibre/mods/ak47dev"
    app=root/"android/app"
    assert (mod/"models/ak47dev_animated.glb").exists(),(
        "V3, V3.1 and V3.2 patches must run before V3.3")
    subprocess.run([sys.executable,
        str(REPO/"sandbox/luanti/v33/build_fp_viewmodel.py"),str(mod)],check=True)
    cpp=root/"src/client/camera.cpp"
    checked(cpp,
        'm_client->getMesh("ak47dev_animated.glb")',
        'm_client->getMesh("ak47dev_fp.glb")')
    checked(cpp,
        "const v3f hip_pos(10.5f, -11.7f, 28.0f);",
        "const v3f hip_pos(8.0f, -6.5f, 31.0f);")
    checked(cpp,
        "const v3f ads_pos(0.0f, -1.9f, 29.0f);",
        "const v3f ads_pos(0.0f, -2.7f, 31.5f);")
    checked(cpp,
        "const v3f hip_rot(-2.0f, -14.0f, -1.0f);",
        "const v3f hip_rot(-2.0f, -10.0f, -3.0f);")
    checked(cpp,
        "m_ak47_viewmodel->setScale(v3f(2.7f, 2.7f, 2.7f));",
        "m_ak47_viewmodel->setScale(v3f(3.1f, 3.1f, 3.1f));")
    # Native fallback also uses a first-person mesh so a GLB loading
    # problem can no longer reintroduce the big buttstock into the lens.
    lua=mod/"init.lua"
    checked(lua,
        'mesh="ak47dev_static.obj",',
        'mesh="ak47dev_fp_static.obj",')
    checked(lua,
        "wield_scale={x=7.0,y=7.0,z=7.0},",
        "wield_scale={x=4.7,y=4.7,z=4.7},")
    # The V3.2 camera implements all animation and ADS logic; no server
    # weapon stat/behavior changes are needed here.
    checked(app/"build.gradle",
        "applicationId 'com.xziel.voxelsandbox.v32'",
        "applicationId 'com.xziel.voxelsandbox.v33'")
    manifest=app/"src/main/AndroidManifest.xml"
    checked(manifest,
        "com.xziel.voxelsandbox.v32.fileprovider",
        "com.xziel.voxelsandbox.v33.fileprovider")
    checked(manifest,
        "com.xziel.voxelsandbox.v32.documents",
        "com.xziel.voxelsandbox.v33.documents")
    activity=app/"src/main/java/net/minetest/minetest/GameActivity.java"
    checked(activity,
        '"com.xziel.voxelsandbox.v32.fileprovider"',
        '"com.xziel.voxelsandbox.v33.fileprovider"')
    checked(app/"src/main/res/values/strings.xml",
        '<string name="label">Voxel Sandbox AK FPS</string>',
        '<string name="label">Voxel Sandbox AK V33</string>')
    print("V3.3 READY: original 43-piece FPS model and 5-bone reload, center "
          "ADS sights, improved hipfire, independent package .v33")
if __name__=="__main__":
    main()
