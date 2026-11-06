#!/usr/bin/env python3
"""Real glTF skinning/animation pose audit for a privately converted IW3 AK47.

Unlike the static diagnostics renderer, this follows glTF nodes, glTF skin
joint transforms, inverse bind matrices and interpolated animation keyframes.
Only PNG screenshots and numerical diagnostics are emitted; the proprietary
mesh/animation buffers remain in CI scratch and are destroyed after the gate.
No ADS/camera/grip accuracy is implied by a successful numerical/render pass.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from voxelize import read_glb, read_accessor

SCREEN=(1100,650)
EPS=1e-8
ACTIONS=("idle","fire","fire_ads","reload","reload_empty")
FRACS=(0.0,.45,.85)


def mat4(data):
    return np.asarray(data, dtype=np.float64).reshape((4,4),order="F")


def quat_matrix(q):
    x,y,z,w=[float(v) for v in q]
    n=x*x+y*y+z*z+w*w
    if n<EPS: return np.eye(4,dtype=np.float64)
    s=2.0/n
    M=np.eye(4,dtype=np.float64)
    M[:3,:3]=np.array([
        [1-s*(y*y+z*z),s*(x*y-z*w),s*(x*z+y*w)],
        [s*(x*y+z*w),1-s*(x*x+z*z),s*(y*z-x*w)],
        [s*(x*z-y*w),s*(y*z+x*w),1-s*(x*x+y*y)]])
    return M


def local_matrix(node, tracks):
    if "matrix" in node and not tracks:
        return mat4(node["matrix"])
    if "matrix" in node and tracks:
        raise ValueError("animated matrix node requires TRS decomposition")
    T=np.eye(4)
    T[:3,3]=tracks.get("translation",node.get("translation",[0,0,0]))
    R=quat_matrix(tracks.get("rotation",node.get("rotation",[0,0,0,1])))
    S=np.diag([*tracks.get("scale",node.get("scale",[1,1,1])),1.])
    return T@R@S


def interp(values, times, t, rotation=False, mode="LINEAR"):
    if len(values)==1:return values[0]
    i=int(np.clip(np.searchsorted(times,t,side="right")-1,0,len(times)-2))
    if t<=times[0]: return values[0]
    if t>=times[-1]: return values[-1]
    if mode=="STEP":return values[i]
    if mode not in ("LINEAR","STEP"):raise ValueError("unsupported glTF sampler interpolation "+mode)
    a=(t-times[i])/max(EPS,times[i+1]-times[i])
    p=values[i];q=values[i+1]
    if rotation:
        # Shortest-path quaternion SLERP is critical for 360-degree reload bones.
        if np.dot(p,q)<0:q=-q
        dot=float(np.clip(np.dot(p,q),-1,1))
        if dot>.9995:return (p*(1-a)+q*a)/max(EPS,np.linalg.norm(p*(1-a)+q*a))
        theta=math.acos(dot)
        return (math.sin((1-a)*theta)*p+math.sin(a*theta)*q)/math.sin(theta)
    return p*(1-a)+q*a


class PoseScene:
    def __init__(self,path):
        self.doc,self.binary=read_glb(path)
        self.nodes=self.doc.get("nodes",[])
        self.parent={}
        for i,node in enumerate(self.nodes):
            for child in node.get("children",[]):
                if child in self.parent:raise ValueError("multiple glTF parents")
                self.parent[child]=i
        self.animations={a.get("name",f"clip_{i}"):a
                         for i,a in enumerate(self.doc.get("animations",[]))}
        self.tracks={}
        self.durations={}
        for name,animation in self.animations.items():
            channels=[]
            duration=0.
            for ch in animation["channels"]:
                prop=ch["target"]["path"]
                if prop not in ("translation","rotation","scale"):continue
                sm=animation["samplers"][ch["sampler"]]
                ts=np.asarray(read_accessor(self.doc,self.binary,sm["input"]),dtype=float).reshape(-1)
                xs=np.asarray(read_accessor(self.doc,self.binary,sm["output"]),dtype=float)
                channels.append((ch["target"]["node"],prop,ts,xs,sm.get("interpolation","LINEAR")))
                duration=max(duration,float(ts[-1]))
            self.tracks[name]=channels
            self.durations[name]=duration
        self.mesh_nodes={}
        for i,node in enumerate(self.nodes):
            if "mesh" in node:
                self.mesh_nodes.setdefault(node["mesh"],[]).append(i)
        self.IBM=[]
        for skin in self.doc.get("skins",[]):
            ids=skin.get("joints",[])
            if "inverseBindMatrices" in skin:
                mats=[mat4(x) for x in read_accessor(self.doc,self.binary,skin["inverseBindMatrices"])]
            else:mats=[np.eye(4) for _ in ids]
            if len(mats)!=len(ids):raise ValueError("skin IBM length differs from joints")
            self.IBM.append(mats)
        self.geometry=[]
        self.surfaces=[]
        from texture_atlas import embedded_surface
        for mi,mesh in enumerate(self.doc.get("meshes",[])):
            for primitive in mesh.get("primitives",[]):
                attrs=primitive["attributes"]
                pos=np.asarray(read_accessor(self.doc,self.binary,attrs["POSITION"]),dtype=float)
                ix=(np.asarray(read_accessor(self.doc,self.binary,primitive["indices"]),dtype=int).reshape(-1)
                    if "indices" in primitive else np.arange(len(pos)))
                joints=(np.asarray(read_accessor(self.doc,self.binary,attrs["JOINTS_0"]),dtype=int)
                        if "JOINTS_0" in attrs else None)
                weights=(np.asarray(read_accessor(self.doc,self.binary,attrs["WEIGHTS_0"]),dtype=float)
                        if "WEIGHTS_0" in attrs else None)
                colors=(np.asarray(read_accessor(self.doc,self.binary,attrs["COLOR_0"]),dtype=float)[:,:3]
                        if "COLOR_0" in attrs else np.ones((len(pos),3)))
                mid=primitive.get("material",0)
                material=self.doc.get("materials",[])
                factor=material[mid].get("pbrMetallicRoughness",{}).get("baseColorFactor",[1,1,1,1])[:3]
                colors*=np.asarray(factor)[None,:]
                self.geometry.append((mi,pos,ix,joints,weights,colors))
                self.surfaces.append(embedded_surface(self.doc,self.binary,primitive))
        if not self.geometry:raise ValueError("no GLB mesh geometry")

    def posed_surfaces(self):
        return [surface for geometry,surface in zip(self.geometry,self.surfaces)
                for _ in self.mesh_nodes.get(geometry[0],[None])]

    def names(self):
        return sorted(self.animations)

    def duration(self,name):
        if name not in self.animations:raise ValueError("missing clip "+name)
        return self.durations[name]

    def local_values(self,name=None,t=0.0,*,layers=()):
        values={}
        # Sparse ADS clips animate tag_ads only. They override those channels
        # on the current idle/fire pose instead of resetting untouched fingers.
        for clip,time in ([(name,t)] if name is not None else [])+list(layers):
            for node,prop,ts,xs,mode in self.tracks[clip]:
                values.setdefault(node,{})[prop]=interp(xs,ts,time,
                      rotation=prop=="rotation",mode=mode)
        return values

    def world(self,name=None,t=0.0,*,layers=()):
        values=self.local_values(name,t,layers=layers)
        locals_=[local_matrix(n,values.get(i,{})) for i,n in enumerate(self.nodes)]
        memo={}
        def transform(i,depth=0):
            if i in memo:return memo[i]
            if depth>128:raise ValueError("joint hierarchy cycle")
            p=self.parent.get(i)
            memo[i]=locals_[i] if p is None else transform(p,depth+1)@locals_[i]
            return memo[i]
        return [transform(i) for i in range(len(self.nodes))]

    def poses(self,name,t,*,layers=()):
        world=self.world(name,t,layers=layers)
        rendered=[];allcoords=[]
        for mesh,pos,ix,joints,weights,colors in self.geometry:
            indices=self.mesh_nodes.get(mesh,[None])
            for nodeidx in indices:
                node=self.nodes[nodeidx] if nodeidx is not None else {}
                v=np.c_[pos,np.ones(len(pos))]
                if joints is not None and weights is not None and "skin" in node:
                    skinidx=node["skin"]
                    skin=self.doc["skins"][skinidx]
                    bind=self.IBM[skinidx]
                    transformed=np.zeros((len(pos),4),dtype=float)
                    for lane in range(joints.shape[1]):
                        joint_ids=joints[:,lane]
                        ws=weights[:,lane]
                        for jid in np.unique(joint_ids):
                            mask=(joint_ids==jid)&(ws>1e-10)
                            if not np.any(mask):continue
                            if jid>=len(bind):raise ValueError("joint index invalid")
                            matrix=world[skin["joints"][int(jid)]]@bind[int(jid)]
                            transformed[mask] += (v[mask]@matrix.T)*ws[mask,None]
                    xyz=transformed[:,:3]/np.maximum(EPS,transformed[:,3,None])
                else:
                    matrix=world[nodeidx] if nodeidx is not None else np.eye(4)
                    transformed=v@matrix.T
                    xyz=transformed[:,:3]/np.maximum(EPS,transformed[:,3,None])
                if not np.all(np.isfinite(xyz)) or np.max(np.abs(xyz))>1e5:
                    raise ValueError("invalid/exploding animated pose")
                rendered.append((xyz,ix,colors))
                allcoords.append(xyz)
        return rendered,np.vstack(allcoords),world

    def tag(self,world,name="tag_weapon"):
        matches=[i for i,n in enumerate(self.nodes) if n.get("name","").lower()==name]
        return world[matches[0]] if matches else None


def camera_params(points,orientation=(28,25)):
    """A FIXED capture camera from the rifle's idle pose (not the moving mag).

    Per-frame auto-fit falsely shrunk the whole AK when the magazine dropped
    offscreen in a reload. FPS camera never zooms out to show a loose magazine.
    """
    lo=points.min(axis=0);hi=points.max(axis=0)
    axis=int(np.argmax(hi-lo))
    vertical=1 if axis!=1 else 2
    side=next(i for i in range(3) if i not in (axis,vertical))
    yaw,elevation=np.radians(orientation)
    u=points[:,axis];v=points[:,side];w=points[:,vertical]
    right=math.cos(yaw)*u+math.sin(yaw)*v
    up=math.sin(elevation)*math.sin(yaw)*u-math.sin(elevation)*math.cos(yaw)*v+math.cos(elevation)*w
    cx=(right.min()+right.max())/2;cy=(up.min()+up.max())/2
    scale=min((SCREEN[0]-110)/max(EPS,np.ptp(right)),(SCREEN[1]-210)/max(EPS,np.ptp(up)))
    return (axis,vertical,side,yaw,elevation,cx,cy,scale)


def draw_pose(scene,action,t,title,output,*,orientation=(28,25),camera=None,geometry_override=None,renderer='depth',surfaces_override=None):
    # Independent skinning/mount code may pass a physically composed scene.
    # This renders the actual transformed vertices, never an artist mock-up.
    if geometry_override is None:
        geometry,points,world=scene.poses(action,t)
    else:
        geometry=geometry_override
        points=np.vstack([item[0] for item in geometry])
        world=scene.world(action,t)
    lo=points.min(axis=0);hi=points.max(axis=0)
    if camera is None:
        camera=camera_params(points,orientation)
    if renderer=='depth':
        from depth_preview import DepthPreview
        preview=DepthPreview(*SCREEN)
        try:
            preview.set_surfaces(scene.posed_surfaces() if geometry_override is None
                                 else (surfaces_override or []))
            result=preview.orthographic(geometry,camera,title,output)
            return {"bbox_min":lo.round(5).tolist(),"bbox_max":hi.round(5).tolist(),
                    "faces":result['source_faces'],"geometry_pixels":result['geometry_pixels'],
                    "tag_weapon":scene.tag(world) is not None,"renderer":"OpenGL EGL"}
        finally:preview.close()
    axis,vertical,side,yaw,elevation,cx,cy,scale=camera
    def xy(vec):
        a,b,c=vec[axis],vec[side],vec[vertical]
        X=math.cos(yaw)*a+math.sin(yaw)*b
        Y=math.sin(elevation)*math.sin(yaw)*a-math.sin(elevation)*math.cos(yaw)*b+math.cos(elevation)*c
        D=-math.cos(elevation)*math.sin(yaw)*a+math.cos(elevation)*math.cos(yaw)*b+math.sin(elevation)*c
        return SCREEN[0]*.5+(X-cx)*scale,SCREEN[1]*.5+12-(Y-cy)*scale,D
    im=Image.new("RGB",SCREEN,(18,22,29));d=ImageDraw.Draw(im)
    for x in range(0,SCREEN[0],36):d.line((x,0,x,SCREEN[1]),fill=(28,32,40))
    for y in range(0,SCREEN[1],36):d.line((0,y,SCREEN[0],y),fill=(28,32,40))
    triangles=[]
    for xyz,ix,colors in geometry:
        for k in range(0,len(ix),3):
            ids=ix[k:k+3]
            verts=[xy(xyz[j]) for j in ids]
            shade=.75+.24*abs((verts[1][0]-verts[0][0])*(verts[2][1]-verts[0][1])-
                (verts[1][1]-verts[0][1])*(verts[2][0]-verts[0][0])) / max(1.,scale*scale)
            rgb=tuple(int(np.clip(float(np.mean(colors[ids,i]))*255*min(1.,shade),27,250))
                      for i in range(3))
            triangles.append((sum(v[2] for v in verts)/3,[(v[0],v[1]) for v in verts],rgb))
    triangles.sort(key=lambda item:item[0])
    for _,poly,rgb in triangles:d.polygon(poly,fill=rgb)
    d.rectangle((0,0,SCREEN[0],75),fill=(13,17,23))
    d.text((27,15),title,fill=(245,245,247))
    d.text((27,45),f"XANIM: {action}   frame {t:.3f}s  |  actually transformed vertices",fill=(174,199,218))
    d.rectangle((0,SCREEN[1]-52,SCREEN[0],SCREEN[1]),fill=(13,17,23))
    d.text((25,SCREEN[1]-35),"REAL ANIMATION DIAGNOSTIC - ADS/RELOAD/GRIP NOT YET APPROVED",fill=(236,196,112))
    output.parent.mkdir(parents=True,exist_ok=True);im.save(output,optimize=True)
    return {"bbox_min":lo.round(5).tolist(),"bbox_max":hi.round(5).tolist(),
            "faces":len(triangles),"tag_weapon":scene.tag(world) is not None}


def closest_clip(scene,query):
    direct="viewmodel_ak47_"+query
    if direct in scene.animations:return direct
    matches=[x for x in scene.names() if x.endswith("_"+query)]
    return min(matches,key=len) if matches else None


def run(rifle_path,hands_path,outdir):
    a=PoseScene(rifle_path)
    b=PoseScene(hands_path)
    idle_clip=closest_clip(a,"idle") or a.names()[0]
    idle_points=a.poses(idle_clip,0.)[1]
    fixed_camera=camera_params(idle_points)
    audit={"rifle_clips":len(a.animations),"hands_clips":len(b.animations),
           "actions":{},"synchronized_grip_verified":False,
           "capture_camera_follows_magazine":False,
           "camera_type":"fixed orthographic debug from rifle idle; NOT gameplay FPS",
           "animation_rest_pose_verified":False,"ads_camera_verified":False}
    selected=["idle","fire","fire_ads","reload","reload_empty"]
    for key in selected:
        name=closest_clip(a,key)
        hand=closest_clip(b,key)
        if not name or not hand:
            audit["actions"][key]={"status":"missing_matching_animation"}
            continue
        duration=min(a.duration(name),b.duration(hand))
        # A single-frame idle XANIM is a valid zero-second bind pose.
        if duration<0:
            audit["actions"][key]={"status":"negative_duration"}
            continue
        info={"duration_seconds":round(duration,4),"clip":name,
              "static_one_frame":duration==0,"frames":[]}
        rifle_start=a.poses(name,0)[1]
        hands_start=b.poses(hand,0)[1]
        source_span=max(.001,float(np.max(np.ptp(rifle_start,axis=0))))
        for fraction in ((0.,) if duration==0 else FRACS):
            t=duration*fraction
            gun=a.poses(name,t)[1]
            hand_points=b.poses(hand,t)[1]
            dr=np.linalg.norm(gun-rifle_start,axis=1)
            dh=np.linalg.norm(hand_points-hands_start,axis=1)
            fname=outdir / f"ak47_{key}_{int(100*fraction):03d}.png"
            shot=draw_pose(a,name,t,f"AK47 / {key.upper()} / {int(100*fraction)}%",fname,camera=fixed_camera)
            info["frames"].append({
              "fraction":fraction,"image":fname.name,
              "rifle_mean_vertex_motion":round(float(dr.mean()),6),
              "rifle_max_vertex_motion":round(float(dr.max()),6),
              "rifle_motion_vs_rifle_extent":round(float(dr.max())/source_span,4),
              "suspiciously_large_rifle_motion":bool(float(dr.max())>source_span*.9),
              "hands_tag_weapon_present":b.tag(b.world(hand,t)) is not None,
              "hands_mean_vertex_motion":round(float(dh.mean()),6),
              "hands_max_vertex_motion":round(float(dh.max()),6),
              "frame":shot})
        audit["actions"][key]=info
    outdir.mkdir(parents=True,exist_ok=True)
    (outdir/"pose-audit.json").write_text(json.dumps(audit,indent=2)+"\n")
    from PIL import ImageOps
    # Explicitly original mesh pose diagnostics; no composite hands.
    names=["ak47_idle_000.png","ak47_fire_045.png","ak47_reload_000.png",
           "ak47_reload_045.png","ak47_reload_085.png","ak47_reload_empty_085.png"]
    existing=[outdir/n for n in names if (outdir/n).is_file()]
    if len(existing)>=3:
        thumbs=[]
        for path in existing:
            x=Image.open(path).convert("RGB")
            x.thumbnail((740,440))
            thumbs.append(ImageOps.pad(x,(740,440)))
        sheet=Image.new("RGB",(1480,440*int(math.ceil(len(thumbs)/2))),(20,23,30))
        for i,img in enumerate(thumbs):sheet.paste(img,((i%2)*740,(i//2)*440))
        sheet.save(outdir/"ak47_animation_comparison.png",optimize=True)
    print(json.dumps({"rifle":audit["rifle_clips"],"hands":audit["hands_clips"],
        "shots":sum(len(x.get("frames",[])) for x in audit["actions"].values()),
        "actions":{k:v.get("status","rendered") for k,v in audit["actions"].items()}}))
    return audit


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--rifle",type=Path,required=True)
    parser.add_argument("--hands",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    run(args.rifle,args.hands,args.output)


if __name__=="__main__":main()

