#!/usr/bin/env python3
"""Stage ONLY authentic, structurally verified IW3 gun+hands GLBs for Luanti.

Writes a PRIVATE native preview mod. No copyrighted meshes, images, sounds or
animation keyframes are published in a public GitHub repo or workflow artifact.
Source stats from WeaponDef are required for a gun to do any hitscan damage.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import struct
import zlib

MAX_FILE = 32 * 1024 * 1024
REQUIRED_ANIMS = ("idle", "ads", "fire", "reload")
CATEGORIES = {"assault","smg","shotgun","lmg","sniper","marksman","pistol"}
TIME_FIELDS = {"fire": "fireTime", "reload": "reloadTime",
               "reload_empty": "reloadEmptyTime"}


def source_seconds(number):
    # Real source dump (COD4 common_mp.ff) contains SECONDS, verified:
    # AK-47 fireTime=0.085, reloadTime=2.5, reloadEmptyTime=3.25.
    # Never misinterpret as milliseconds (0.000085 sec would be absurd).
    if not isinstance(number, (int, float)) or not (0.02 <= number <= 20):
        return None
    return float(number)


def parse_glb(path):
    with path.open("rb") as f:
        head=f.read(20)
        if len(head)!=20:
            raise ValueError("truncated GLB")
        magic,ver,size,jlen,jtype=struct.unpack("<4sIIII",head)
        if (magic!=b"glTF" or ver!=2 or size!=path.stat().st_size or
                jtype!=0x4E4F534A or jlen>MAX_FILE or jlen%4):
            raise ValueError("invalid GLB header or length")
        doc=json.loads(f.read(jlen))
    if not doc.get("meshes") or not doc.get("skins"):
        raise ValueError("GLB lacks skinned geometry")
    return {a["name"] for a in doc.get("animations",[])
            if isinstance(a,dict) and a.get("name") and a.get("channels")}


def png_solid(path, rgba):
    # Independently authored flat PBR-test colors; not copied COD4 textures.
    w=h=8
    pixels=b"".join(b"\x00"+bytes(rgba)*w for _ in range(h))
    def chunk(tag,data):
        return (struct.pack(">I",len(data))+tag+data+
                struct.pack(">I",zlib.crc32(tag+data)&0xffffffff))
    path.write_bytes(b"\x89PNG\r\n\x1a\n"+
        chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))+
        chunk(b"IDAT",zlib.compress(pixels))+
        chunk(b"IEND",b""))


def icon_text_png(path: Path, title: str, *, small: str = ""):
    """Author an actual 96px labeled touch icon; never reuse one metal square."""
    from PIL import Image, ImageDraw, ImageFont
    image=Image.new("RGBA",(96,96),(16,24,35,255))
    d=ImageDraw.Draw(image)
    d.rounded_rectangle((3,3,92,92),radius=14,fill=(36,49,64,255),
                        outline=(177,203,226,255),width=3)
    try:
        font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",19)
        font2=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",11)
    except OSError:
        font=ImageFont.load_default()
        font2=font
    label=title[:8].upper()
    bounds=d.textbbox((0,0),label,font=font)
    tw=bounds[2]-bounds[0]
    d.text(((96-tw)/2,32),label,font=font,fill=(246,249,252,255))
    if small:
        label2=small[:11].upper()
        b=d.textbbox((0,0),label2,font=font2)
        d.text(((96-(b[2]-b[0]))/2,66),label2,font=font2,
               fill=(122,237,211,255))
    image.save(path,format="PNG",optimize=True)


def source_profile(original: dict, row: dict):
    numeric=row.get("numeric") or {}
    # These are original exact WeaponDef quantities, not older guessed counts.
    clip=numeric.get("clipSize")
    cap=numeric.get("maxAmmo")
    delay=source_seconds(numeric.get("fireTime"))
    normal=source_seconds(numeric.get("reloadTime"))
    empty=source_seconds(numeric.get("reloadEmptyTime"))
    dmg=numeric.get("damage")
    raw_type=(row.get("strings") or {}).get("fireType","").lower()
    fire_kind="".join(c for c in raw_type if c.isascii() and c.isalnum())
    if (not row.get("has_required_timing_and_ammo") or
            not isinstance(clip,(int,float)) or not 1<=clip<=250 or
            not isinstance(cap,(int,float)) or cap<clip or cap>10000 or
            not delay or not .035<=delay<=5 or
            not normal or not .2<=normal<=20 or
            not empty or not .1<=empty<=20 or
            not isinstance(dmg,(int,float)) or not 1<=dmg<=250):
        return None
    if int(clip)!=clip or int(cap)!=cap:
        return None
    # Disable weapon mechanics for ambiguous original fire types, not fabricate.
    if fire_kind in {"fullauto", "auto", "fullyautomatic"}:
        fire_mode="auto"
    elif fire_kind in {"single", "semi", "semiauto", "singleshot"}:
        fire_mode="semi"
    elif fire_kind in {"burst", "burstfire", "burst3", "3roundburst"}:
        fire_mode="burst"
    else:
        return None
    return {
        "magazine_capacity":int(clip),"reserve_max":int(cap),
        "fire_interval_seconds":delay,
        "reload_seconds":normal,"reload_empty_seconds":empty,
        "damage":float(dmg),"fire_mode":fire_mode,
        "original_source_definition":row.get("source_definition_name")
    }


def stage(expected, animated, definitions, glbs: Path, output: Path):
    weapons=expected.get("weapons",[])
    if len(weapons)!=28 or len({w["id"] for w in weapons})!=28:
        raise ValueError("28 source identities required")
    if animated.get("target_unique_weapon_count")!=28:
        raise ValueError("authentic animated GLB report for 28 targets required")
    output.mkdir(parents=True,exist_ok=True)
    models=output/"models";models.mkdir(exist_ok=True)
    textures=output/"textures";textures.mkdir(exist_ok=True)
    png_solid(textures/"arsenal_flat_metal.png",(69,77,86,255))
    png_solid(textures/"arsenal_flat_hands.png",(165,110,87,255))
    icon_text_png(textures/"arsenal_menu.png","ARSENAL",small="TAP HERE")
    icon_text_png(textures/"arsenal_ammo.png","AMMO",small="REFILL")
    # Labels are source identities, not guessed 3D previews or screenshots.
    for info in weapons:
        icon_text_png(textures/("arsenal_icon_"+info["id"]+".png"),
                      info.get("name",info["id"]),small=info["id"])
    native=[]
    rejected={}
    profiles=[]
    for w in weapons:
        wid=w["id"]
        a=(animated.get("result") or {}).get(wid,{})
        d=(definitions.get("weapons") or {}).get(wid,{})
        if w.get("category") not in CATEGORIES:
            rejected[wid]="no implemented projectile physics for category"
            continue
        if not (a.get("source_glb_generated") and a.get("source_hands_generated")):
            rejected[wid]="no actual animated gun+hands source pair"
            continue
        gun=glbs/f"{wid}_real_source_experimental.glb"
        hands=glbs/f"{wid}_hands_source_experimental.glb"
        try:
            for original in (gun,hands):
                if not original.is_file() or original.stat().st_size>MAX_FILE:
                    raise ValueError("missing/oversized source GLB (32 MiB limit)")
            ga=parse_glb(gun); ha=parse_glb(hands)
            if not set(REQUIRED_ANIMS)<=ga or not set(REQUIRED_ANIMS)<=ha:
                raise ValueError("required original tracks absent from GLB bytes")
        except (OSError,ValueError,KeyError) as error:
            rejected[wid]=str(error)
            continue
        have_empty="reload_empty" in ga and "reload_empty" in ha
        profile=source_profile(w,d)
        metadata={
            "id":wid,"name":w["name"],"category":w["category"],
            "gun_model":f"arsenal_{wid}_gun.glb",
            "hands_model":f"arsenal_{wid}_hands.glb",
            "model_skins_verified":True,
            "source_glb_animation_names":sorted(ga&ha),
            "distinct_empty_reload_animation":have_empty,
            "original_stats_verified":bool(profile),
            # Shotguns require per-shell reload / pellet logic; sniper optics
            # and bolt actions need native calibrated scope+cycling. Preview
            # their real animated models, never pretend gameplay is complete.
            "gameplay_logic_enabled":bool(profile and
                                           w["category"] not in ("shotgun","sniper")),
            "audio_samples_present":False,
            "ads_sights_calibrated":False,
            "android_playtest_verified":False,
        }
        if profile:
            metadata.update(profile)
        shutil.copy2(gun,models/metadata["gun_model"])
        shutil.copy2(hands,models/metadata["hands_model"])
        native.append(wid)
        profiles.append(metadata)
    if not native:
        raise ValueError("no genuine native model pairs: cannot stage fake mod")
    shutil.copy2(Path(__file__).with_name("arsenal_mod")/"init.lua",output/"init.lua")
    shutil.copy2(Path(__file__).with_name("arsenal_mod")/"mod.conf",output/"mod.conf")
    runtime={
        "schema_version":1,"mode":"private_first_person_source_preview",
        "native_model_ids":native,"weapons":profiles,
        "native_models_verified_by_original_binary":len(native),
        "gameplay_logic_with_original_stats_and_empty_reload":sum(
            x["gameplay_logic_enabled"] for x in profiles),
        "runtime_pose_verified":False,
        "runtime_sounds_verified":False,
        "android_fps_verified":False,
        "commercial_license_cleared":False,
        "not_published_original_content":True,
        "rejected":rejected
    }
    (output/"arsenal_runtime.json").write_text(json.dumps(runtime,indent=2)+"\n")
    (output/"private_runtime_metadata.json").write_text(json.dumps(runtime,indent=2)+"\n")
    return runtime


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--expected",type=Path,required=True)
    p.add_argument("--animated",type=Path,required=True)
    p.add_argument("--definitions",type=Path,required=True)
    p.add_argument("--glbs",type=Path,required=True)
    p.add_argument("--private-output",type=Path,required=True)
    p.add_argument("--metadata",type=Path,required=True)
    args=p.parse_args()
    data=stage(json.loads(args.expected.read_text()),
               json.loads(args.animated.read_text()),
               json.loads(args.definitions.read_text()),
               args.glbs,args.private_output)
    # Only the manifest (names and original *numerical values*) may be
    # copied outside the transient private build directory.
    args.metadata.parent.mkdir(parents=True,exist_ok=True)
    args.metadata.write_text(json.dumps(data,indent=2)+"\n")
    print("PRIVATE_NATIVE_ARSENAL_GLBS",len(data["native_model_ids"]),
          "ORIGINAL_STATS_GAMEPLAY_LOGIC",
          data["gameplay_logic_with_original_stats_and_empty_reload"],
          "ANDROID_FPS_VERIFIED:NO")


if __name__=="__main__":
    main()
