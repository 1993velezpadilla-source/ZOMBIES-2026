#!/usr/bin/env python3
"""Private IW3 AK-47 -> cuboid/skinned glTF with ALL compatible XANIM clips.

Input comes from the user's COD4 extraction in a temporary GitHub runner.
Never commit/export extracted game meshes, textures, animation keyframes or
this tool's binary outputs as public Actions artifacts.

The converter replaces *rendered* triangles with a box/voxel shell, retaining
gltf node hierarchy, inverse bind matrices and skin joint indices. It does not
prove that IW3 XANIM rest poses/axes are calibrated for gameplay.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import json
import math
from pathlib import Path
import re
import struct
import sys

# This module is taken from our existing PR #6 in the PRIVATE CI checkout.
from iw3_gltf_animation_bridge import (
    add_animation, read_glb, write_glb,
)
from iw3_xanim_v17 import load_xanim
from oat_coordinates import oat_animation_tracks, install_native_rest

COMPONENT = {
    5121: ("B", 1), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4),
    5120: ("b", 1), 5122: ("h", 2),
}
WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
MODEL = re.compile(r"^viewmodel_ak47(?:_|$)", re.I)
KINDS = ("idle", "ads", "fire", "reload", "pullout", "putaway", "sprint", "other")
MAX_POINTS = 1_500_000
MAX_CUBES = 4000
MAX_CLIPS = 128
RIFLE_DETAIL_PROFILES = {
    "legacy": dict(density=76, max_cubes=4000, max_points=MAX_POINTS,
                   max_steps=72, cull_internal=False, allow_lod=True),
    "high": dict(density=384, max_cubes=40000, max_points=8_000_000,
                 max_steps=512, cull_internal=True, allow_lod=False),
}


def read_accessor(doc: dict, raw: bytes, index: int):
    a = doc["accessors"][index]
    if "sparse" in a:
        raise ValueError("sparse accessor needs explicit reconstruction")
    view = doc["bufferViews"][a["bufferView"]]
    if view.get("buffer", 0) != 0:
        raise ValueError("only embedded GLB buffer 0 is supported")
    count, width = a["count"], WIDTH[a["type"]]
    fmt, size = COMPONENT[a["componentType"]]
    stride = view.get("byteStride", width * size)
    start = view.get("byteOffset", 0) + a.get("byteOffset", 0)
    if count > 2_000_000 or stride < width * size or start < 0:
        raise ValueError("invalid accessor bounds")
    if count and start + (count-1)*stride + width*size > len(raw):
        raise ValueError("GLB accessor beyond buffer")
    pattern = "<" + fmt * width
    normalized = a.get("normalized", False)
    values = []
    for i in range(count):
        row = struct.unpack_from(pattern, raw, start + i*stride)
        if normalized and a["componentType"] in (5121,5123):
            cap = (1 << (size*8)) - 1
            row = tuple(n/cap for n in row)
        values.append(row)
    return values


def pack_new(doc: dict, payload: bytearray, rows, kind: str, ctype=5126, target=None):
    fmt, width_bytes = COMPONENT[ctype]
    width = WIDTH[kind]
    if any(len(r) != width for r in rows):
        raise ValueError("malformed generated vertex attribute")
    while len(payload) % 4:
        payload.append(0)
    offset = len(payload)
    plain = [v for row in rows for v in row]
    payload.extend(struct.pack("<" + fmt*len(plain), *plain))
    view = {"buffer": 0, "byteOffset": offset,
            "byteLength": len(plain)*width_bytes}
    if target:
        view["target"] = target
    view_id = len(doc["bufferViews"])
    doc["bufferViews"].append(view)
    acc = {"bufferView":view_id,"componentType":ctype,
           "count":len(rows),"type":kind}
    if kind in ("SCALAR", "VEC3") and rows:
        acc["min"]=[min(v[i] for v in rows) for i in range(width)]
        acc["max"]=[max(v[i] for v in rows) for i in range(width)]
    idx = len(doc["accessors"])
    doc["accessors"].append(acc)
    return idx


def color_for_material(source: dict) -> list[float]:
    name = source.get("name", "").lower()
    if any(w in name for w in ("wood", "stock", "grip", "walnut")):
        return [0.49,0.25,0.12,1.0]
    if any(w in name for w in ("hand", "skin", "finger", "arm")):
        return [0.69,0.48,0.34,1.0]
    if any(w in name for w in ("metal", "steel", "sight", "bolt")):
        return [0.30,0.32,0.34,1.0]
    c = source.get("pbrMetallicRoughness",{}).get("baseColorFactor")
    if c and len(c) == 4 and all(isinstance(v,(int,float)) for v in c):
        # Most extracted models have white factors; darken to game-art graphite.
        return [max(.14, min(.67, float(v)*.49)) for v in c[:3]] + [1.0]
    return [0.25,0.27,0.28,1.0]


def triangles(doc: dict, binary: bytes, primitive: dict):
    attrs = primitive["attributes"]
    if "POSITION" not in attrs:
        return
    pos = read_accessor(doc,binary,attrs["POSITION"])
    joints = read_accessor(doc,binary,attrs["JOINTS_0"]) if "JOINTS_0" in attrs else None
    weights = read_accessor(doc,binary,attrs["WEIGHTS_0"]) if "WEIGHTS_0" in attrs else None
    if "indices" in primitive:
        inds = [n[0] for n in read_accessor(doc,binary,primitive["indices"])]
    else:
        inds = list(range(len(pos)))
    if primitive.get("mode",4) != 4:
        raise ValueError("triangles mode only (GLTF primitive mode 4)")
    if len(inds)%3 or any(i>=len(pos) for i in inds):
        raise ValueError("invalid source triangle indices")
    for k in range(0,len(inds),3):
        ids=inds[k:k+3]
        xyz=[pos[i] for i in ids]
        bone=0
        if joints and weights:
            scores=defaultdict(float)
            for i in ids:
                for j,w in zip(joints[i],weights[i]):
                    scores[int(j)] += float(w)
            if scores:
                bone=max(scores, key=scores.get)
        yield xyz, bone



# Procedural materials are independently drawn color choices, not COD4 textures.
# Decorative ACOG / reflex variants are omitted from the iron-sight AK view.
ACCESSORY_LABELS = ("acog", "reflex", "reticle", "lens", "holo", "red_dot")

def allowed_primitive(source: dict, primitive: dict, mode: str) -> bool:
    if mode != "rifle":
        return True
    mid = primitive.get("material", 0)
    mats = source.get("materials", [])
    name = mats[mid].get("name", "").lower() if mid < len(mats) else ""
    return not any(word in name for word in ACCESSORY_LABELS)

def procedural_color(center: tuple, bone: int, pitch: float, context: dict) -> tuple:
    kind = context["kind"]
    if kind in ("hands","hands_tight"):
        base = (0.73, 0.52, 0.40)  # adult cartoon skin, not COD4 material
    else:
        lo, hi, major = context["lo"], context["hi"], context["major"]
        f = (center[major] - lo[major]) / max(1e-9, hi[major] - lo[major])
        material = context["material"]
        if "misc" in material:
            base = (0.49, 0.53, 0.56)      # selector/machined steel
        elif f < .245:
            base = (0.56, 0.29, 0.15)      # original walnut palette: stock
        elif .51 < f < .745:
            base = (0.62, 0.34, 0.18)      # handguard
        elif f > .76:
            base = (0.37, 0.42, 0.45)      # barrel and muzzle
        else:
            base = (0.29, 0.34, 0.38)      # receiver/magazine
    ix, iy, iz = (int(round(x / max(pitch, .001))) for x in center)
    grain=.013 if kind in ("hands","hands_tight") else .013*min(1.,pitch/.35)
    shade = (((ix * 3 + iy * 5 + iz * 11 + bone * 13) % 9) - 4) * grain
    return tuple(max(.12, min(.9, v + shade)) for v in base) + (1.0,)

def surface_cells(tris: list, pitch: float, *, max_points=MAX_POINTS, max_steps=72):
    cubes=set()
    sampled=0
    for xyz,bone in tris:
        a,b,c=xyz
        def length(p,q):
            return math.sqrt(sum((p[i]-q[i])**2 for i in range(3)))
        longest=max(length(a,b),length(b,c),length(c,a))
        steps=max(1,min(max_steps,math.ceil(longest/(pitch*.9))))
        # Triangular barycentric sampling includes boundaries and interior;
        # unlike bounding-box fill, does not create large solid weapon bricks.
        for i in range(steps+1):
            for j in range(steps+1-i):
                v=i/steps
                w=j/steps
                q=tuple(a[d]*(1-v-w)+b[d]*v+c[d]*w for d in range(3))
                cubes.add((bone,*(math.floor(t/pitch) for t in q)))
                sampled+=1
                if sampled > max_points:
                    raise OverflowError("triangle sampling budget exhausted")
    return cubes


def z_merge(cells):
    by_column=defaultdict(list)
    for bone,x,y,z in cells:
        by_column[(bone,x,y)].append(z)
    out=[]
    for (bone,x,y),zs in sorted(by_column.items()):
        zs=sorted(set(zs))
        first=last=zs[0]
        for z in zs[1:]:
            if z==last+1:
                last=z
            else:
                out.append((bone,x,y,first,last+1))
                first=last=z
        out.append((bone,x,y,first,last+1))
    return out


def exposed_box_faces(cells, box):
    """Cull only faces fully covered by cells on the SAME animated joint.

    Faces between the magazine/bolt and receiver must remain, because those
    parts move apart. Partially covered long faces are retained conservatively.
    Face order matches emit_boxes' bottom, top, left, right, front, back.
    """
    bone,x,y,z0,z1=box
    covered=[(bone,x,y,z0-1) in cells,(bone,x,y,z1) in cells]
    for dx,dy in ((-1,0),(1,0),(0,1),(0,-1)):
        covered.append(all((bone,x+dx,y+dy,z) in cells for z in range(z0,z1)))
    return [i for i,hidden in enumerate(covered) if not hidden]


def bone_identity(doc: dict, bone: int) -> str:
    # In glTF JOINTS_0 stores the index INTO skin.joints, not the global
    # node number. Preserve this exact mapping while filtering forearms.
    skins=doc.get("skins",[])
    if not skins or bone>=len(skins[0].get("joints",[])):
        return ""
    node_idx=skins[0]["joints"][bone]
    return doc["nodes"][node_idx].get("name","").lower()


def is_hand_or_finger_bone(name: str) -> bool:
    """Only true hand/wrist segments; exclude shoulders, elbows and forearms.

    This is an EXPERIMENTAL FPS crop, not an anatomical skin-retarget.
    It never changes the joint indices, source XANIM, or original scene.
    """
    if "wristtwist" in name or any(x in name for x in ("elbow","shoulder","clavicle")):
        return False
    return any(x in name for x in ("thumb","index","pinky","finger",
                                  "ring","wrist","palm","j_mid","j_hand"))


def emit_boxes(doc, raw, primitive, target_doc, dest_binary, pitch, context):
    tri=list(triangles(doc,raw,primitive))
    if context["kind"]=="hands_tight":
        tri=[(xyz,bone) for xyz,bone in tri
             if is_hand_or_finger_bone(bone_identity(doc,bone))]
    if not tri:
        raise ValueError("internal error: unselected primitive passed to voxel emission")
    cells=surface_cells(tri,pitch,max_points=context["max_points"],max_steps=context["max_steps"])
    boxes=z_merge(cells)
    if len(boxes)>context["max_cubes"]:
        raise OverflowError("cuboid output budget exceeded")
    positions=[]; normals=[]; tex=[]; joints=[]; weights=[]; colors=[]; indices=[]
    sides=[
      ((0,3,2,1),(0.,0.,-1.)), ((4,5,6,7),(0.,0.,1.)),
      ((0,4,7,3),(-1.,0.,0.)),((1,2,6,5),(1.,0.,0.)),
      ((3,7,6,2),(0.,1.,0.)),((0,1,5,4),(0.,-1.,0.)),
    ]
    removed=0
    for box in boxes:
        bone,x,y,z0,z1=box
        visible=exposed_box_faces(cells,box) if context["cull_internal"] else list(range(6))
        removed+=6-len(visible)
        if not visible:continue
        x0=x*pitch; x1=(x+1)*pitch
        y0=y*pitch; y1=(y+1)*pitch
        a=z0*pitch; b=z1*pitch
        center=((x0+x1)/2, (y0+y1)/2, (a+b)/2)
        rgba=procedural_color(center,bone,pitch,context)
        corners=[
            (x0,y0,a),(x1,y0,a),(x1,y1,a),(x0,y1,a),
            (x0,y0,b),(x1,y0,b),(x1,y1,b),(x0,y1,b),
        ]
        for face_index in visible:
            face,norm=sides[face_index]
            off=len(positions)
            for j,vertex in enumerate(face):
                positions.append(corners[vertex])
                normals.append(norm)
                tex.append(((j==1 or j==2)*1.,(j>=2)*1.))
                joints.append((bone,0,0,0))
                weights.append((1.,0.,0.,0.))
                colors.append(rgba)
            indices.extend((off,off+1,off+2,off,off+2,off+3))
    attrs={
        "POSITION":pack_new(target_doc,dest_binary,positions,"VEC3",target=34962),
        "NORMAL":pack_new(target_doc,dest_binary,normals,"VEC3",target=34962),
        "TEXCOORD_0":pack_new(target_doc,dest_binary,tex,"VEC2",target=34962),
        "COLOR_0":pack_new(target_doc,dest_binary,colors,"VEC4",target=34962),
    }
    if "JOINTS_0" in primitive["attributes"] and "WEIGHTS_0" in primitive["attributes"]:
        attrs["JOINTS_0"]=pack_new(target_doc,dest_binary,joints,"VEC4",5123,34962)
        attrs["WEIGHTS_0"]=pack_new(target_doc,dest_binary,weights,"VEC4",target=34962)
    result={"attributes":attrs,"indices":pack_new(target_doc,dest_binary,
            [(v,) for v in indices],"SCALAR",5125,34963),
            "mode":4,"material":primitive.get("material",0)}
    return result, len(boxes), len(cells), removed


def voxelize(source: Path, target: Path, *, density=42, kind='rifle',
             max_cubes=MAX_CUBES,max_points=MAX_POINTS,max_steps=72,
             cull_internal=False,allow_lod=True):
    if not 12<=density<=512 or max_cubes>40000 or max_points>8_000_000:
        raise ValueError('unsupported voxel detail budget')
    doc,original=read_glb(source)
    out=deepcopy(doc)
    surviving=[]
    mesh_mapping={}
    filtered_primitives=0
    for i,mesh in enumerate(doc.get("meshes",[])):
        good=[]
        for prim in mesh.get("primitives",[]):
            if not allowed_primitive(doc,prim,kind):
                filtered_primitives+=1
                continue
            if kind=="hands_tight" and not any(
                is_hand_or_finger_bone(bone_identity(doc,bone))
                for _,bone in triangles(doc,original,prim)
            ):
                # A forearm-only primitive MUST be discarded entirely instead
                # of aborting the full weapon conversion on empty selection.
                filtered_primitives+=1
                continue
            good.append(prim)
        if good:
            mesh_mapping[i]=len(surviving)
            surviving.append(good)
    if not surviving:
        raise ValueError("no base weapon geometry after accessory filtering")
    for node in out.get("nodes",[]):
        if "mesh" in node:
            old_i=node["mesh"]
            if old_i in mesh_mapping:
                node["mesh"]=mesh_mapping[old_i]
            else:
                node.pop("mesh",None)
                node.pop("skin",None)
    out["meshes"]=[deepcopy(doc["meshes"][old]) for old in sorted(mesh_mapping)]
    for old_index,mesh in zip(sorted(mesh_mapping),out["meshes"]):
        # Keep the exact filtered primitive subset and consistent node remaps.
        mesh["primitives"]=surviving[mesh_mapping[old_index]]
    out["buffers"]=[{"byteLength":0}]
    out["accessors"]=[];out["bufferViews"]=[]
    out.pop("images",None);out.pop("textures",None);out.pop("samplers",None)
    out.pop("extensionsUsed",None);out.pop("extensionsRequired",None)
    old_mats=doc.get("materials",[])
    if not old_mats:
        old_mats=[{"name":"unspecified"}]
    out["materials"]=[{"name":"blockstyle_"+m.get("name",str(i)),
       "pbrMetallicRoughness":{"baseColorFactor":[1.0,1.0,1.0,1.0],
                              "metallicFactor":0,"roughnessFactor":1},
       "doubleSided":True} for i,m in enumerate(old_mats)]
    binary=bytearray()
    def retain(aid):
        rows=read_accessor(doc,original,aid)
        old=doc["accessors"][aid]
        return pack_new(out,binary,rows,old["type"],old["componentType"])
    for skin in out.get("skins",[]):
        if "inverseBindMatrices" in skin:
            skin["inverseBindMatrices"]=retain(skin["inverseBindMatrices"])
    for anim in out.get("animations",[]):
        for sampler in anim["samplers"]:
            sampler["input"]=retain(sampler["input"])
            sampler["output"]=retain(sampler["output"])
    all_coords=[]
    for mesh in out.get("meshes",[]):
        for prim in mesh.get("primitives",[]):
            if kind=="hands_tight":
                for xyz,bone in triangles(doc,original,prim):
                    if is_hand_or_finger_bone(bone_identity(doc,bone)):
                        all_coords.extend(xyz)
            else:
                all_coords.extend(read_accessor(doc,original,prim["attributes"]["POSITION"]))
    if not all_coords:
        raise ValueError("no source mesh vertices")
    lo=[min(p[i] for p in all_coords) for i in range(3)]
    hi=[max(p[i] for p in all_coords) for i in range(3)]
    longest=max(hi[i]-lo[i] for i in range(3))
    major=max(range(3),key=lambda i: hi[i]-lo[i])
    if longest <= 0:
        raise ValueError("degenerate model")
    best=None
    # Automatic LOD cap rather than exploding a mobile renderer into millions
    # of voxels. Source geometry is never shipped with the model.
    divisors=[density]+([d for d in (256,192,128,96,72,64,56,48,42,32,24,18,12) if d<density] if allow_lod else [])
    for divisor in divisors:
        pitch=longest/divisor
        attempt=deepcopy(out)
        blob=bytearray(binary)
        parts=[]; total=0; occupied=0; removed_faces=0
        try:
            for mesh in out["meshes"]:
                target_primitives=[]
                for prim in mesh["primitives"]:
                    mat_id=prim.get("material",0)
                    mat_name=doc.get("materials",[])[mat_id].get("name","").lower() if mat_id<len(doc.get("materials",[])) else ""
                    context={"kind":kind,"lo":lo,"hi":hi,"major":major,"material":mat_name,
                             "max_cubes":max_cubes,"max_points":max_points,"max_steps":max_steps,
                             "cull_internal":cull_internal}
                    result,count,cells,removed=emit_boxes(doc,original,prim,attempt,blob,pitch,context)
                    result["material"]=min(result["material"],len(out["materials"])-1)
                    target_primitives.append(result)
                    total+=count;occupied+=cells;removed_faces+=removed
                    if total>max_cubes:
                        raise OverflowError("mesh cube budget exhausted")
                parts.append(target_primitives)
        except OverflowError:
            continue
        best=(attempt,blob,parts,total,occupied,pitch,divisor,removed_faces)
        break
    if best is None:
        raise ValueError(f"requested density {density} exceeds the explicit geometry budget; no lower detail accepted")
    target_doc,raw,parts,total,occupied,pitch,effective_density,removed_faces=best
    for mesh,primitives in zip(target_doc["meshes"],parts):
        mesh["primitives"]=primitives
    write_glb(target,target_doc,raw)
    check,_=read_glb(target)
    assert len(check.get("skins",[]))==len(doc.get("skins",[]))
    assert len(check.get("nodes",[]))==len(doc.get("nodes",[]))
    primitives=[p for m in check['meshes'] for p in m['primitives']]
    triangle_count=sum(check['accessors'][p['indices']]['count']//3 for p in primitives)
    vertex_count=sum(check['accessors'][p['attributes']['POSITION']]['count'] for p in primitives)
    return {"cuboids":total,"sampled_cells":occupied,"pitch":round(pitch,6),
            "requested_density":density,"effective_density":effective_density,
            "automatic_lod_reduced":effective_density!=density,
            "triangle_count":triangle_count,"vertex_count":vertex_count,
            "internal_faces_removed":removed_faces,"same_joint_face_culling":cull_internal,
            "skin_count":len(check.get("skins",[])),
            "node_count":len(check.get("nodes",[])),
            "primitives":sum(len(m["primitives"]) for m in check["meshes"]),
            "source_triangles_retained":False,
            "palette":"original procedural adult-cartoon vertex colors, not COD4 texture",
            "render_mode":kind,
            "accessory_meshes_removed":len(doc.get("meshes",[]))-len(out["meshes"]),
            "filtered_source_primitives":filtered_primitives,
            "hand_only_positive_joint_names":sorted({
              doc["nodes"][node_id].get("name","") for skin in doc.get("skins",[])
              for node_id in skin.get("joints",[]) if kind=="hands_tight" and
              is_hand_or_finger_bone(doc["nodes"][node_id].get("name","").lower())}),
            "voxel_glb_bytes":target.stat().st_size}


def family(p: Path) -> bool:
    return bool(MODEL.match(p.name))


def classify(name: str):
    found=[k for k in KINDS[:-1] if re.search(r"(?:^|_)"+k+r"(?:_|$)",name,re.I)]
    return found or ["other"]


def compatible(doc, animation) -> int:
    joints={doc["nodes"][i].get("name","").casefold()
            for skin in doc.get("skins",[])
            for i in skin.get("joints",[])}
    return len(joints & {b.name.casefold() for b in animation.bones})


def add_all_animations(base: Path, target: Path, clips, native_locals=None):
    doc,b=read_glb(base)
    native_info=install_native_rest(doc,native_locals) if native_locals else {}
    raw=bytearray(b)
    report={}
    for path,animation in clips:
        overlap=compatible(doc,animation)
        if overlap==0:
            report[path.name]={"status":"unmatched","matched_bones":0}
            continue
        try:
            # OAT exports global frames as Rx(-90deg)*native; its child
            # locals remain native. Preserve that frame for root XANIM too.
            gltf_animation,coordinate_info=oat_animation_tracks(doc,animation)
            info=add_animation(doc,raw,gltf_animation,label=path.stem)
            report[path.name]={"status":"attached" if info["channels"] else "unmatched",
                               "matched_bones":info["matched_bones"],
                               "channels":info["channels"],
                               **coordinate_info,
                               **native_info,
                               "actions":classify(path.stem)}
        except (ValueError,KeyError,OverflowError) as e:
            report[path.name]={"status":"error","reason":str(e)[:130]}
    write_glb(target,doc,raw)
    check,_=read_glb(target)
    assert len(check.get("animations",[]))==sum(
        x["status"]=="attached" for x in report.values())
    return report


def run(dumps: Path, target: Path, native_locals_dir=None,rifle_detail='high'):
    source=dumps/"common_mp"
    model_dir=source/"model_export"
    models=sorted(p for p in model_dir.glob("viewmodel_ak47*_lod0.glb") if family(p))
    if not models:
        raise FileNotFoundError("original first-person AK47 LOD0 GLB not found")
    clips=[]
    errors={}
    for p in sorted((source/"xanim").iterdir()):
        if not p.is_file() or not family(p):
            continue
        try:
            clips.append((p,load_xanim(p)))
        except (ValueError,OSError,OverflowError,struct.error) as e:
            errors[p.name]=str(e)[:110]
    if not clips:
        raise ValueError("no IW3 AK47 XANIM tracks decoded")
    if len(clips)>MAX_CLIPS:
        raise ValueError("too many XANIM files for bounded conversion")
    scored=[]
    for p in models:
        doc,_=read_glb(p)
        scores=[compatible(doc,a) for _,a in clips]
        scored.append((sum(x>0 for x in scores),sum(scores),p))
    _,_,chosen=max(scored,key=lambda v:(v[0],v[1],-len(v[2].name)))
    source_doc,_=read_glb(chosen)
    def native_for(path):
        if native_locals_dir is None:raise ValueError('native model locals directory required')
        name=re.sub(r'_lod\d+$','',path.stem)+'.json'
        return json.loads((Path(native_locals_dir)/name).read_text())
    rifle_native=native_for(chosen)
    source_mats=[m.get('name','unnamed') for m in source_doc.get('materials',[])]
    source_meshes=[m.get('name','unnamed') for m in source_doc.get('meshes',[])]
    target.mkdir(parents=True,exist_ok=True)
    rifle=target/"AK47_COD4_BLOCKSTYLE_PRIVATE.glb"
    voxel=voxelize(chosen,rifle,kind='rifle',**RIFLE_DETAIL_PROFILES[rifle_detail])
    animated=target/"AK47_COD4_BLOCKSTYLE_ALL_XANIM_PRIVATE.glb"
    gun_clips=add_all_animations(rifle,animated,clips,rifle_native)
    hands_path=model_dir/"viewmodel_base_viewhands_lod0.glb"
    hands={}
    hands_voxel=None
    hands_tight_geometry=None
    tight_hands={}
    if hands_path.exists():
        hands_native=native_for(hands_path)
        hands_voxel=voxelize(hands_path,target/"AK47_COD4_HANDS_BLOCKSTYLE_PRIVATE.glb",density=42,kind="hands")
        hands=add_all_animations(
            target/"AK47_COD4_HANDS_BLOCKSTYLE_PRIVATE.glb",
            target/"AK47_COD4_HANDS_ALL_XANIM_PRIVATE.glb", clips,hands_native)
        # Owner's earlier request: only the first-person HANDS should remain
        # visible, not full-sized forearms obstructing the FPS camera.
        # Preserve original bones/animation; only emit triangles attached to
        # wrists/fingers. This is an opt-in comparison asset, not a replacement.
        hands_tight_geometry=voxelize(
            hands_path,target/"AK47_COD4_HANDSONLY_BLOCKSTYLE_PRIVATE.glb",
            density=48,kind="hands_tight")
        tight_hands=add_all_animations(
            target/"AK47_COD4_HANDSONLY_BLOCKSTYLE_PRIVATE.glb",
            target/"AK47_COD4_HANDSONLY_ALL_XANIM_PRIVATE.glb", clips,hands_native)
        if hands_tight_geometry["cuboids"]<50 or not any(
            item["status"]=="attached" for item in tight_hands.values()):
            raise ValueError("hand-only option produced insufficient skinned geometry")
    from texture_atlas import apply_texture
    # Keep the existing rig and mesh byte ranges. Atlas PNGs and UV bindings
    # live only in private outputs, while this report contains metadata.
    apply_texture(rifle,rifle)
    rifle_texture=apply_texture(animated,animated,target/'AK47_texture_512_PRIVATE.png')
    labels={k:sum(a["status"]=="attached" and k in a.get("actions",[])
                  for a in gun_clips.values()) for k in KINDS}
    return {
      "source":"user-provided COD4 archive, extracted privately with OAT",
      "animation_coordinate_frame":"OAT glTF Y-up; Rx(-90deg) on skeleton roots only",
      "animation_translation_semantics":"IW3 model bind offset + XANIM translation delta on non-root bones",
      "selected_ak_model":chosen.name,
      "rifle_detail_profile":rifle_detail,
      "source_material_names":source_mats,
      "source_mesh_names":source_meshes,
      "candidate_models":len(models),"xanim_decoded":len(clips),
      "xanim_decode_errors":errors,"rifle_geometry":voxel,"rifle_texture":rifle_texture,
      "rifle_animation_counts":labels,
      "rifle_animations_attached":sum(x["status"]=="attached" for x in gun_clips.values()),
      "rifle_animations":gun_clips,
      "hands_geometry":hands_voxel,
      "hands_animations_attached":sum(x["status"]=="attached" for x in hands.values()),
      "hands_animations":hands,
      "hands_tight_geometry":hands_tight_geometry,
      "hands_tight_animations_attached":sum(x["status"]=="attached" for x in tight_hands.values()),
      "hands_tight_animations":tight_hands,
      "private_binary_outputs":True,
      "mosaicary_blockbench_import":"Generic Model / GeckoLib: supports cubes and animation channels",
      "rest_pose_verified":False,"gameplay_ADS_verified":False,
      "minecraft_native_conversion_verified":False,
      "rights_clearance":False,
      "public_artifact_contains_proprietary_data":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--dumps",type=Path,default=Path("_iw3_private/dumps"))
    parser.add_argument("--output",type=Path,default=Path("_iw3_private/blockstyle"))
    parser.add_argument("--report",type=Path,default=Path("_iw3_reports/ak47-blockstyle.json"))
    parser.add_argument("--native-locals",type=Path,default=Path("_iw3_private/native-locals"))
    parser.add_argument("--rifle-detail",choices=sorted(RIFLE_DETAIL_PROFILES),default='high')
    args=parser.parse_args()
    result=run(args.dumps,args.output,args.native_locals,args.rifle_detail)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"rifle_cuboids":result["rifle_geometry"]["cuboids"],
        "xanim_decoded":result["xanim_decoded"],
        "rifle_animations_attached":result["rifle_animations_attached"],
        "hands_animations_attached":result["hands_animations_attached"]}))
    if not result["rifle_animations_attached"]:
        raise SystemExit("ERROR: voxel AK has no compatible animation channels")


if __name__=="__main__":
    main()

