#!/usr/bin/env python3
"""Mount the REAL IW3 AK47 voxel GLB onto original skinned viewhands tag_weapon.

Pure diagnostic prototype: exact source XANIM pose sampling, source node
transforms and skinned cuboid vertices. Generates screenshot-only review
artifacts. We deliberately do not claim a proper grip/reload/ADS from an
attachment transform alone. No COD4 mesh or keyframes leave private CI.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
from render_pose_sequence import PoseScene, camera_params, closest_clip, draw_pose

ACTIONS=("idle","fire","fire_ads","reload","reload_empty")
TIMES=(0.0,0.25,0.50,0.75,0.95)
OAT_TO_NATIVE=np.array([[1.,0,0,0],[0,0,-1,0],[0,1,0,0],[0,0,0,1]])


def transform_points(points, matrix):
    hom=np.c_[points,np.ones((len(points),1))]
    transformed=hom@matrix.T
    denom=transformed[:,3]
    if np.any(np.abs(denom)<1e-8):
        raise ValueError("invalid homogenous bone attachment")
    xyz=transformed[:,:3]/denom[:,None]
    if not np.all(np.isfinite(xyz)):
        raise ValueError("nonfinite mounted geometry")
    return xyz


def measure_proximity(rifle, hands):
    # Representative point distances are only a structural sanity metric.
    # They do NOT establish finger anatomy or proper magazine manipulation.
    rs=rifle[::max(1,len(rifle)//320)][:320]
    hs=hands[::max(1,len(hands)//320)][:320]
    x=hs[:,None,:]-rs[None,:,:]
    d=np.linalg.norm(x,axis=2)
    return float(np.median(np.min(d,axis=1)))


def compose(rifle,viewhands,gunclip,handclip,t,rest_hand_tag,mode='iw3_dobj',*,hand_layers=(),gun_layers=()):
    rifle_mesh, gunpoints, gunworld=rifle.poses(gunclip,t,layers=gun_layers)
    hand_mesh, handpoints, handworld=viewhands.poses(handclip,t,layers=hand_layers)
    hand_tag=viewhands.tag(handworld)
    if hand_tag is None:
        raise ValueError("source COD4 hand skeleton missing tag_weapon")
    # Keep the earlier tag-pair hypothesis for A/B review. CG_RegisterWeapon
    # actually attaches the gun model root under the hands' tag_weapon.
    anchor_name=next((name for name in ("tag_ak47_mount","tag_weapon")
                      if rifle.tag(gunworld,name) is not None),None)
    weapon_tag=rifle.tag(gunworld,anchor_name) if anchor_name else None
    if mode == "iw3_dobj":
        # CG_RegisterWeapon attaches the gun MODEL ROOT to hands.tag_weapon.
        # tag_ak47_mount is not the rifle-to-hands socket. Remove only OAT's
        # global basis C; preserve the rifle's own native root animation.
        matrix=hand_tag@OAT_TO_NATIVE
        mode="iw3_dobj_model_root_to_hands_tag_weapon"
        err=float(np.linalg.norm(matrix@np.linalg.inv(OAT_TO_NATIVE)-hand_tag))
    elif mode == "native_pair":
        if weapon_tag is None:
            raise ValueError("native_pair needs the original rifle tag_ak47_mount")
        matrix=hand_tag@np.linalg.inv(weapon_tag)
        mode="original_tag_weapon_to_tag_ak47_mount"
        err=float(np.linalg.norm((matrix@weapon_tag-hand_tag)[:3,3]))
    elif mode == "direct_tag":
        # Old Godot BoneAttachment3D path: assumes the rifle's root origin
        # coincides with native grip anchor. This assumption was WRONG.
        matrix=hand_tag
        mode="original_hands_tag_weapon_direct_attachment"
        err=None
    elif mode == "relative_delta":
        # Previous scratch placement, only for explicit A/B diagnostics.
        matrix=hand_tag@np.linalg.inv(rest_hand_tag)
        mode="original_hands_tag_weapon_delta_only"
        err=None
    else:
        raise ValueError("unsupported attachment mode")
    mounted=[]
    for xyz,ix,colors in rifle_mesh:
        mounted.append((transform_points(xyz,matrix),ix,colors))
    combined=mounted+hand_mesh
    moved=np.vstack([g[0] for g in mounted])
    extent=max(.001,float(np.max(np.ptp(moved,axis=0))))
    d=measure_proximity(moved,handpoints)
    info={
      "mount_strategy":mode,
      "gun_anchor_present":True if mode=="iw3_dobj_model_root_to_hands_tag_weapon" else weapon_tag is not None,
      "gun_anchor_name":"native_model_root" if mode=="iw3_dobj_model_root_to_hands_tag_weapon" else anchor_name,
      "hand_anchor_present":True,
      "tag_alignment_error":round(err,7) if err is not None else None,
      "hand_point_to_rifle_median_nearest_distance":round(d,4),
      "hand_proximity_normalized_by_rifle_extent":round(d/extent,4),
      "grip_verified":False,
      "ads_verified":False,
      "frame_pose_generated_from_real_xanim":True,
    }
    return combined,info


def build(rifle_path,hand_path,output):
    output.mkdir(parents=True,exist_ok=True)
    rifle=PoseScene(rifle_path)
    hands=PoseScene(hand_path)
    idle_gun=closest_clip(rifle,"idle")
    idle_hand=closest_clip(hands,"idle")
    if not idle_gun or not idle_hand:
        raise ValueError("missing original AK47 idle on weapon or hands")
    rest_tag=hands.tag(hands.world(idle_hand,0))
    if rest_tag is None:
        raise ValueError("hands GLB missing tag_weapon; cannot mount physically")
    report={
      "method":"IW3 CG_RegisterWeapon DObj model-root attachment under hands tag_weapon; OAT basis removed once",
      "gun_animations":len(rifle.animations),
      "hand_animations":len(hands.animations),
      "hands_attached_structurally":True,
      "hand_grip_verified":False,
      "reload_visual_approved":False,
      "ADS_iron_sights_verified":False,
      "runtime_android_verified":False,
      "frames":[],
      "errors":{},
    }
    baseline,_=compose(rifle,hands,idle_gun,idle_hand,0,rest_tag)
    baseline_gun=np.vstack([mesh[0] for mesh in baseline])
    camera=camera_params(baseline_gun,orientation=(28,25))
    for action in ACTIONS:
        gunclip=closest_clip(rifle,action)
        handclip=closest_clip(hands,action)
        if not gunclip or not handclip:
            report["errors"][action]="missing matching action in original rifle/hands"
            continue
        duration=min(rifle.duration(gunclip),hands.duration(handclip))
        timeline=(0.0,) if duration<=0 else TIMES
        for frac in timeline:
            t=duration*frac
            try:
                combined,meta=compose(rifle,hands,gunclip,handclip,t,rest_tag)
                name=f"ak47_mounted_{action}_{int(round(frac*100)):03d}.png"
                path=output/name
                draw_pose(rifle,gunclip,t,
                    f"COD4 BLOCK AK + VIEW HANDS / {action.upper()} / {int(frac*100)}%",
                    path,camera=camera,geometry_override=combined,
                    surfaces_override=rifle.posed_surfaces()+hands.posed_surfaces())
                report["frames"].append({"action":action,"fraction":frac,"time_s":round(t,4),
                    "image":name,**meta})
            except (ValueError,IndexError,np.linalg.LinAlgError) as e:
                report["errors"][f"{action}:{frac}"]=str(e)[:200]
    # Compare exact original dual-anchor tag pair against TWO older fallback
    # strategies using identical camera and original XANIM timestamps.
    comparison=[]
    for action,fraction in (("idle",0.0),("reload",.5),("reload_empty",.5)):
        gunclip=closest_clip(rifle,action)
        handclip=closest_clip(hands,action)
        if not gunclip or not handclip:
            continue
        duration=min(rifle.duration(gunclip),hands.duration(handclip))
        t=duration*fraction
        for strategy in ("iw3_dobj","native_pair","direct_tag"):
            try:
                combo,stat=compose(rifle,hands,gunclip,handclip,t,rest_tag,mode=strategy)
                img=output/f"ak47_compare_{strategy}_{action}.png"
                # Use per-strategy idle/camera framing only for the second
                # comparison sheet; mounted-frames main sheet uses fixed camera.
                draw_pose(rifle,gunclip,t,
                    f"COD4 TAG MOUNT TEST: {strategy} / {action}",
                    img,geometry_override=combo,camera=camera,
                    surfaces_override=rifle.posed_surfaces()+hands.posed_surfaces())
                comparison.append({"action":action,"candidate":strategy,
                                   "image":img.name,**stat})
            except (ValueError,np.linalg.LinAlgError) as exc:
                report["errors"][f"comparison_{strategy}_{action}"]=str(exc)[:160]
    report["mount_candidates"]=comparison
    pairs=[]
    for action in ("idle","reload","reload_empty"):
        for strategy in ("iw3_dobj","native_pair","direct_tag"):
            name=output/f"ak47_compare_{strategy}_{action}.png"
            if name.exists():
                with Image.open(name) as im:
                    pairs.append(ImageOps.pad(im.convert("RGB"),(825,488)))
    if pairs:
        check=Image.new("RGB",(2475,488*math.ceil(len(pairs)/3)),(20,22,29))
        for i,img in enumerate(pairs):
            check.paste(img,((i%3)*825,(i//3)*488))
        check.save(output/"ak47_tag_strategy_comparison.png",optimize=True)
    if not report["frames"]:
        raise ValueError("no combined weapon+hand frames rendered")
    # Side-by-side images share the SAME camera so an apparent grip error cannot
    # be hidden by automatically zooming to different pose bounds.
    images=[]
    for action,frac in (("idle",0),("fire",.50),("reload",0),("reload",.50),
                        ("reload",.95),("reload_empty",.50)):
        p=output/f"ak47_mounted_{action}_{int(round(frac*100)):03d}.png"
        if p.is_file():
            x=Image.open(p).convert("RGB")
            images.append(ImageOps.pad(x,(825,488)))
    if images:
        rows=math.ceil(len(images)/2)
        sheet=Image.new("RGB",(1650,rows*488),(20,22,29))
        for i,im in enumerate(images):
            sheet.paste(im,((i%2)*825,(i//2)*488))
        sheet.save(output/"ak47_real_viewhands_mounted_contact_sheet.png",optimize=True)
    (output/"mount-audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({
       "rendered_frames":len(report["frames"]),
       "mount_errors":report["errors"],
       "mount_strategy":sorted({x["mount_strategy"] for x in report["frames"]}),
       "max_tag_error":max((x["tag_alignment_error"] or 0 for x in report["frames"]),default=0),
       "mean_relative_hand_rifle_proximity":round(float(np.mean(
           [x["hand_proximity_normalized_by_rifle_extent"] for x in report["frames"]])),4),
       "grip_verified":False
    }))
    if "reload" in {x["action"] for x in report["frames"]} and (
        output/"ak47_real_viewhands_mounted_contact_sheet.png").is_file():
        return report
    raise ValueError("original rifle/hand reload pair could not be rendered")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--rifle",type=Path,required=True)
    p.add_argument("--hands",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    build(args.rifle,args.hands,args.output)

if __name__=="__main__":
    main()

