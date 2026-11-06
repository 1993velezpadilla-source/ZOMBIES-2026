"""Compose native sparse ADS layers, calibrate emitted irons, and bake full clips.

Outputs are private animated GLBs; only labeled raster/metadata evidence may be
published by CI. This is a viewmodel preview/controller export, not an APK.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from voxelize import read_glb, pack_new, write_glb
from render_pose_sequence import PoseScene, local_matrix, quat_matrix
from render_mounted_viewhands import compose, OAT_TO_NATIVE, transform_points
from fps_composition_gate import gif_timing
from depth_preview import DepthPreview

IDLE='viewmodel_ak47_idle'
UP='viewmodel_ak47_ads_up'
DOWN='viewmodel_ak47_ads_down'
FIRE='viewmodel_ak47_fire_ads'
NAMES={'hip':'ak47_hip_idle','enter':'ak47_ads_enter','hold':'ak47_ads_hold',
       'fire':'ak47_ads_fire','exit':'ak47_ads_exit'}


def quaternion(matrix):
    """Unit quaternion from an orthonormal rotation, including half turns."""
    m=np.asarray(matrix)[:3,:3];trace=float(np.trace(m))
    if trace>0:
        s=math.sqrt(1+trace)*2
        q=np.array([(m[2,1]-m[1,2])/s,(m[0,2]-m[2,0])/s,
                    (m[1,0]-m[0,1])/s,s/4])
    else:
        i=int(np.argmax(np.diag(m)));j=(i+1)%3;k=(i+2)%3
        s=math.sqrt(1+m[i,i]-m[j,j]-m[k,k])*2
        q=np.zeros(4);q[i]=s/4;q[j]=(m[j,i]+m[i,j])/s
        q[k]=(m[k,i]+m[i,k])/s;q[3]=(m[k,j]-m[j,k])/s
    q/=np.linalg.norm(q)
    return q if q[3]>=0 else -q


def find_sights(rifle):
    """Landmarks on actual upward-facing HD quads, not screen-space guesses."""
    top=[]
    for mesh,pos,ix,joints,weights,colors in rifle.geometry:
        if len(pos)%4:raise ValueError('expected emitted HD quads')
        quads=pos.reshape(-1,4,3);centers=quads.mean(1)
        normal=np.cross(quads[:,1]-quads[:,0],quads[:,2]-quads[:,0])
        mask=(normal[:,1]>1e-9)&(np.abs(normal[:,0])<1e-7)&(np.abs(normal[:,2])<1e-7)
        top.append(centers[mask])
    top=np.vstack(top)
    front=top[(top[:,0]>24.35)&(top[:,0]<24.7)&(np.abs(top[:,2])<.09)&(top[:,1]>3.4)]
    rear=top[(top[:,0]>6.5)&(top[:,0]<7.1)&(np.abs(top[:,2])>.25)&(np.abs(top[:,2])<.65)&(top[:,1]>3.5)]
    if len(front)==0 or len(rear)==0:raise ValueError('AK iron landmark regions missing')
    front=front[np.abs(front[:,1]-front[:,1].max())<1e-6]
    rear=rear[np.abs(rear[:,1]-rear[:,1].max())<1e-6]
    return rear.mean(0),front.mean(0)


def full_ads_matrix(rifle,hands):
    hw=hands.world(IDLE,0,layers=((UP,hands.duration(UP)),))
    rw=rifle.world(IDLE,0)
    root=next(i for i,n in enumerate(rifle.nodes) if n.get('name')=='j_gun')
    return hands.tag(hw)@OAT_TO_NATIVE@rw[root]@rifle.IBM[0][0]


def calibrate(rifle,hands):
    rear,front=find_sights(rifle)
    matrix=full_ads_matrix(rifle,hands)
    pair=transform_points(np.array([rear,front]),matrix)
    direction=pair[1]-pair[0];direction/=np.linalg.norm(direction)
    right=np.cross(direction,[0.,1.,0.]);right/=np.linalg.norm(right)
    up=np.cross(right,direction)
    rotation=np.array([direction,up,right])
    translation=np.array([pair[0,0],0.,0.])-rotation@pair[0]
    return {'rear_local':rear.tolist(),'front_local':front.tolist(),
            'rotation_quaternion':quaternion(rotation).tolist(),
            'translation':translation.tolist(),
            'rotation_degrees':math.degrees(math.acos(np.clip((np.trace(rotation)-1)*.5,-1,1))),
            'method':'one fixed rigid correction from actual emitted iron quads; applied to hand root only'}


def correction_matrix(config,amount=1.):
    q=np.array(config['rotation_quaternion'])
    # Shortest-path identity SLERP for a constant alignment transform.
    angle=math.acos(float(np.clip(q[3],-1,1)))
    value=(np.array([0.,0.,0.,1.]) if angle<1e-12 else
           np.r_[q[:3]*(math.sin(angle*amount)/math.sin(angle)),math.cos(angle*amount)])
    out=quat_matrix(value);out[:3,3]=np.array(config['translation'])*amount
    return out


def phase_values(scene,phase,t,duration,*,hands,config):
    fraction=float(np.clip(t/duration,0,1))
    base=FIRE if phase=='fire' else IDLE
    base_time=t if phase=='fire' else 0.
    amount=(fraction if phase=='enter' else 1-fraction if phase=='exit' else 0. if phase=='hip' else 1.)
    layers=()
    if hands and phase!='hip':
        clip=DOWN if phase=='exit' else UP
        source_time=(fraction if phase in ('enter','exit') else 1.)*scene.duration(clip)
        layers=((clip,source_time),)
    values=scene.local_values(base,base_time,layers=layers)
    if hands:
        root=next(i for i,n in enumerate(scene.nodes) if n.get('name')=='tag_view')
        matrix=correction_matrix(config,amount)@local_matrix(scene.nodes[root],values.get(root,{}))
        values[root]={'translation':matrix[:3,3], 'rotation':quaternion(matrix[:3,:3]), 'scale':np.ones(3)}
    return values


def bake(source,target,*,hands,config,durations):
    scene=PoseScene(source);doc=deepcopy(scene.doc);raw=bytearray(scene.binary)
    joints=sorted({n for skin in doc['skins'] for n in skin['joints']})
    for phase,name in NAMES.items():
        duration=durations[phase]
        times=np.linspace(0.,duration,max(2,int(math.ceil(duration*60))+1))
        # Include every source key time, rescaled through weaponPosFrac.
        relevant=[(FIRE,1.)] if phase=='fire' else []
        if hands and phase in ('enter','exit'):
            clip=UP if phase=='enter' else DOWN
            relevant.append((clip,duration/scene.duration(clip)))
        for clip,scale in relevant:
            times=np.union1d(times,np.concatenate([ts*scale for _,_,ts,_,_ in scene.tracks[clip]]))
        frames=[phase_values(scene,phase,float(t),duration,hands=hands,config=config) for t in times]
        time_accessor=pack_new(doc,raw,[(float(t),) for t in times],'SCALAR')
        animation={'name':name,'samplers':[],'channels':[],
                   'extras':{'composed_source_ads':True,'loop':phase in ('hip','hold'),
                            'root_calibration_on_hands_only':hands}}
        for joint in joints:
            node=scene.nodes[joint]
            for prop,kind,default in [('translation','VEC3',[0,0,0]),('rotation','VEC4',[0,0,0,1]),('scale','VEC3',[1,1,1])]:
                rows=[tuple(frame.get(joint,{}).get(prop,node.get(prop,default))) for frame in frames]
                accessor=pack_new(doc,raw,rows,kind)
                sampler=len(animation['samplers'])
                animation['samplers'].append({'input':time_accessor,'output':accessor,'interpolation':'LINEAR'})
                animation['channels'].append({'sampler':sampler,'target':{'node':joint,'path':prop}})
        doc.setdefault('animations',[]).append(animation)
    write_glb(target,doc,raw)


def sight_metrics(rifle,hands,config,clip,t=0.,fov=50.,width=1100,height=640):
    rw=rifle.world(clip,t);hw=hands.world(clip,t)
    root=next(i for i,n in enumerate(rifle.nodes) if n.get('name')=='j_gun')
    matrix=hands.tag(hw)@OAT_TO_NATIVE@rw[root]@rifle.IBM[0][0]
    points=transform_points(np.array([config['rear_local'],config['front_local']]),matrix)
    focal=width*.5/math.tan(math.radians(fov*.5))
    pixels=np.c_[width*.5+focal*points[:,2]/points[:,0],height*.5-focal*points[:,1]/points[:,0]]
    center=np.array([width*.5,height*.5])
    return {'projected_rear_front_pixels':pixels.tolist(),
            'maximum_center_error_pixels':float(np.linalg.norm(pixels-center,axis=1).max()),
            'rear_front_separation_pixels':float(np.linalg.norm(pixels[0]-pixels[1])),
            'in_front_of_camera':bool(np.all(points[:,0]>.25))}


def verify_export(source_rifle,source_hands,rifle,hands,audit):
    audit['source_preservation']=[]
    for old,new in ((source_rifle,rifle),(source_hands,hands)):
        if new.doc['animations'][:len(old.animations)]!=old.doc['animations']:
            raise ValueError('original animation definitions changed')
        if new.binary[:len(old.binary)]!=old.binary:
            raise ValueError('original binary data changed')
        if any(new.doc[k]!=old.doc[k] for k in ('nodes','skins','meshes')):
            raise ValueError('base geometry or rig changed during ADS bake')
        audit['source_preservation'].append({'original_clips':len(old.animations),
            'total_clips':len(new.animations),'original_binary_prefix_unchanged':True,
            'nodes_skins_meshes_unchanged':True})
    hip=hands.world(NAMES['hip'],0);inverse=np.linalg.inv(hands.tag(hip))
    relative=[inverse@matrix for matrix in hip]
    joints=[n for n in hands.doc['skins'][0]['joints'] if any(word in hands.nodes[n].get('name','')
            for word in ('wrist','thumb','index','mid_','pinky','ring','webbing'))]
    if not joints:raise ValueError('visible hand joints missing')
    maximum=0.
    for phase in ('enter','hold','exit'):
        for time in np.linspace(0,audit['playback_durations'][phase],11):
            world=hands.world(NAMES[phase],float(time));inverse=np.linalg.inv(hands.tag(world))
            maximum=max(maximum,max(float(np.abs(inverse@world[j]-relative[j]).max()) for j in joints))
    if maximum>1e-5:raise ValueError('ADS changed the base grip relative to the weapon')
    audit['grip_relative_joint_matrix_maximum_difference']=maximum
    boundaries={}
    for left,t,right,u in [('hip',0,'enter',0),('enter',audit['playback_durations']['enter'],'hold',0),
                           ('hold',0,'exit',0),('exit',audit['playback_durations']['exit'],'hip',0)]:
        difference=np.array(hands.world(NAMES[left],t))-np.array(hands.world(NAMES[right],u))
        boundaries[left+'->'+right]=float(np.max(np.abs(difference)))
    if max(boundaries.values())>.003:raise ValueError('discontinuous composed ADS boundary')
    audit['boundary_world_matrix_maximum_difference']=boundaries
    fire=[sight_metrics(rifle,hands,audit['calibration'],NAMES['fire'],float(t))['maximum_center_error_pixels']
          for t in np.linspace(0,audit['playback_durations']['fire'],11)]
    if max(fire)<1. or fire[-1]>.1:raise ValueError('source recoil missing or did not return to aim')
    audit['ads_fire_maximum_landmark_displacement_pixels']=max(fire)
    audit['ads_fire_final_landmark_center_error_pixels']=fire[-1]


def build(rifle_path,hands_path,weapon_path,output):
    output.mkdir(parents=True,exist_ok=True)
    rifle=PoseScene(rifle_path);hands=PoseScene(hands_path)
    fields=weapon_path.read_text(encoding='latin-1').split('\\')
    fields=dict(zip(fields[1::2],fields[2::2]))
    durations={'hip':1.,'enter':float(fields['adsTransInTime']),'hold':1.,
               'fire':min(rifle.duration(FIRE),hands.duration(FIRE)),
               'exit':float(fields['adsTransOutTime'])}
    config=calibrate(rifle,hands)
    target_rifle=output/'AK47_ADS_512_RIFLE_PRIVATE.glb'
    target_hands=output/'AK47_ADS_HANDS_PRIVATE.glb'
    bake(rifle_path,target_rifle,hands=False,config=config,durations=durations)
    bake(hands_path,target_hands,hands=True,config=config,durations=durations)
    r=PoseScene(target_rifle);h=PoseScene(target_hands)
    metrics=sight_metrics(r,h,config,NAMES['hold'])
    if metrics['maximum_center_error_pixels']>1. or not metrics['in_front_of_camera']:
        raise ValueError('baked ADS iron alignment failed: '+str(metrics))
    audit={'method':'native idle/fire pose plus sparse tag_ads layer; baked complete channels',
           'source_reference':'SwagSoftware/KisakCOD src/cgame/cg_weapons.cpp PlayADSAnim and WeaponRunXModelAnims',
           'source_ads_up_down_seconds':[hands.duration(UP),hands.duration(DOWN)],
           'playback_durations':durations,'clips':NAMES,'calibration':config,'ads_metrics':metrics,
           'camera_eye':[0.,0.,0.],'camera_forward':[1.,0.,0.],'camera_fixed':True,
           'hip_fov':75.,'ads_fov':float(fields['adsZoomFov']),
           'fov_interpolation':'linear review curve; source ADS endpoint FOV',
           'original_clips_preserved':[len(rifle.names()),len(hands.names())],
           'derived_clips_added_per_model':5,'runtime_android_verified':False,
           'anatomical_contact_verified':False,'frames':[]}
    verify_export(rifle,hands,r,h,audit)
    timeline=[('hip',.4),('enter',durations['enter']),('hold',.4),
              ('fire',durations['fire']),('hold',.25),('exit',durations['exit']),('hip',.4)]
    preview=DepthPreview(center_y_offset=0)
    preview.set_surfaces(r.posed_surfaces()+h.posed_surfaces())
    images=[];delays=[]
    rest=h.tag(h.world(NAMES['hip'],0))
    try:
        for segment,(phase,length) in enumerate(timeline):
            count=max(2,int(math.ceil(length*60)))
            times=np.linspace(0.,length,count,endpoint=False)
            delays.extend(gif_timing(length,count))
            for frame,time in enumerate(times):
                clip=NAMES[phase];sample=min(float(time),durations[phase])
                geometry,mount=compose(r,h,clip,clip,sample,rest)
                frac=(sample/durations[phase] if phase=='enter' else
                      1-sample/durations[phase] if phase=='exit' else 0. if phase=='hip' else 1.)
                fov=75+(float(fields['adsZoomFov'])-75)*frac
                path=output/f'ads_{segment}_{frame:03d}.png'
                report=preview.render(geometry,np.zeros(3),1,
                    f'AK47 512 | {phase.upper()} | native composed ADS',path,fov=fov,forward_override=[1,0,0])
                with Image.open(path) as im:
                    image=im.copy();draw=ImageDraw.Draw(image)
                    # Aim center is exactly the perspective's optical center.
                    for a,b in [((537,320),(543,320)),((557,320),(563,320)),
                                ((550,307),(550,313)),((550,327),(550,333))]:
                        draw.line((a,b),fill=(220,225,230),width=1)
                    image.save(path,optimize=True)
                    images.append(image.resize((880,512),Image.Resampling.LANCZOS))
                audit['frames'].append({'phase':phase,'time':sample,'file':path.name,
                    'fov':fov,'geometry_pixels':report['geometry_pixels'],
                    'textured_primitives':report['textured_primitives'],
                    'mount_error':mount['tag_alignment_error']})
        for phase in ('hip','hold'):
            geometry,_=compose(r,h,NAMES[phase],NAMES[phase],0,rest)
            preview.render(geometry,np.zeros(3),1,f'AK47 512 | {phase.upper()} | fixed optical center',
                           output/f'AK47_{phase.upper()}_512.png',fov=75 if phase=='hip' else float(fields['adsZoomFov']),forward_override=[1,0,0])
    finally:preview.close()
    images[0].save(output/'AK47_ADS_512.gif',save_all=True,append_images=images[1:],
                   duration=delays,loop=0,optimize=False,disposal=2)
    audit['gif_frames']=len(images);audit['gif_duration_ms']=sum(delays)
    (output/'ads-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({'frames':len(images),'duration_ms':sum(delays),'metrics':metrics,'calibration':config}))
    return audit


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('rifle','hands','weapon','output'):p.add_argument('--'+key,type=Path,required=True)
    args=p.parse_args();build(args.rifle,args.hands,args.weapon,args.output)
