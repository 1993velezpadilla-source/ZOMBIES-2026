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


def compose(rifle,viewhands,gunclip,handclip,t,rest_hand_tag):
    rifle_mesh, gunpoints, gunworld=rifle.poses(gunclip,t)
    hand_mesh, handpoints, handworld=viewhands.poses(handclip,t)
    hand_tag=viewhands.tag(handworld)
    if hand_tag is None:
        raise ValueError("source COD4 hand skeleton missing tag_weapon")
    weapon_tag=rifle.tag(gunworld)
    if weapon_tag is not None:
        # Both tags are derived from actual imported bone trees, not guessed
        # per-weapon offsets. The local rifle tag is the attachment pivot.
        matrix=hand_tag@np.linalg.inv(weapon_tag)
        mode="original_tag_weapon_to_tag_weapon"
        err=float(np.linalg.norm((matrix@weapon_tag-hand_tag)[:3,3]))
    else:
        # If weapon GLB contains no tag_weapon, retain first-frame rifle
        # placement and follow the animated hand mount RELATIVELY.
        matrix=hand_tag@np.linalg.inv(rest_hand_tag)
        mode="original_hands_tag_weapon_delta_only_no_gun_tag"
        err=None
    mounted=[]
    for xyz,ix,colors in rifle_mesh:
        mounted.append((transform_points(xyz,matrix),ix,colors))
    combined=mounted+hand_mesh
    moved=np.vstack([g[0] for g in mounted])
    extent=max(.001,float(np.max(np.ptp(moved,axis=0))))
    d=measure_proximity(moved,handpoints)
    info={
      "mount_strategy":mode,
      "gun_anchor_present":weapon_tag is not None,
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
      "method":"skinned glTF XANIM on real COD4 voxel AK47 + source tag_weapon",
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
    baseline_gun=rifle.poses(idle_gun,0)[1]
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
                    path,camera=camera,geometry_override=combined)
                report["frames"].append({"action":action,"fraction":frac,"time_s":round(t,4),
                    "image":name,**meta})
            except (ValueError,IndexError,np.linalg.LinAlgError) as e:
                report["errors"][f"{action}:{frac}"]=str(e)[:200]
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
