#!/usr/bin/env python3
"""First-person perspective probe of real COD4 AK47 and original animated hands.

This is NOT a simulated game screenshot. It evaluates skinned glTF vertices
from original XANIM for rifle and hands in the same bone-driven scene and
then projects them through independent, labelled candidate cameras.

No extracted model, bone matrix, texture or animation keyframes are uploaded.
Only raster previews and non-reversible metadata leave private CI.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from render_pose_sequence import PoseScene, closest_clip
from render_mounted_viewhands import compose

WIDTH, HEIGHT = 1100, 640
FOV = 75.0
NEAR = 0.25
BG = (21, 24, 31)


def projection_basis(sign=1):
    # IW3 X-model axes documented by original source probe: +X = model
    # forward, +Z = up. -X is a diagnostic alternative, NOT a claim.
    forward = np.array([float(sign), 0., 0.])
    up = np.array([0., 0., 1.])
    right = np.cross(forward, up)
    return right, up, forward


def project_point(point, basis, camera):
    right, up, forward = basis
    p = np.asarray(point, dtype=float) - camera
    return np.array([float(np.dot(p, right)), float(np.dot(p, up)),
                     float(np.dot(p, forward))])


def clip_against_near(poly, near):
    out = []
    prev = poly[-1]
    prev_inside = prev[2] >= near
    for current in poly:
        inside = current[2] >= near
        if inside != prev_inside:
            denom = current[2] - prev[2]
            if abs(denom) > 1e-10:
                factor = (near - prev[2]) / denom
                out.append(prev + factor*(current-prev))
        if inside:
            out.append(current)
        prev = current
        prev_inside = inside
    return out


def render_perspective(geometry, camera, sign, label, outfile, fov=FOV):
    basis = projection_basis(sign)
    cx,cy = WIDTH/2, HEIGHT/2+15
    focal = (WIDTH/2)/math.tan(math.radians(fov/2))
    im=Image.new('RGB',(WIDTH,HEIGHT),BG)
    draw=ImageDraw.Draw(im)
    # Crosshair at the real optical center. No fabricated ADS claim.
    draw.line((cx-10,cy,cx+10,cy),fill=(72,94,116),width=1)
    draw.line((cx,cy-10,cx,cy+10),fill=(72,94,116),width=1)
    triangles=[]
    near_front=0
    visible=0
    rendered_faces=0
    source_faces=0
    for positions,indices,colors in geometry:
        pts=np.array([project_point(p,basis,camera) for p in positions])
        near_front+=int(np.count_nonzero(pts[:,2]>=NEAR))
        source_faces+=len(indices)//3
        for i in range(0,len(indices),3):
            ids=indices[i:i+3]
            polygon=clip_against_near([pts[j] for j in ids],NEAR)
            if len(polygon)<3:
                continue
            screen=[]
            for v in polygon:
                X=cx + focal*v[0]/v[2]
                Y=cy - focal*v[1]/v[2]
                screen.append((float(X),float(Y)))
            if (max(v[0] for v in screen)<0 or min(v[0] for v in screen)>WIDTH
                or max(v[1] for v in screen)<0 or min(v[1] for v in screen)>HEIGHT):
                continue
            rgb=tuple(int(np.clip(np.mean(colors[ids,col])*255,28,235))
                      for col in range(3))
            depth=float(np.mean([v[2] for v in polygon]))
            # Moderate facet illumination, still actual GLB palette.
            p,q,r=polygon[:3]
            normal=np.cross(q-p,r-p)
            ratio=np.linalg.norm(normal)
            shade=.83+.16*abs(float(normal[2]/ratio)) if ratio>1e-9 else 1.
            color=tuple(int(np.clip(x*shade,22,245)) for x in rgb)
            triangles.append((depth,screen,color))
            visible+=1
    # Painter sort: far triangles before near ones.
    triangles.sort(key=lambda x:x[0], reverse=True)
    for depth,poly,color in triangles:
        draw.polygon(poly,fill=color)
        rendered_faces+=1
    draw.rectangle((0,0,WIDTH,76),fill=(14,17,22))
    draw.text((18,16),label,fill=(233,238,246))
    draw.text((18,43),f"real original XANIM + voxel geometry  |  75deg FOV  |  {'+X' if sign>0 else '-X'} forward",fill=(179,196,210))
    draw.rectangle((0,HEIGHT-50,WIDTH,HEIGHT),fill=(14,17,22))
    draw.text((18,HEIGHT-32),"PERSPECTIVE PROBE • NOT VERIFIED FPS ADS/RELOAD • NOT A GAME SCREENSHOT",fill=(237,186,109))
    outfile.parent.mkdir(parents=True,exist_ok=True)
    im.save(outfile,optimize=True)
    return {"source_faces":source_faces,"drawn_faces":rendered_faces,
            "source_vertices_in_front":near_front, "near":NEAR,
            "camera_origin":[round(float(v),4) for v in camera],
            "camera_forward":'+X' if sign>0 else '-X'}


def gather_source_camera(hands, clip):
    world=hands.world(clip,0.)
    matches=[(i,n.get('name','')) for i,n in enumerate(hands.nodes)
             if 'camera' in n.get('name','').lower()]
    tags={name:[round(float(v),4) for v in world[idx][:3,3]]
          for idx,name in matches}
    if not matches:return None,tags
    selected=next(((i,name) for i,name in matches if name.lower()=='tag_camera'),
                  matches[0])
    return world[selected[0]][:3,3].copy(),tags


def make_grid(output, names, dest, columns=2):
    files=[output/n for n in names if (output/n).exists()]
    if not files:return
    size=(720,420)
    rows=math.ceil(len(files)/columns)
    dest_img=Image.new('RGB',(size[0]*columns,size[1]*rows),BG)
    for i,file in enumerate(files):
        with Image.open(file) as f:
            photo=ImageOps.pad(f.convert('RGB'),size,method=Image.Resampling.LANCZOS)
            dest_img.paste(photo,((i%columns)*size[0],(i//columns)*size[1]))
    dest_img.save(output/dest,optimize=True)


def run(rifle_path, hands_path, output):
    rifle=PoseScene(rifle_path)
    hands=PoseScene(hands_path)
    gun_idle=closest_clip(rifle,'idle')
    hand_idle=closest_clip(hands,'idle')
    if not gun_idle or not hand_idle:
        raise ValueError("not enough original idle animations")
    hand_rest=hands.tag(hands.world(hand_idle,0.))
    if hand_rest is None:
        raise ValueError("viewhands lacks original tag_weapon")
    camtag,tags=gather_source_camera(hands,hand_idle)
    candidates={"original_origin":np.zeros(3)}
    if camtag is not None:
        candidates["original_hand_tag_camera"]=camtag
    source_tags={
        "hands_tag_weapon_exists":True,
        "hands_tag_camera_candidates":tags,
        "rifle_tag_iron_sight":any(n.get("name","").lower()=="tag_iron_sight"
                                  for n in rifle.nodes),
        "rifle_tag_weapon":any(n.get("name","").lower()=="tag_weapon"
                               for n in rifle.nodes),
        "rifle_relevant_joint_names":[n.get("name","") for n in rifle.nodes
            if any(w in n.get("name","").lower() for w in ('sight','mag','tag','bolt'))][:40],
        "hand_relevant_joint_names":[n.get("name","") for n in hands.nodes
            if any(w in n.get("name","").lower() for w in ('camera','weapon','wrist','hand'))][:40],
    }
    results=[]
    for strategy in ("relative_delta","direct_tag"):
        for view,origin in candidates.items():
            for sign in (1,-1):
                for action,fraction in (("idle",0.),("reload",.50)):
                    gc=closest_clip(rifle,action)
                    hc=closest_clip(hands,action)
                    if not gc or not hc:continue
                    t=min(rifle.duration(gc),hands.duration(hc))*fraction
                    combined,meta=compose(rifle,hands,gc,hc,t,hand_rest,mode=strategy)
                    stem=f"{strategy}_{view}_{'posx' if sign>0 else 'negx'}_{action}"
                    report=render_perspective(combined,origin,sign,
                         f"{strategy.upper()} | {view} | {action.upper()} @ {int(fraction*100)}%",
                         output/(stem+".png"))
                    results.append({"name":stem+".png","strategy":strategy,"view":view,
                       "forward":'+X' if sign>0 else '-X',"action":action,
                       "fraction":fraction,
                       **report,"hand_proximity_normalized":meta.get("hand_proximity_normalized_by_rifle_extent"),
                       "visually_approved":False})
    output.mkdir(parents=True,exist_ok=True)
    # Each contact sheet compares idle/reload on two camera positions/directions.
    for strategy in ("relative_delta","direct_tag"):
        names=[f"{strategy}_{view}_{axis}_{action}.png"
                for view in candidates for axis in ("posx","negx")
                for action in ("idle","reload")]
        make_grid(output,names,"ak47_fps_"+strategy+"_camera_comparison.png",2)
    audit={"source": "real privately converted COD4 skinned XANIM voxel rifle + viewhands",
           "source_tags":source_tags,"camera_candidates":list(candidates),
           "projections":results,"gameplay_verified":False,"camera_calibrated":False,
           "ads_verified":False,"hand_grip_verified":False,
           "private_original_geometry_exported":False}
    (output/"fps-camera-audit.json").write_text(json.dumps(audit,indent=2)+"\n")
    print(json.dumps({"frames":len(results),"tag_camera":camtag is not None,
      "camera_candidates":list(candidates),
      "source_tags":source_tags,
      "results":[{"view":x["view"],"strategy":x["strategy"],"action":x["action"],
                  "forward":x["forward"],"faces":x["drawn_faces"]} for x in results]}))
    if not any(x["drawn_faces"]>40 for x in results):
        raise ValueError("all real perspective projections blank")
    return audit


def main():
    a=argparse.ArgumentParser()
    a.add_argument('--rifle',type=Path,required=True)
    a.add_argument('--hands',type=Path,required=True)
    a.add_argument('--output',type=Path,required=True)
    args=a.parse_args()
    run(args.rifle,args.hands,args.output)


if __name__=='__main__':
    main()
