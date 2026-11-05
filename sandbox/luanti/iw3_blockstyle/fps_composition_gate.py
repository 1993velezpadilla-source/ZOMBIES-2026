#!/usr/bin/env python3
"""Data-driven COD4 AK47 FPS framing, original tag-mounted rifle + HANDS ONLY.

Generates REVIEW images/GIF from actual converted GLB+XANIM. This is not the
original game's camera, gameplay, a commercial asset, or proof of sight
alignment. No proprietary meshes, textures or keyframes leave private CI.

The camera is *fixed* across idle/fire/reload and fitted to an objectively
measured bounding box; it never follows the moving magazine.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
from render_pose_sequence import PoseScene, closest_clip
from render_mounted_viewhands import compose
from render_fps_camera_probe import projection_basis, render_perspective, WIDTH, HEIGHT, FOV, NEAR, make_grid


def camera_stats(geometry, eye, front):
    """Cheap numerical frame statistics BEFORE an expensive raster pass."""
    basis=projection_basis(1,front)
    pts=np.vstack([m[0][::max(1,len(m[0])//2500)] for m in geometry])
    points=pts-np.asarray(eye)
    camera=np.stack([points@basis[0],points@basis[1],points@basis[2]],axis=1)
    good=camera[:,2]>=NEAR
    if float(good.mean())<.9:
        return None
    focal=(WIDTH*.5)/math.tan(math.radians(FOV*.5))
    x=(WIDTH*.5 + focal*camera[good,0]/camera[good,2])/WIDTH
    y=(HEIGHT*.5 + 15. - focal*camera[good,1]/camera[good,2])/HEIGHT
    box=[float(np.quantile(q,v)) for q,v in ((x,.05),(x,.95),(y,.05),(y,.95))]
    minx,maxx,miny,maxy=box
    w=maxx-minx;h=maxy-miny
    c=((minx+maxx)*.5,(miny+maxy)*.5)
    visible=float(np.mean((x>=0)&(x<=1)&(y>=.12)&(y<=.92)))
    # Favor a modestly lower-right shooter weapon without blocking the reticle.
    score=(max(0., .78-visible)*3.3
            +abs(w-.56)*1.3+abs(h-.53)*1.3
            +abs(c[0]-.63)*.8+abs(c[1]-.63)*.9
            +max(0.,.18-w)*1.8
            +max(0.,.14-h)*1.4)
    return {"score":round(score,5),"visible_fraction":round(visible,4),
            "projected_bbox_5_to_95":[round(v,4) for v in box],
            "projected_center":[round(v,4) for v in c],
            "projected_size":[round(w,4),round(h,4)]}


def source_model_frame(rifle,hands):
    idle_rifle=closest_clip(rifle,"idle")
    idle_hands=closest_clip(hands,"idle")
    if not idle_rifle or not idle_hands:
        raise ValueError("No original COD4 rifle+hands idle")
    rest_tag=hands.tag(hands.world(idle_hands,0.))
    if rest_tag is None:
        raise ValueError("source hand rig lacks tag_weapon")
    gun_world=rifle.world(idle_rifle,0.)
    mount=rifle.tag(gun_world,"tag_ak47_mount")
    flash=rifle.tag(gun_world,"tag_flash")
    if mount is None or flash is None:
        raise ValueError("original AK-specific mount and muzzle anchors required")
    native=rest_tag@np.linalg.inv(mount)
    muzzle=(native@flash)[:3,3]
    grip=rest_tag[:3,3]
    forward=muzzle-grip
    forward/=max(1e-9,np.linalg.norm(forward))
    combined,_=compose(rifle,hands,idle_rifle,idle_hands,0,rest_tag,mode="native_pair")
    rifle_xyz=np.vstack([m[0] for m in combined[:len(rifle.geometry)]])
    axial=rifle_xyz@forward
    span=float(np.ptp(axial))
    if span<=1.:raise ValueError("original rifle geometry collapsed")
    rear=grip+(float(np.min(axial))-float(grip@forward))*forward
    return idle_rifle,idle_hands,rest_tag,combined,forward,muzzle,rear,span


def select(rifle,hands):
    (ri,hi,rest,combined,front,muzzle,rear,span)=source_model_frame(rifle,hands)
    right,up,_=projection_basis(1,front)
    choices=[]
    for distance in (.32,.45,.60,.8,1.05):
        for lateral in (-.26,-.16,-.08,0.,.08):
            for elevation in (.04,.11,.19,.28):
                # Lateral neg places the rifle right of the player crosshair;
                # forward remains the source muzzle direction.
                eye=(rear-distance*span*front
                    +lateral*span*right+elevation*span*up)
                metrics=camera_stats(combined,eye,front)
                if metrics is None:continue
                choices.append({"distance_behind_rear_fraction":distance,
                    "lateral_fraction":lateral,"height_fraction":elevation,
                    "eye_xyz":eye.round(6).tolist(), **metrics})
    if not choices:
        raise ValueError("no viable FPS camera candidate")
    choices.sort(key=lambda c:c["score"])
    return (ri,hi,rest,combined,front,muzzle,rear,span),choices


def build(rifle_path,hands_path,output):
    rifle=PoseScene(rifle_path);hands=PoseScene(hands_path)
    source,rank=select(rifle,hands)
    idle_rifle,idle_hands,rest,combined,front,muzzle,rear,span=source
    output.mkdir(parents=True,exist_ok=True)
    audit={"method":"quantitative world-space camera framing from ORIGINAL COD4 tag pair + voxel vertices",
        "camera_is_original_cod4":False,"hand_grip_verified":False,
        "ads_iron_sight_verified":False,"runtime_fps_verified":False,
        "original_mount_pair":["hands:tag_weapon","rifle:tag_ak47_mount"],
        "source_forward_direction":front.round(5).tolist(),
        "source_rifle_length":round(span,5),
        "candidates_tested":len(rank),"best_candidates":rank[:8],
        "camera_fixed_for_all_animation_frames":True,
        "frames":[]}
    # Render top three objectively ranked shots to expose possible scoring
    # failure; do not hand-select a pose and call that verified.
    for index,candidate in enumerate(rank[:3],1):
        path=output/f"ak47_fps_hipfire_candidate_{index}.png"
        render_perspective(combined,np.asarray(candidate["eye_xyz"]),1,
            f"AK47 COD4 VOXEL | HIPFIRE CANDIDATE #{index} | idle (diagnostic)",
            path,forward_override=front)
    make_grid(output,[f"ak47_fps_hipfire_candidate_{i}.png" for i in range(1,4)],
              "ak47_fps_hipfire_top3_comparison.png",columns=3)
    best=rank[0]
    eye=np.asarray(best["eye_xyz"])
    # ONE camera for all frames. No per-frame perspective recentering.
    actions=(("idle",[0]),("fire",[0,.50]),("fire_ads",[.5]),
             ("reload",[0,.25,.5,.75,.95]),
             ("reload_empty",[0,.5,.95]))
    for action,fracs in actions:
        gc=closest_clip(rifle,action)
        hc=closest_clip(hands,action)
        if gc is None or hc is None:
            audit["frames"].append({"action":action,"error":"missing corresponding original source clip"})
            continue
        duration=min(rifle.duration(gc),hands.duration(hc))
        for fraction in fracs:
            t=duration*fraction
            geometry,mount=compose(rifle,hands,gc,hc,t,rest,mode="native_pair")
            name=f"ak47_fps_{action}_{int(round(fraction*100)):03d}.png"
            render=render_perspective(geometry,eye,1,
                 f"REAL AK47 XANIM | {action.upper()} {int(round(fraction*100))}% | candidate HIP camera",
                 output/name,forward_override=front)
            audit["frames"].append({"action":action,"fraction":fraction,
                 "time_seconds":round(t,4),"file":name,
                 "rendered_faces":render["drawn_faces"],
                 "mount_tag_error":mount["tag_alignment_error"]})
    reload_frames=[x for x in audit["frames"] if x["action"]=="reload" and "file" in x]
    if len(reload_frames)!=5:
        raise ValueError("five real reload frames required for timing proof")
    seq=[]
    for frame in reload_frames:
        with Image.open(output/frame["file"]) as im:
            seq.append(im.convert("RGB").resize((770,448),Image.Resampling.LANCZOS))
    gif_path=output/"ak47_fps_original_reload_diagnostic.gif"
    # Original XANIM reload time, split across 5 snapshots. It is a coarse
    # 5-frame diagnostic, NOT original 30/60fps keyframe capture.
    duration_s=reload_frames[-1]["time_seconds"] / .95
    ms=int(round(duration_s*1000*.2375))
    seq[0].save(gif_path,format="GIF",save_all=True,append_images=seq[1:],
        duration=[ms]*5,loop=0,optimize=True)
    audit["reload_gif"]={"name":gif_path.name,"frames":5,
        "duration_s_approx":round(duration_s,3),
        "note":"5 sampled real XANIM poses with same diagnostic FPS camera; not gameplay"}
    sheet=[f["file"] for f in reload_frames]
    make_grid(output,sheet,"ak47_fps_original_reload_contact_sheet.png",columns=3)
    (output/"fps-framing-audit.json").write_text(json.dumps(audit,indent=2)+"\n")
    print(json.dumps({"cameras_checked":len(rank),
       "best_camera":rank[0],
       "real_frame_count":sum("file" in f for f in audit["frames"]),
       "original_reload_duration":duration_s,
       "five_frame_reload_gif":gif_path.name}))
    return audit


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--rifle",type=Path,required=True)
    p.add_argument("--hands",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    build(args.rifle,args.hands,args.output)


if __name__=="__main__":
    main()
