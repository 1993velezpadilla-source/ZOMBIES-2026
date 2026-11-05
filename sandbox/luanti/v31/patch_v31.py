#!/usr/bin/env python3
"""Build Android V3.1 from already-patched V3 Luanti working tree.

Fix V3 missing first-person gun using native wield-node rendering;
retain original skinned GLB for experiments via /akrig on.
A third separate APK ID ensures earlier V1/V2/V3 apps stay intact.
"""
from pathlib import Path
import subprocess
import sys

REPO=Path(__file__).resolve().parents[3]

def checked(file,before,after):
    text=file.read_text(encoding="utf8")
    if text.count(before)!=1:
        raise RuntimeError(f"{file}: expected one {before!r}, got {text.count(before)}")
    file.write_text(text.replace(before,after),encoding="utf8")

def main():
    if len(sys.argv)!=2: raise SystemExit("Usage: patch_v31.py LUANTI_PATH")
    root=Path(sys.argv[1]).resolve()
    app=root/"android/app"
    mod=root/"games/voxelibre/mods/ak47dev"
    if not (mod/"models/ak47dev_animated.glb").exists():
        raise RuntimeError("V3 assets missing; run patch_v3 first")
    lua=(mod/"init.lua").read_text()
    if 'minetest.register_node(AK,{' not in lua:
        raise RuntimeError("Missing V3.1 native mesh wield fix")
    subprocess.run([sys.executable,str(REPO/"sandbox/luanti/v31/build_wield_mesh.py"),
                    str(mod)],check=True)
    checked(app/"build.gradle", "applicationId 'com.xziel.voxelsandbox.v3'",
            "applicationId 'com.xziel.voxelsandbox.v31'")
    manifest=app/"src/main/AndroidManifest.xml"
    checked(manifest,"com.xziel.voxelsandbox.v3.fileprovider",
            "com.xziel.voxelsandbox.v31.fileprovider")
    checked(manifest,"com.xziel.voxelsandbox.v3.documents",
            "com.xziel.voxelsandbox.v31.documents")
    checked(app/"src/main/java/net/minetest/minetest/GameActivity.java",
            '"com.xziel.voxelsandbox.v3.fileprovider"',
            '"com.xziel.voxelsandbox.v31.fileprovider"')
    checked(app/"src/main/res/values/strings.xml",
            '<string name="label">Voxel Sandbox AK Test</string>',
            '<string name="label">Voxel Sandbox AK Visible</string>')
    print("V3.1 READY: native wield mesh + animated GLB, "
          "package com.xziel.voxelsandbox.v31")
if __name__=="__main__":main()
