#!/usr/bin/env python3
"""Assemble isolated V3 AK-47 prototype on an already-patched V2 Android tree.

AK shoot/reload/dryfire audio is sourced from CC0-licensed GunLib via GitHub
(publisher's README identifies those AK sounds as CC0 Freesound recordings).
Project Aether has no AK in our extracted WaW inventory; proprietary Aether
audio is deliberately not redistributed into this monetizable candidate.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

repo = Path(__file__).resolve().parents[3]
sounds = {
    "ak47dev_fire.ogg": "ak47_shot.ogg",
    "ak47dev_reload.ogg": "ak47_reload.ogg",
    "ak47dev_dry.ogg": "ak47_click.ogg",
}
base = "https://raw.githubusercontent.com/Deases/GunLib/main/sounds/"

def checked(path, old, new):
    s = path.read_text(encoding="utf8")
    if s.count(old) != 1:
        raise RuntimeError(f"{path}: found {s.count(old)} instances of {old!r}")
    path.write_text(s.replace(old,new),encoding="utf8")

def main():
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python patch_v3.py /path/to/luanti")
    root=Path(sys.argv[1]).resolve()
    android=root/"android/app"
    game=root/"games/voxelibre"
    assert (game/"mods/zmapdev/init.lua").is_file(), "V2 must be patched first"
    checked(android/"build.gradle",
            "applicationId 'com.xziel.voxelsandbox.v2'",
            "applicationId 'com.xziel.voxelsandbox.v3'")
    manifest=android/"src/main/AndroidManifest.xml"
    checked(manifest, "com.xziel.voxelsandbox.v2.fileprovider",
            "com.xziel.voxelsandbox.v3.fileprovider")
    checked(manifest, "com.xziel.voxelsandbox.v2.documents",
            "com.xziel.voxelsandbox.v3.documents")
    activity=android/"src/main/java/net/minetest/minetest/GameActivity.java"
    checked(activity,
            '"com.xziel.voxelsandbox.v2.fileprovider"',
            '"com.xziel.voxelsandbox.v3.fileprovider"')
    checked(android/"src/main/res/values/strings.xml",
            '<string name="label">Voxel Sandbox V2</string>',
            '<string name="label">Voxel Sandbox AK Test</string>')

    dest=game/"mods/ak47dev"
    dest.mkdir(parents=True,exist_ok=True)
    src=repo/"sandbox/luanti/v3/ak47dev"
    shutil.copyfile(src/"init.lua",dest/"init.lua")
    shutil.copyfile(src/"mod.conf",dest/"mod.conf")
    subprocess.run([sys.executable,str(repo/"sandbox/luanti/v3/build_ak47_assets.py"),
                    str(dest)],check=True)
    for wav in list((dest/"sounds").glob("*.wav")):
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                        "-i",str(wav),"-c:a","libvorbis","-q:a","4",
                        str(wav.with_suffix(".ogg"))],check=True)
        wav.unlink()

    for newname,oldname in sounds.items():
        dest_path=dest/"sounds"/newname
        url=base+oldname
        print(f"Fetching CC0 AK sound: {url}",flush=True)
        with urllib.request.urlopen(url,timeout=45) as src_stream:
            data=src_stream.read()
        if len(data)<5000 or not data.startswith(b"OggS"):
            raise RuntimeError("Invalid public CC0 sound file: "+oldname)
        dest_path.write_bytes(data)

    model=dest/"models/ak47dev_animated.glb"
    assert model.read_bytes()[:4]==b"glTF"
    for f in ["ak47dev_fire.ogg","ak47dev_reload.ogg","ak47dev_dry.ogg",
              "ak47dev_magout.ogg","ak47dev_magin.ogg","ak47dev_bolt.ogg"]:
        assert (dest/"sounds"/f).read_bytes().startswith(b"OggS"),f
    print(f"V3 READY: original 3D AK rig ({model.stat().st_size} bytes), "
          "mag+bolt+hand skeletal keyframes, authentic AK shot/reload from "
          "GunLib CC0, separate com.xziel.voxelsandbox.v3 package")
if __name__=="__main__":
    main()
