#!/usr/bin/env python3
"""Fixed-camera technical FPS renders from original GLB skins and XANIM."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image
from render_pose_sequence import PoseScene, closest_clip
from render_mounted_viewhands import compose
from render_fps_camera_probe import projection_basis, render_perspective, WIDTH, HEIGHT, FOV, NEAR, make_grid

def camera_points(geometry, front):
    pts=np.vstack([m[0][::max(1,len(m[0])//1000)] for m in geometry])
    return pts@np.asarray(projection_basis(1,front)).T

def projected_stats(points, eye):
    p=points-eye
    good=p[:,2]>=NEAR
    front_fraction=float(good.mean())
    if not np.any(good):return None
    focal=(WIDTH*.5)/math.tan(math.radians(FOV*.5))
    x=.5+focal*p[good,0]/p[good,2]/WIDTH
    y=(HEIGHT*.5+15.-focal*p[good,1]/p[good,2])/HEIGHT
    minx,maxx=np.quantile(x,[.02,.98]);miny,maxy=np.quantile(y,[.02,.98])
    w=maxx-minx;h=maxy-miny;cx=(minx+maxx)*.5;cy=(miny+maxy)*.5
    visible=float(np.mean((x>=.02)&(x<=.98)&(y>=.14)&(y<=.92)))*front_fraction
    # Explicit clipping cost. Matching a target width cannot excuse overflow.
    overflow=max(0.,.02-minx)+max(0.,maxx-.98)+max(0.,.14-miny)+max(0.,maxy-.92)
    score=(overflow*9.+max(0.,.97-visible)*7.+(1.-front_fraction)*15.
           +abs(w-.43)*1.5+abs(h-.34)*1.2+abs(cx-.68)*1.2+abs(cy-.70)*1.2)
    return {"score":float(score),"visible_fraction":visible,"in_front_fraction":front_fraction,
        "overflow":float(overflow),"projected_bbox_2_to_98":list(map(float,(minx,maxx,miny,maxy))),
        "projected_center":[float(cx),float(cy)],"projected_size":[float(w),float(h)]}

def camera_stats(geometry,eye,front):
    return projected_stats(camera_points(geometry,front),np.asarray(projection_basis(1,front))@eye)

def source_model_frame(rifle,hands):
    ri=closest_clip(rifle,"idle");hi=closest_clip(hands,"idle")
    if not ri or not hi:raise ValueError("missing original idle pair")
    rest=hands.tag(hands.world(hi,0.));gw=rifle.world(ri,0.)
    mount=rifle.tag(gw,"tag_ak47_mount");flash=rifle.tag(gw,"tag_flash")
    if rest is None or mount is None or flash is None:raise ValueError("original source tags required")
    native=rest@np.linalg.inv(mount);muzzle=(native@flash)[:3,3];grip=rest[:3,3]
    front=muzzle-grip;front/=max(1e-9,np.linalg.norm(front))
    combined,_=compose(rifle,hands,ri,hi,0,rest)
    xyz=np.vstack([m[0] for m in combined[:len(rifle.geometry)]])
    axial=xyz@front;span=float(np.ptp(axial))
    if span<=1.:raise ValueError("source rifle geometry collapsed")
    rear=grip+(float(np.min(axial))-float(grip@front))*front
    return ri,hi,rest,combined,front,muzzle,rear,span

def validation_poses(rifle,hands,rest,front):
    samples=[]
    for action in ("idle","fire","reload","reload_empty"):
        gc=closest_clip(rifle,action);hc=closest_clip(hands,action)
        if gc is None or hc is None:raise ValueError("missing original pair: "+action)
        duration=min(rifle.duration(gc),hands.duration(hc))
        fracs=[0.] if action=="idle" else ([0.,.5,1.] if action=="fire" else np.linspace(0.,1.,17))
        for f in fracs:
            geometry,_=compose(rifle,hands,gc,hc,duration*float(f),rest)
            samples.append((action,float(f),camera_points(geometry,front)))
    return samples

def rank_cameras(samples,front,rear,span):
    basis=np.asarray(projection_basis(1,front));right,up,_=basis;choices=[]
    for distance in (.08,.16,.24,.32,.45,.60,.80):
        for lateral in (-.26,-.20,-.14,-.08,-.02,.04,.10):
            for elevation in (.00,.04,.08,.12,.16,.20,.24):
                eye=rear-distance*span*front+lateral*span*right+elevation*span*up
                metrics=[projected_stats(p,basis@eye) for _,_,p in samples]
                if any(m is None for m in metrics):continue
                scores=np.asarray([m["score"] for m in metrics])
                # Complete timeline: idle cannot conceal a broken middle pose.
                score=.25*metrics[0]["score"]+.45*float(scores.mean())+.30*float(scores.max())
                worst=int(np.argmax(scores))
                choices.append({"score":round(score,6),"distance_behind_rear_fraction":distance,
                    "lateral_fraction":lateral,"height_fraction":elevation,"eye_xyz":eye.tolist(),
                    "idle_metrics":metrics[0],"minimum_visible_fraction":min(m["visible_fraction"] for m in metrics),
                    "maximum_overflow":max(m["overflow"] for m in metrics),
                    "worst_sample":{"action":samples[worst][0],"fraction":samples[worst][1],**metrics[worst]}})
    if not choices:raise ValueError("no viable complete-timeline camera")
    choices.sort(key=lambda c:c["score"]);return choices

def select(rifle,hands):
    source=source_model_frame(rifle,hands)
    _,_,rest,_,front,_,rear,span=source
    samples=validation_poses(rifle,hands,rest,front)
    return source,rank_cameras(samples,front,rear,span),samples

def gif_timing(duration,count):
    # GIF uses centiseconds; cumulative rounding avoids playback-time drift.
    ticks=np.rint(np.linspace(0.,duration*100.,count+1)).astype(int)
    delays=(np.diff(ticks)*10).tolist()
    if min(delays)<10:raise ValueError("GIF sampling exceeds centisecond timebase")
    return delays

def build(rifle_path,hands_path,output):
    rifle=PoseScene(rifle_path);hands=PoseScene(hands_path)
    source,rank,samples=select(rifle,hands)
    ri,hi,rest,combined,front,muzzle,rear,span=source
    output.mkdir(parents=True,exist_ok=True);eye=np.asarray(rank[0]["eye_xyz"])
    audit={"method":"OAT Y-up roots; fixed camera ranked on complete original action timelines",
        "camera_is_original_cod4":False,"hand_grip_verified":False,"ads_iron_sight_verified":False,
        "runtime_fps_verified":False,"coordinate_system":"OAT glTF Y-up",
        "original_mount_pair":["hands:tag_weapon","rifle:tag_ak47_mount"],
        "source_forward_direction":front.tolist(),"source_rifle_length":span,
        "candidates_tested":len(rank),"camera_validation_samples":len(samples),"best_candidates":rank[:8],
        "camera_fixed_for_all_animation_frames":True,"frames":[],"animations":{}}
    for i,c in enumerate(rank[:3],1):
        render_perspective(combined,np.asarray(c["eye_xyz"]),1,
            f"REAL COD4 AK47 | Y-UP HIP CAMERA #{i} | full reload ranked",
            output/f"ak47_fps_hipfire_candidate_{i}.png",forward_override=front)
    make_grid(output,[f"ak47_fps_hipfire_candidate_{i}.png" for i in range(1,4)],
              "ak47_fps_hipfire_top3_comparison.png",columns=3)
    for action,fps in (("idle",0),("fire",12),("fire_ads",12),("reload",24),("reload_empty",12)):
        gc=closest_clip(rifle,action);hc=closest_clip(hands,action)
        if gc is None or hc is None:raise ValueError("missing original pair: "+action)
        duration=min(rifle.duration(gc),hands.duration(hc))
        count=1 if fps==0 else max(2,int(math.ceil(duration*fps)))
        times=[0.] if fps==0 else np.linspace(0.,duration,count,endpoint=False)
        seq=[];records=[]
        for index,t in enumerate(times):
            geometry,mount=compose(rifle,hands,gc,hc,float(t),rest)
            name=f"ak47_fps_{action}_frame_{index:03d}.png"
            render=render_perspective(geometry,eye,1,
                f"REAL COD4 XANIM | {action.upper()} {t:.3f}/{duration:.3f}s | fixed Y-up camera",
                output/name,forward_override=front)
            record={"action":action,"fraction":float(t/duration) if duration else 0.,
                "time_seconds":float(t),"file":name,"rendered_faces":render["drawn_faces"],
                "mount_tag_error":mount["tag_alignment_error"],"framing":camera_stats(geometry,eye,front)}
            audit["frames"].append(record);records.append(record)
            if action in ("reload","reload_empty"):
                with Image.open(output/name) as im:
                    seq.append(im.convert("RGB").resize((880,512),Image.Resampling.LANCZOS))
        if seq:
            delays=gif_timing(duration,count)
            filename=("ak47_fps_original_reload_diagnostic.gif" if action=="reload"
                      else "ak47_fps_original_reload_empty_diagnostic.gif")
            seq[0].save(output/filename,format="GIF",save_all=True,append_images=seq[1:],
                duration=delays,loop=0,optimize=False,disposal=2)
            report={"name":filename,"frames":len(seq),"sample_rate":fps,"source_duration_s":duration,
                "gif_duration_s":sum(delays)/1000.,"camera_fixed":True,
                "note":"evaluated source XANIM poses; technical render, not gameplay"}
            audit["animations"][action]=report
            if action=="reload":audit["reload_gif"]=report
            chosen=np.rint(np.linspace(0,len(records)-1,9)).astype(int)
            make_grid(output,[records[i]["file"] for i in chosen],
                      f"ak47_fps_original_{action}_contact_sheet.png",columns=3)
    audit["full_render_minimum_visible_fraction"]=min(f["framing"]["visible_fraction"] for f in audit["frames"])
    audit["framing_within_screen_95pct"]=audit["full_render_minimum_visible_fraction"]>=.95
    (output/"fps-framing-audit.json").write_text(json.dumps(audit,indent=2)+"\n")
    print(json.dumps({"cameras_checked":len(rank),"timeline_samples":len(samples),
        "minimum_visible_fraction":rank[0]["minimum_visible_fraction"],
        "real_frames":len(audit["frames"]),"reload_gif":audit["reload_gif"]}))
    return audit

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--rifle",type=Path,required=True);p.add_argument("--hands",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();build(a.rifle,a.hands,a.output)

if __name__=="__main__":main()

