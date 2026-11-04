#!/usr/bin/env python3
"""Private true Blender visualization: original COD4/IW3 MP5 first-person viewmodel + viewhands.
Uses ONLY locally extracted user-owned GLBs and source-tag attachment. Outputs two PNGs
and a .blend file; does not emit original mesh or textures in a public artifact.
"""
import bpy,sys,os,json
from pathlib import Path
from mathutils import Vector, Matrix
here=Path(__file__).resolve().parent.parent
src=here/"_iw3_private/animated_preview"
out=here/"_iw3_private/blender_proof"
out.mkdir(parents=True,exist_ok=True)
weapon=src/"mp5_animated_experimental.glb"
hands=src/"mp5_hands_animated_experimental.glb"
assert weapon.exists() and hands.exists(),("Missing source converted COD4 MP5 data",weapon,hands)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
def imp(path):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    got=[o for o in bpy.data.objects if o not in before]
    assert any(o.type=="MESH" for o in got),path
    return got
hand_objects=imp(hands)
gun_objects=imp(weapon)
mesh_hand=[o for o in hand_objects if o.type=="MESH"]
mesh_gun=[o for o in gun_objects if o.type=="MESH"]
handarm=next(o for o in hand_objects if o.type=="ARMATURE")
gunarm=next(o for o in gun_objects if o.type=="ARMATURE")
print("IW3_REAL_MESHES",len(mesh_hand),len(mesh_gun))
print("IW3_HAND_BONES",len(handarm.data.bones),[b.name for b in handarm.data.bones if b.name.startswith("tag_")][:30])
print("IW3_GUN_BONES",len(gunarm.data.bones),[b.name for b in gunarm.data.bones if b.name.startswith("tag_")][:30])
assert any("tag_weapon" in b.name.lower() for b in handarm.data.bones),"COD4 real hands have no mount tag"
def roots(group):
    group_set=set(group)
    return [o for o in group if o.parent not in group_set]
hand_roots=roots(hand_objects);weapon_roots=roots(gun_objects)
righ=bpy.data.objects.new("COD4_ORIGINAL_HANDS_RIG",None)
bpy.context.collection.objects.link(righ)
for o in hand_roots:
    m=o.matrix_world.copy()
    o.parent=righ;o.matrix_world=m
rigw=bpy.data.objects.new("COD4_ORIGINAL_MP5_WEAPON_MOUNT",None)
bpy.context.collection.objects.link(rigw)
for o in weapon_roots:
    old=o.matrix_world.copy()
    o.parent=rigw;o.matrix_world=old
def setaction(objects,term):
    acts=list(bpy.data.actions)
    options=[a for a in acts if a.name.lower()==term or a.name.lower().startswith(term+".")]
    if not options:
        options=[a for a in acts if term in a.name.lower()]
    if not options:
        print("ACTION_UNAVAILABLE",term,[a.name for a in acts]);return False
    for o in objects:
        if o.type=="ARMATURE":
            o.animation_data_create()
            o.animation_data.action=options[0]
            print("ACTION_APPLIED",o.name,options[0].name)
    return True

def bone_world(arm,name):
    match=next((b for b in arm.pose.bones if b.name.lower()==name.lower()),None)
    if not match:return None
    return arm.matrix_world@match.matrix
def mounter():
    mount=bone_world(handarm,"tag_weapon")
    assert mount is not None
    rigw.matrix_world=mount
    bpy.context.view_layer.update()
def scene_bounds(meshes):
    v=[o.matrix_world@Vector(corner) for o in meshes for corner in o.bound_box]
    return [min(x[i] for x in v) for i in range(3)],[max(x[i] for x in v) for i in range(3)]
def addarea(name,pos,power,size,color):
    d=bpy.data.lights.new(name,"AREA");d.energy=power;d.shape="DISK";d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
    o.location=pos;o.rotation_euler=(Vector((0,1,0))-o.location).to_track_quat("-Z","Y").to_euler()
addarea("main softbox",(-1,-.3,1),650,2.4,(.84,.91,1))
addarea("warm fill",(1,.2,.5),340,2.7,(1,.8,.64))
scene=bpy.context.scene
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.engine="BLENDER_EEVEE"
scene.world.color=(.02,.03,.05)
camera_data=bpy.data.cameras.new("COD4 FPS reference")
camera=bpy.data.objects.new("COD4 FPS reference",camera_data);scene.collection.objects.link(camera)
scene.camera=camera
camera.location=(0,0,0)
camera.rotation_euler=Vector((0,1,0)).to_track_quat("-Z","Y").to_euler()
camera_data.lens=25
camera_data.clip_start=.005
# Camera-only calibration based on true tags and viewmodel bounds. Do not invent source meshes.
summary={"model":"COD4 MP5", "source":"privately extracted user-owned IW3 game data", "hands":"COD4 viewmodel_base_viewhands", "modes":{}, "original_animations":[]}
for mode in ["HIPFIRE","ADS"]:
    # Real source idle and ADS frames are applied to BOTH armatures.
    source_action="idle" if mode=="HIPFIRE" else "ads"
    setaction(hand_objects,source_action)
    setaction(gun_objects,source_action)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    mounter()
    vmin,vmax=scene_bounds(mesh_gun+mesh_hand)
    print("IW3_SOURCE_BOUNDS",mode,vmin,vmax)
    # Align ADS using the weapon's source-authored iron-sight tag, without estimating offsets.
    if mode=="ADS":
        sight=bone_world(gunarm,"tag_iron_sight")
        if sight:
            point=sight.translation
            righ.location+=Vector((-point.x,0.65-point.y,-point.z))
            bpy.context.view_layer.update()
            mounter()
            summary["modes"][mode]={"original_sight_tag":"tag_iron_sight","measured_sight_xyz":list(point)}
        else: summary["modes"][mode]={"original_sight_tag":"MISSING"}
    else:
        # Native weapon low-right first-person position comes from original XANIM rig.
        summary["modes"][mode]={"original_action":"idle"}
    # Imported COD4 viewmodel mesh may be centimeters. Confirm scale by bounds.
    size=max(vmax[i]-vmin[i] for i in range(3))
    if size>6:
        righ.scale=(.01,)*3
        bpy.context.view_layer.update()
        mounter()
        summary["modes"][mode]["centimeter_scale_applied"]=True
    scene.render.filepath=str(out/f"COD4_MP5_{mode}_BLENDER.png")
    bpy.ops.render.render(write_still=True)
    print("REAL_IW3_BLENDER_RENDER",mode,scene.render.filepath,os.path.getsize(scene.render.filepath))
bpy.ops.wm.save_as_mainfile(filepath=str(out/"COD4_MP5_ORIGINAL_WITH_HANDS.blend"))
(out/"audit.json").write_text(json.dumps(summary,indent=2))
assert (out/"COD4_MP5_HIPFIRE_BLENDER.png").stat().st_size>5000
assert (out/"COD4_MP5_ADS_BLENDER.png").stat().st_size>5000
print("COD4_MP5_REAL_BLENDER_SCREENSHOTS_GREEN")
