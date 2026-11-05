#!/usr/bin/env python3
"""Generate an original low-poly AK-style FPS rifle, skinned glTF animation,
editable Blockbench source, palette textures, and royalty-free TEST sounds.

Only Python stdlib. No copied TaCZ or Project Aether meshes/audio.
The model has distinct body, magazine, bolt, left/right hands and three
timeline sections: idle [0,.18], shoot [.4,.82], reload [1,3.75].
"""
import json
import math
import random
import struct
import sys
import wave
import zlib
from collections import defaultdict
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv)>1 else Path("ak47dev-out")
(root/"models").mkdir(parents=True,exist_ok=True)
(root/"textures").mkdir(parents=True,exist_ok=True)
(root/"sounds").mkdir(parents=True,exist_ok=True)

# Dimensions are measured in glTF model units: Luanti renders 10 units = 1 node.
# Long axis is +Z. An adult-cartoon low-poly silhouette with practical proportions.
parts=[]
def box(name, material, bone, x1,y1,z1,x2,y2,z2):
    parts.append(dict(name=name,material=material,bone=bone,bounds=[x1,y1,z1,x2,y2,z2]))

# Receiver, stamped dust cover, barrel and wood furniture.
box("receiver", "metal", 0, -.64,-.30,.85, .64,.43,4.20)
box("receiver_dust_cover", "black", 0, -.58,.38,.95, .58,.56,3.48)
box("receiver_right_rail", "black", 0, .64,-.10,1.0, .75,.12,3.4)
box("receiver_bottom", "black", 0, -.55,-.52,1.04,.55,-.25,3.50)
box("rear_sight_base", "black", 0, -.19,.52,2.0,.19,.79,2.78)
box("rear_sight_left", "metal", 0, -.28,.72,2.13,-.12,.94,2.40)
box("rear_sight_right", "metal", 0, .12,.72,2.13,.28,.94,2.40)
box("rear_sight_notch", "black", 0, -.16,.78,2.14,.16,.84,2.30)
box("gas_tube", "metal", 0, -.22,.18,4.13,.22,.38,7.77)
box("barrel", "black", 0, -.17,-.05,6.48,.17,.20,9.55)
box("barrel_muzzle", "metal", 0, -.23,-.11,9.35,.23,.27,9.76)
box("muzzle_tip", "black", 0, -.15,-.04,9.76,.15,.20,9.86)
box("front_sight_body", "metal", 0, -.27,.20,8.7,.27,.73,9.03)
box("front_sight_left", "black", 0, -.31,.50,8.70,-.17,.93,9.04)
box("front_sight_right", "black", 0, .17,.50,8.70,.31,.93,9.04)
box("front_sight_post", "black", 0, -.065,.73,8.80,.065,.96,8.94)
box("handguard_front", "wood", 0, -.54,-.16,4.35,.54,.31,6.65)
box("handguard_top", "wood", 0, -.47,.30,4.35,.47,.49,6.47)
box("handguard_ribs1", "black", 0, -.58,-.03,4.61,.58,.06,4.73)
box("handguard_ribs2", "black", 0, -.58,-.03,5.64,.58,.06,5.76)
box("gas_block", "metal", 0, -.34,-.02,7.16,.34,.39,7.59)
box("wood_stock_neck", "wood", 0, -.43,-.24,-.50,.43,.28,.92)
box("wood_stock_middle", "wood", 0, -.53,-.35,-2.29,.53,.27,-.34)
box("wood_stock_butt", "wood", 0, -.64,-.47,-3.41,.64,.46,-2.24)
box("butt_plate", "black", 0, -.67,-.50,-3.53,.67,.48,-3.37)
box("grip", "wood", 0, -.37,-1.92,.17,.37,-.38,1.03)
box("trigger_guard", "black", 0, -.48,-.78,1.0,.48,-.52,2.13)
box("trigger", "metal", 0, -.10,-.89,1.32,.10,-.61,1.45)
box("selector", "metal", 0, .72,-.02,2.4,.78,.16,3.28)
box("rivets_1", "black", 0, .74,-.05,1.85,.81,.04,2.02)
box("rivets_2", "black", 0, .74,-.05,3.35,.81,.04,3.52)
# Magazine has its own animated bone, including a visibly angled rear curve.
box("mag_top", "black", 1, -.45,-1.03,2.32,.45,-.43,3.23)
box("mag_front", "black", 1, -.43,-1.88,2.44,.43,-.96,3.55)
box("mag_curved_middle", "black", 1, -.40,-2.61,2.63,.40,-1.83,3.89)
box("mag_curved_tip", "metal", 1, -.38,-2.96,2.91,.38,-2.53,4.02)
box("mag_stripe", "metal", 1, -.47,-1.72,2.72,-.42,-1.54,3.51)
# Separate bolt carrier: moves backward at firing and empty-reload charge.
box("bolt", "black", 2, -.54,.25,.97,.54,.45,3.11)
box("bolt_handle", "metal", 2, .54,.17,1.68, .99,.33,2.12)
box("bolt_tip", "black", 2, .84,.11,1.75,1.07,.39,2.08)
# Human hands in low-poly adult cartoon style, not duplicated on camera center.
box("right_glove", "skin", 4, .17,-1.60,.12,.90,-.77,1.17)
box("right_thumb", "skin", 4, -.15,-1.22,.37,.32,-.91,.95)
box("right_fingers", "skin", 4, .00,-1.77,.72,.58,-1.44,1.12)
box("right_wrist", "skin", 4, .57,-2.44,-.12,1.07,-1.54,.82)
box("left_glove", "skin", 3, -.67,-1.09,4.59,.19,-.28,5.83)
box("left_thumb", "skin", 3, -.26,-.66,5.43,.30,-.29,5.95)
box("left_fingers", "skin", 3, -.82,-.80,4.79,-.53,-.12,5.89)
box("left_wrist", "skin", 3, -.91,-1.79,4.29,-.27,-.96,5.31)
assert len(parts)>=35

# Real editable Blockbench source for all component parts, no Blender needed.
def make_bbmodel():
    import uuid
    ids = []
    elements = []
    for p in parts:
        id_=str(uuid.uuid5(uuid.NAMESPACE_URL,"voxel-sandbox-v3/"+p["name"]))
        ids.append(id_)
        a=p["bounds"]
        faces={side:{"uv":[0,0,16,16],"texture":0} for side in
               ("north","east","south","west","up","down")}
        elements.append({
            "name":p["name"],"uuid":id_,"type":"cube",
            "from":[a[0],a[1],a[2]],"to":[a[3],a[4],a[5]],
            "rotation":[0,0,0],"origin":[0,0,0],"faces":faces,
            "visibility":True,"autouv":0,
        })
    obj={"meta":{"format_version":"4.10","model_format":"free","box_uv":False},
         "name":"AK47_Prototype_Original",
         "resolution":{"width":16,"height":16},
         "elements":elements,"outliner":ids,
         "textures":[],"animations":[],
         "artist":"Voxel Sandbox original"}
    (root/"AK47_EDITABLE.bbmodel").write_text(
        json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf8")

def png_chunk(tag,data):
    return struct.pack(">I",len(data))+tag+data+struct.pack(">I",zlib.crc32(tag+data)&0xffffffff)
def rgb_png(path,w,h,pixel):
    dat=bytearray()
    for y in range(h):
        dat.append(0)
        for x in range(w):dat+=bytes(pixel(x,y))
    hdr=struct.pack(">IIBBBBB",w,h,8,6,0,0,0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n"+
       png_chunk(b"IHDR",hdr)+png_chunk(b"IDAT",zlib.compress(dat,9))+png_chunk(b"IEND",b""))
palette={
 "metal":(92,98,102),"black":(35,38,42),
 "wood":(146,80,42),"skin":(180,131,103),
}
for i,(mat,col) in enumerate(palette.items()):
    def px(x,y,col=col,mat=mat):
        shade=((x*19+y*13+(x*y)%7)%19)-9
        if mat=="wood": shade+=(x%4==0)*8-(y%7==1)*4
        return tuple(max(0,min(255,c+shade)) for c in col)+(255,)
    rgb_png(root/"textures"/("ak47dev_"+mat+".png"),16,16,px)
# Transparent wield icon to avoid duplicate 2D first-person gun. The real
# geometry is the animated attached mesh above it.
rgb_png(root/"textures/ak47dev_blank.png",2,2,lambda x,y:(0,0,0,0))
def icon(x,y):
    metal=(48,51,55,255); wood=(157,91,43,255)
    if 29<=y<=36 and 8<=x<=59:return metal
    if 16<=y<=29 and 23<=x<=30:return metal
    if 34<=y<=47 and 34<=x<=42:return metal
    if 41<=y<=54 and 25<=x<=30:return wood
    if 26<=y<=36 and 2<=x<=15:return wood
    if 23<=y<=37 and 52<=x<=56:return metal
    return (0,0,0,0)
rgb_png(root/"textures/ak47dev_icon.png",64,64,icon)

# Create glb: skinned mesh, 5 joints, separate material groups, keyframed bone
# transformations, true 3D geometry. No glTF images embedded (Luanti requirement).
binary=bytearray(); buffer_views=[]; accessors=[]
def accessor(blob, component, typ, count, target=None, minmax=None):
    while len(binary)%4:binary.append(0)
    off=len(binary); binary.extend(blob)
    view={"buffer":0,"byteOffset":off,"byteLength":len(blob)}
    if target:view["target"]=target
    v=len(buffer_views);buffer_views.append(view)
    a={"bufferView":v,"componentType":component,"count":count,"type":typ}
    if minmax:
        a["min"],a["max"]=minmax
    index=len(accessors);accessors.append(a);return index

# 4-color separate draw calls, each vertex gets 100% weight to one bone.
geo=defaultdict(lambda:dict(pos=[],norm=[],uv=[],joints=[],weights=[],idx=[]))
faces=[
    # face corners in consistent winding, normals and UV order
    ([0,3,2,1],(0,0,-1)),([4,5,6,7],(0,0,1)),
    ([0,4,7,3],(-1,0,0)),([1,2,6,5],(1,0,0)),
    ([3,7,6,2],(0,1,0)),([0,1,5,4],(0,-1,0)),
]
for p in parts:
    x1,y1,z1,x2,y2,z2=p["bounds"]
    vertices=[
        (x1,y1,z1),(x2,y1,z1),(x2,y2,z1),(x1,y2,z1),
        (x1,y1,z2),(x2,y1,z2),(x2,y2,z2),(x1,y2,z2),
    ]
    g=geo[p["material"]]; bone=p["bone"]
    for fs,normal in faces:
        base=len(g["pos"])//3
        for i,v in enumerate(fs):
            g["pos"]+=list(vertices[v]);g["norm"]+=list(normal)
            g["uv"]+=[(0.06,0.94),(0.94,0.94),(0.94,0.06),(0.06,0.06)][i]
            g["joints"]+=[bone,0,0,0]
            g["weights"]+=[1,0,0,0]
        # orient triangles matching face vertex winding
        g["idx"] += [base,base+1,base+2,base,base+2,base+3]
materials=list(palette.keys())
primitives=[]
def pack_floats(nums):return struct.pack("<"+"f"*len(nums),*nums)
def pack_us(nums):return struct.pack("<"+"H"*len(nums),*nums)
for mat in materials:
    g=geo[mat];n=len(g["pos"])//3
    verts=[g["pos"][i:i+3] for i in range(0,len(g["pos"]),3)]
    lo=[min(v[i] for v in verts) for i in range(3)]
    hi=[max(v[i] for v in verts) for i in range(3)]
    att={
      "POSITION":accessor(pack_floats(g["pos"]),5126,"VEC3",n,34962,(lo,hi)),
      "NORMAL":accessor(pack_floats(g["norm"]),5126,"VEC3",n,34962),
      "TEXCOORD_0":accessor(pack_floats(g["uv"]),5126,"VEC2",n,34962),
      "JOINTS_0":accessor(pack_us(g["joints"]),5123,"VEC4",n,34962),
      "WEIGHTS_0":accessor(pack_floats(g["weights"]),5126,"VEC4",n,34962),
    }
    idx=accessor(pack_us(g["idx"]),5123,"SCALAR",len(g["idx"]),34963)
    primitives.append({"attributes":att,"indices":idx,"material":materials.index(mat)})

# Model joint transforms at bind pose are all identity. Each inverse bind matrix
# is identity, hence every piece starts exactly at its Blockbench cube coordinates.
identity=[1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
ibm=accessor(pack_floats(identity*5),5126,"MAT4",5)
nodes=[{"name":"root","children":[1,2,3,4]},
       {"name":"magazine"},{"name":"bolt"},{"name":"left_hand"},
       {"name":"right_hand"},{"name":"AK47SkinnedMesh","mesh":0,"skin":0}]
def quat_x(angle):
    a=math.radians(angle)/2;return [math.sin(a),0,0,math.cos(a)]
def quat_y(angle):
    a=math.radians(angle)/2;return [0,math.sin(a),0,math.cos(a)]
# Root, mag, bolt, left hand and right hand keyframe state.
times=[0,.18,.4,.46,.56,.68,.82,1.0,1.30,1.65,1.9,2.24,2.5,2.83,3.20,3.42,3.75]
translation={i:[[0,0,0] for _ in times] for i in range(5)}
rotation={i:[[0,0,0,1] for _ in times] for i in range(5)}
def at(time):return times.index(time)
for t,p,r in [(.46,[0,-.13,-.33],quat_x(-5)),(.56,[0,-.06,-.14],quat_x(-2)),
              (1.30,[0,-.09,-.10],quat_y(8)),(1.65,[0,-.12,-.15],quat_y(10)),
              (1.9,[0,-.12,-.15],quat_y(8)),(2.5,[0,-.09,-.10],quat_y(5))]:
    translation[0][at(t)]=p;rotation[0][at(t)]=r
for t,p in [(.46,[0,0,-.55]),(.56,[0,0,-.20]),(3.20,[0,0,-.70]),(3.42,[0,0,-.5])]:
    translation[2][at(t)]=p
for t,p,r in [
    (1.30,[0,-.70,-.35],quat_x(-17)),(1.65,[0,-2.5,-.9],quat_x(-31)),
    (1.9,[.1,-3.1,-.9],quat_x(-22)),(2.24,[0,-1.3,-.4],quat_x(-10)),
    (2.5,[0,-.1,-.05],quat_x(-2))]:
    translation[1][at(t)]=p;rotation[1][at(t)]=r
for t,p,r in [
    (1.30,[-.25,-.60,-.4],quat_x(6)),(1.65,[-.1,-2.2,-1.1],quat_x(30)),
    (1.9,[-.1,-2.5,-1.1],quat_x(23)),(2.24,[0,-1.2,-.4],quat_x(14)),
    (2.83,[0,0,-.1],quat_x(4)),(3.20,[.18,.3,-3.3],quat_x(-25)),
    (3.42,[.18,.3,-2.4],quat_x(-24))]:
    translation[3][at(t)]=p;rotation[3][at(t)]=r

time_accessor=accessor(pack_floats(times),5126,"SCALAR",len(times),
                      minmax=([times[0]],[times[-1]]))
samplers=[];channels=[]
for joint in range(5):
    for prop,components,values in [
        ("translation","VEC3",translation[joint]),
        ("rotation","VEC4",rotation[joint])]:
        out=accessor(pack_floats([v for row in values for v in row]),5126,
                     components,len(times))
        si=len(samplers)
        samplers.append({"input":time_accessor,"output":out,"interpolation":"LINEAR"})
        channels.append({"sampler":si,"target":{"node":joint,"path":prop}})
gltf={
 "asset":{"version":"2.0","generator":"Voxel Sandbox custom skinned AK prototype"},
 "scene":0,"scenes":[{"nodes":[0,5]}],"nodes":nodes,
 "buffers":[{"byteLength":len(binary)}],
 "bufferViews":buffer_views,"accessors":accessors,
 "meshes":[{"name":"AK47","primitives":primitives}],
 "skins":[{"joints":[0,1,2,3,4],"skeleton":0,"inverseBindMatrices":ibm}],
 "materials":[{"name":mat,"doubleSided":False,
      "pbrMetallicRoughness":{"metallicFactor":0,"roughnessFactor":1}}
      for mat in materials],
 "animations":[{"name":"idle_fire_reload","samplers":samplers,"channels":channels}],
}
# GLB JSON+BIN chunks are 4-byte padded.
js=json.dumps(gltf,separators=(",",":")).encode("utf8")
js+=b" " * (-len(js)%4)
binary.extend(b"\x00" * (-len(binary)%4))
gltf["buffers"][0]["byteLength"]=len(binary)
js=json.dumps(gltf,separators=(",",":")).encode("utf8");js+=b" " * (-len(js)%4)
chunk0=struct.pack("<I4s",len(js),b"JSON")+js
chunk1=struct.pack("<I4s",len(binary),b"BIN\x00")+binary
glb=b"glTF"+struct.pack("<II",2,12+len(chunk0)+len(chunk1))+chunk0+chunk1
(root/"models/ak47dev_animated.glb").write_bytes(glb)
make_bbmodel()

# Procedural FX are entirely original and CC0-like (no Aether redistribution).
# They are test Foley placeholders; no claim of an authentic AK recording.
random.seed(17047)
RATE=22050
def save_sound(name,kind,duration):
    length=round(RATE*duration);samples=[]
    for i in range(length):
        t=i/RATE
        if kind=="fire":
            amp=math.exp(-t*17)
            sample=(random.uniform(-1,1)*.85+
                    math.sin(t*2*math.pi*(170-60*t))*.30)*amp
            sample+=random.uniform(-1,1)*.07*math.exp(-t*5)
        elif kind=="dry":
            sample=random.uniform(-1,1)*.14*math.exp(-t*95)
        else:
            if kind=="bolt":peaks=[(.02,.11),(.18,.11)]
            elif kind=="magout":peaks=[(.05,.11),(.29,.10)]
            else:peaks=[(.02,.12),(.20,.15)]
            sample=0
            for time,gain in peaks:
                delta=t-time
                if delta>=0:
                    sample+=(random.uniform(-1,1)*.45+
                             math.sin(2*math.pi*900*delta)*.16)*gain*math.exp(-delta*65)
        sample=max(-.98,min(.98,sample))
        samples.append(int(sample*32767))
    with wave.open(str(root/"sounds"/(name+".wav")),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE)
        w.writeframes(struct.pack("<"+"h"*len(samples),*samples))

for name,kind,d in [
 ("ak47dev_fire","fire",.42),("ak47dev_dry","dry",.13),
 ("ak47dev_magout","magout",.36),("ak47dev_magin","magin",.42),
 ("ak47dev_bolt","bolt",.44)]:
    save_sound(name,kind,d)
print(f"Generated original GLB {len(glb)} bytes, {len(parts)} parts, 5 skeletal bones, "
      "3 animation sections, 5 original WAV Foley clips + editable Blockbench file")
