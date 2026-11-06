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
from render_mounted_viewhands import compose, OAT_TO_NATIVE

WIDTH, HEIGHT = 1100, 640
FOV = 75.0
NEAR = 0.25
BG = (21, 24, 31)


def projection_basis(sign=1, forward_override=None, roll_degrees=0):
    # A tag_flash direction is stronger evidence than assuming world +X.
    # +X/-X are retained strictly for A/B coordinate system diagnostics.
    forward = (np.asarray(forward_override,dtype=float) if forward_override is not None
               else np.array([float(sign),0.,0.]))
    length=float(np.linalg.norm(forward))
    if length<1e-8:raise ValueError("degenerate original muzzle direction")
    forward=forward/length
    # OAT's glTF is Y-up, including converted animation roots.
    up=np.array([0.,1.,0.])
    if abs(float(np.dot(forward,up)))>.95:
        up=np.array([0.,0.,1.])
    right=np.cross(forward,up)
    right=right/max(1e-8,float(np.linalg.norm(right)))
    up=np.cross(right,forward)
    if roll_degrees:
        theta=math.radians(float(roll_degrees))
        right,up=(right*math.cos(theta)+up*math.sin(theta),
                  up*math.cos(theta)-right*math.sin(theta))
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


def render_perspective(geometry, camera, sign, label, outfile, fov=FOV, forward_override=None, roll_degrees=0):
    basis = projection_basis(sign,forward_override,roll_degrees)
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
        pts=(positions-np.asarray(camera))@np.asarray(basis).T
        near_front+=int(np.count_nonzero(pts[:,2]>=NEAR))
        source_faces+=len(indices)//3
        faces=indices.reshape((-1,3))
        vertices=pts[faces]
        in_front=vertices[:,:,2]>=NEAR
        complete=np.all(in_front,axis=1)
        # Most faces never cross the near plane. Project/color/shade them in
        # batches so an actual 24 fps source-pose sequence is practical in CI.
        if np.any(complete):
            v=vertices[complete]
            screen=np.empty((len(v),3,2))
            screen[:,:,0]=cx+focal*v[:,:,0]/v[:,:,2]
            screen[:,:,1]=cy-focal*v[:,:,1]/v[:,:,2]
            keep=((screen[:,:,0].max(axis=1)>=0)&(screen[:,:,0].min(axis=1)<=WIDTH)
                 &(screen[:,:,1].max(axis=1)>=0)&(screen[:,:,1].min(axis=1)<=HEIGHT))
            v=v[keep];screen=screen[keep]
            ids=faces[complete][keep]
            normal=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0])
            ratio=np.linalg.norm(normal,axis=1)
            shade=np.where(ratio>1e-9,.83+.16*np.abs(normal[:,2])/np.maximum(ratio,1e-9),1.)
            rgb=np.clip(colors[ids].mean(axis=1)*255,28,235).astype(int)
            rgb=np.clip(rgb*shade[:,None],22,245).astype(int)
            depths=v[:,:,2].mean(axis=1)
            for depth,poly,color in zip(depths,screen.tolist(),rgb.tolist()):
                triangles.append((float(depth),[tuple(p) for p in poly],tuple(color)))
        crossing=(~complete)&np.any(in_front,axis=1)
        for ids in faces[crossing]:
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
    direction=("native +X" if np.allclose(basis[2],[1.,0.,0.]) else "source muzzle") if forward_override is not None else ('+X' if sign>0 else '-X')
    draw.text((18,43),f"original XANIM voxel mesh | {fov:g}deg FOV | Y-up | {direction} forward | roll {roll_degrees} deg",fill=(179,196,210))
    draw.rectangle((0,HEIGHT-50,WIDTH,HEIGHT),fill=(14,17,22))
    draw.text((18,HEIGHT-32),"PERSPECTIVE PROBE | NOT VERIFIED FPS ADS/RELOAD | NOT A GAME SCREENSHOT",fill=(237,186,109))
    outfile.parent.mkdir(parents=True,exist_ok=True)
    im.save(outfile,optimize=True)
    return {"source_faces":source_faces,"drawn_faces":rendered_faces,
            "source_vertices_in_front":near_front, "near":NEAR,
            "camera_origin":[round(float(v),4) for v in camera],
            "camera_forward":'source muzzle' if forward_override is not None else ('+X' if sign>0 else '-X'),
            "camera_roll_degrees":float(roll_degrees)}


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
    # The original COD4 rifle actually has tag_ak47_mount! Pair that with
    # hands.tag_weapon instead of treating the rifle root as its grip pivot.
    # Use tag_flash to derive a genuine forward vector, not a guessed rotation.
    hg=hands.tag(hands.world(hand_idle,0.),"tag_weapon")
    gw=rifle.world(gun_idle,0.)
    mount=rifle.tag(gw,"tag_ak47_mount")
    flash=rifle.tag(gw,"tag_flash")
    if mount is None or flash is None:
        raise ValueError("real original AK mount / muzzle tags absent")
    rel=hg@OAT_TO_NATIVE
    muzzle=(rel@flash)[:3,3]
    anchor=hg[:3,3]
    muzzle_direction=muzzle-anchor
    muzzle_direction/=max(1e-8,float(np.linalg.norm(muzzle_direction)))
    native_mesh,_=compose(rifle,hands,gun_idle,hand_idle,0.,hg,mode="iw3_dobj")
    rifle_xyz=np.vstack([part[0] for part in native_mesh[:len(rifle.geometry)]])
    axial=rifle_xyz@muzzle_direction
    min_axis=float(np.min(axial))
    span=float(np.ptp(axial))
    # Behind the original receiver based on actual *measured* geometry
    # bounds. This camera is a diagnostic, not a fabricated COD4 view offset.
    behind=anchor + (min_axis-float(np.dot(anchor,muzzle_direction))
                    -0.10*span)*muzzle_direction
    candidates={"original_camera_origin":np.asarray(camtag if camtag is not None
                                                     else np.zeros(3),dtype=float),
                "behind_real_rifle_geometry":behind}
    source_tags={
        "hands_tag_weapon_exists":True,
        "hands_tag_camera_candidates":tags,
        "rifle_tag_iron_sight":any(n.get("name","").lower()=="tag_iron_sight"
                                  for n in rifle.nodes),
        "rifle_tag_weapon":any(n.get("name","").lower()=="tag_weapon"
                               for n in rifle.nodes),
        "rifle_tag_ak47_mount":any(n.get("name","").lower()=="tag_ak47_mount"
                                   for n in rifle.nodes),
        "rifle_tag_flash":any(n.get("name","").lower()=="tag_flash"
                               for n in rifle.nodes),
        "measured_muzzle_forward":[round(float(x),4) for x in muzzle_direction],
        "rifle_relevant_joint_names":[n.get("name","") for n in rifle.nodes
            if any(w in n.get("name","").lower() for w in ('sight','mag','tag','bolt'))][:40],
        "hand_relevant_joint_names":[n.get("name","") for n in hands.nodes
            if any(w in n.get("name","").lower() for w in ('camera','weapon','wrist','hand'))][:40],
    }
    results=[]
    for strategy in ("iw3_dobj","native_pair","direct_tag"):
        for view,origin in candidates.items():
            # Original source +X/-X versus the rig's own source muzzle.
            for axis in ("muzzle","posx","negx"):
                sign=1 if axis!="negx" else -1
                direction=muzzle_direction if axis=="muzzle" else None
                for action,fraction in (("idle",0.),("reload",.50)):
                    gc=closest_clip(rifle,action)
                    hc=closest_clip(hands,action)
                    if not gc or not hc:continue
                    t=min(rifle.duration(gc),hands.duration(hc))*fraction
                    combined,meta=compose(rifle,hands,gc,hc,t,hand_rest,mode=strategy)
                    stem=f"{strategy}_{view}_{axis}_{action}"
                    report=render_perspective(combined,origin,sign,
                         f"{strategy.upper()} | {view} | {axis} | {action.upper()} @ {int(fraction*100)}%",
                         output/(stem+".png"),forward_override=direction)
                    results.append({"name":stem+".png","strategy":strategy,"view":view,
                       "forward":axis,"action":action,
                       "fraction":fraction,
                       **report,"hand_proximity_normalized":meta.get("hand_proximity_normalized_by_rifle_extent"),
                       "visually_approved":False})
    # Real viewmodel camera calibration: rotate the eye basis around the
    # source-derived muzzle forward vector and compare three eye heights.
    # Original model still uses its genuine animated arm and gun poses.
    # NO camera candidate here is certified for hipfire/ADS yet.
    sweep=[]
    neutral,meta=compose(rifle,hands,gun_idle,hand_idle,0.,hand_rest,mode="iw3_dobj")
    spine=np.array([0.,1.,0.],dtype=float)
    for above in (0.0,.12,.25):
        eye=behind+spine*(span*above)
        # Aim at the ORIGINAL model muzzle, not an invented iron sight tag.
        aim=muzzle-eye
        aim/=max(1e-8,float(np.linalg.norm(aim)))
        for roll in (0,90,-90,180):
            filename=f"ak47_native_fps_eyeheight_{int(above*100):02d}_roll_{roll:+04d}.png"
            shot=render_perspective(neutral,eye,1,
                  f"NATIVE SOURCE TAGS | CAMERA HEIGHT {above:.2f} of rifle | ROLL {roll:+d}",
                  output/filename,forward_override=aim,roll_degrees=roll)
            sweep.append({"filename":filename,"height_fraction":above,
                         "roll_degrees":roll,**shot,
                         "camera_pose_verified":False})
    sweep_names=[i["filename"] for i in sweep]
    make_grid(output,sweep_names,"ak47_native_fps_roll_and_height_sweep.png",3)
    output.mkdir(parents=True,exist_ok=True)
    # Each contact sheet compares idle/reload on two camera positions/directions.
    for strategy in ("iw3_dobj","native_pair","direct_tag"):
        names=[f"{strategy}_{view}_{axis}_{action}.png"
                for view in candidates for axis in ("muzzle","posx","negx")
                for action in ("idle","reload")]
        make_grid(output,names,"ak47_fps_"+strategy+"_camera_comparison.png",2)
    audit={"source": "real privately converted COD4 skinned XANIM voxel rifle + viewhands",
           "original_mount_pair": ["hands:tag_weapon","rifle:native model root"],
           "muzzle_direction_from_original_tag_flash":[round(float(v),5) for v in muzzle_direction],
           "source_tags":source_tags,"camera_candidates":list(candidates),
           "projections":results,"fps_camera_roll_sweep":sweep,
           "gameplay_verified":False,"camera_calibrated":False,
           "ads_verified":False,"hand_grip_verified":False,
           "private_original_geometry_exported":False}
    (output/"fps-camera-audit.json").write_text(json.dumps(audit,indent=2)+"\n")
    print(json.dumps({"frames":len(results),"tag_camera":camtag is not None,
      "camera_candidates":list(candidates),
      "source_tags":source_tags,
      "source_roll_sweep":[{"height":x["height_fraction"],"roll":x["roll_degrees"],
                       "faces":x["drawn_faces"]} for x in sweep],
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

