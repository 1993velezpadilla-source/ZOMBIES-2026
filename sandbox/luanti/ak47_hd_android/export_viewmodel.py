"""Private COD4 block viewmodel -> Luanti's single-skin glTF subset.

Flatten only weighted joints, bake their world motion, split u16 mesh buffers,
and bind external textures. No source/derived game binaries belong in git.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from io import BytesIO
import json
import math
from pathlib import Path
import sys
import numpy as np
from PIL import Image

BLOCK=Path(__file__).resolve().parents[1]/'iw3_blockstyle'
sys.path.insert(0,str(BLOCK))
from voxelize import read_glb,read_accessor,pack_new,write_glb
from render_pose_sequence import PoseScene
from ads_pipeline import quaternion,NAMES
from render_mounted_viewhands import OAT_TO_NATIVE

CLIPS=[*NAMES.values(),'viewmodel_ak47_fire','viewmodel_ak47_reload','viewmodel_ak47_reload_empty']
MAX_VERTICES=64000


def export(rifle_path,hands_path,output):
    output.mkdir(parents=True,exist_ok=True)
    (output/'models').mkdir(exist_ok=True);(output/'textures').mkdir(exist_ok=True)
    r=PoseScene(rifle_path);h=PoseScene(hands_path);scenes=[r,h]
    used=[]
    for scene in scenes:
        ids=set()
        for _,_,_,joints,weights,_ in scene.geometry:
            ids.update(int(j) for j in joints[weights>1e-8])
        used.append(sorted(ids))
    count=sum(map(len,used))
    if count+2>64:raise ValueError('weighted joint palette exceeds 64-node GPU target: '+str(count))
    mapping=[{j:i+sum(map(len,used[:component])) for i,j in enumerate(used[component])}
             for component in range(2)]
    doc={'asset':{'version':'2.0','generator':'AK47 HD Luanti adapter'},
         'buffers':[{'byteLength':0}],'bufferViews':[],'accessors':[],
         'materials':[{'name':'rifle_512','pbrMetallicRoughness':{'baseColorTexture':{'index':0}}},
                      {'name':'hand_palette','pbrMetallicRoughness':{'baseColorTexture':{'index':1}}}],
         'textures':[{'sampler':0},{'sampler':0}],
         'samplers':[{'magFilter':9728,'minFilter':9728,'wrapS':33071,'wrapT':33071}],
         'meshes':[{'name':'AK47_HD_combined','primitives':[]}],
         'nodes':[],'skins':[],'animations':[],
         'extras':{'external_texture_slots':['ak47hd_512.png','ak47hd_hands.png']}}
    raw=bytearray();inverse=[]
    for component,scene in enumerate(scenes):
        skin=scene.doc['skins'][0]
        for index in used[component]:
            node=skin['joints'][index]
            doc['nodes'].append({'name':('rifle:' if component==0 else 'hands:')+scene.nodes[node].get('name',str(node))})
            inverse.append(scene.IBM[0][index].reshape(-1,order='F').tolist())
    # glTF loader negates Z. Rotate native +X forward into glTF -Z first;
    # loaded result is +Z forward, +X right, +Y up in the wield camera.
    G=np.array([[0.,0,1,0],[0,1,0,0],[-1,0,0,0],[0,0,0,1]])
    root=count;mesh_node=count+1
    doc['nodes'] += [{'name':'camera_basis','matrix':G.reshape(-1,order='F').tolist(),
                      'children':list(range(count))+[mesh_node]},
                     {'name':'combined_mesh','mesh':0,'skin':0}]
    doc['skins']=[{'joints':list(range(count)),'skeleton':root,
                   'inverseBindMatrices':pack_new(doc,raw,inverse,'MAT4')}]
    doc['scenes']=[{'nodes':[root]}];doc['scene']=0
    palette=sorted({tuple(np.clip(np.rint(color*255),0,255).astype(int))
                    for _,_,_,_,_,colors in h.geometry for color in colors})
    width=1
    while width<len(palette):width*=2
    width=max(width,16)
    colors=np.array(palette+[palette[-1]]*(width-len(palette)),dtype='u1')[None,:,:]
    hand_image=Image.fromarray(colors);hand_image.save(output/'textures/ak47hd_hands.png')
    color_ids={color:i for i,color in enumerate(palette)}
    buffer_counts=[];triangles=[]
    for component,scene in enumerate(scenes):
        buffers=0;faces=0
        for mesh,pos,indices,joints,weights,tints in scene.geometry:
            if len(pos)%4:raise ValueError('source shell no longer has separate quad vertices')
            # Geometry order and primitives are one-to-one for these outputs.
            source_index=next(i for i,g in enumerate(scene.geometry) if g[1] is pos)
            source_primitive=[p for m in scene.doc['meshes'] for p in m['primitives']][source_index]
            normals=np.array(read_accessor(scene.doc,scene.binary,source_primitive['attributes']['NORMAL']))
            if component==0:
                uv=np.array(read_accessor(scene.doc,scene.binary,source_primitive['attributes']['TEXCOORD_0']))
            else:
                rgb=np.clip(np.rint(tints*255),0,255).astype(int)
                uv=np.array([[(color_ids[tuple(c)]+.5)/width,.5] for c in rgb])
            mapped=np.zeros_like(joints)
            for lane in range(4):
                for old,new in mapping[component].items():
                    mask=(joints[:,lane]==old)&(weights[:,lane]>1e-8);mapped[mask,lane]=new
            for start in range(0,len(pos),MAX_VERTICES):
                stop=min(start+MAX_VERTICES,len(pos));select=slice(start,stop)
                ix=indices[(indices>=start)&(indices<stop)]-start
                if len(ix)%6:raise ValueError('mesh split cuts through a source quad')
                attrs={}
                for key,rows,kind,ctype in [
                    ('POSITION',pos[select],'VEC3',5126),('NORMAL',normals[select],'VEC3',5126),
                    ('TEXCOORD_0',uv[select],'VEC2',5126),('JOINTS_0',mapped[select],'VEC4',5123),
                    ('WEIGHTS_0',weights[select],'VEC4',5126)]:
                    attrs[key]=pack_new(doc,raw,rows.tolist(),kind,ctype,target=34962)
                idx=pack_new(doc,raw,[(int(i),) for i in ix],'SCALAR',5123,target=34963)
                doc['meshes'][0]['primitives'].append({'attributes':attrs,'indices':idx,'mode':4,'material':component})
                buffers+=1;faces+=len(ix)//3
        buffer_counts.append(buffers);triangles.append(faces)
    atlas=r.surfaces[0]['image'];atlas.save(output/'textures/ak47hd_512.png')
    def joint_frames(name,t):
        rw=r.world(name,t);hw=h.world(name,t);mount=h.tag(hw)@OAT_TO_NATIVE
        return [rw_node for comp,scene,world in [(0,r,rw),(1,h,hw)]
                for index in used[comp]
                for rw_node in [(mount@world[scene.doc['skins'][0]['joints'][index]] if comp==0
                                 else world[scene.doc['skins'][0]['joints'][index]])]]
    durations={}
    for name in CLIPS:
        duration=min(r.duration(name),h.duration(name));durations[name]=duration
        duration=max(duration,1e-6)
        times=np.linspace(0,duration,max(2,int(math.ceil(duration*120))+1))
        for scene in scenes:
            times=np.union1d(times,np.concatenate([ts for _,_,ts,_,_ in scene.tracks[name]]))
        times=np.unique(times.astype('f4'))
        frames=[joint_frames(name,float(t)) for t in times]
        time_acc=pack_new(doc,raw,[(float(t),) for t in times],'SCALAR')
        anim={'name':name,'samplers':[],'channels':[]}
        for joint in range(count):
            for prop,kind,rows in [
                ('translation','VEC3',[frame[joint][:3,3].tolist() for frame in frames]),
                ('rotation','VEC4',[quaternion(frame[joint][:3,:3]).tolist() for frame in frames])]:
                out=pack_new(doc,raw,rows,kind);sampler=len(anim['samplers'])
                anim['samplers'].append({'input':time_acc,'output':out,'interpolation':'LINEAR'})
                anim['channels'].append({'sampler':sampler,'target':{'node':joint,'path':prop}})
        doc['animations'].append(anim)
    for node,matrix in zip(doc['nodes'],joint_frames(NAMES['hip'],0)):
        node['translation']=matrix[:3,3].tolist();node['rotation']=quaternion(matrix[:3,:3]).tolist()
    target=output/'models/ak47hd.glb';write_glb(target,doc,raw)
    # Standard embedded-texture copy only for numerical/raster QA; never ship it.
    preview_doc=deepcopy(doc);preview_raw=bytearray(raw);preview_doc['images']=[]
    for i,image in enumerate((atlas,hand_image)):
        stream=BytesIO();image.save(stream,format='PNG');encoded=stream.getvalue()
        while len(preview_raw)%4:preview_raw.append(0)
        view=len(preview_doc['bufferViews']);preview_doc['bufferViews'].append({'buffer':0,'byteOffset':len(preview_raw),'byteLength':len(encoded)})
        preview_raw.extend(encoded);preview_doc['images'].append({'bufferView':view,'mimeType':'image/png'})
        preview_doc['textures'][i]['source']=i
    validation=output/'VALIDATION_PRIVATE.glb';write_glb(validation,preview_doc,preview_raw)
    merged=PoseScene(validation)
    worst=0.
    for name in CLIPS:
        for fraction in (0.,.25,.5,.75,1.):
            t=durations[name]*fraction
            # Compare joint matrices, independent of topology batching.
            actual=merged.world(name,t);expected=joint_frames(name,t)
            for index,want in enumerate(expected):
                worst=max(worst,float(np.abs(actual[index]-G@want).max()))
    if worst>.005:raise ValueError('flattened source motion mismatch: '+str(worst))
    report={'joint_count':count,'total_nodes':count+2,'mesh_buffers':buffer_counts,
            'triangles':triangles,'max_vertices_per_buffer':MAX_VERTICES,
            'texture_slots':['ak47hd_512.png','ak47hd_hands.png'],'durations':durations,
            'flattened_joint_matrix_maximum_difference':worst,
            'camera_forward_after_loader':'+Z','camera_up':'+Y',
            'private_model':str(target),'private_outputs':True}
    # Golden deformed vertices for the actual Luanti C++ loader/skinner probe.
    # Kept beside the private model, never in public metadata artifacts.
    golden=[]
    for name,fraction in [(NAMES['hip'],0.),(NAMES['hold'],0.),
                          (NAMES['fire'],.5),('viewmodel_ak47_reload',.5),
                          ('viewmodel_ak47_reload_empty',.7)]:
        time=durations[name]*fraction;geometry,_,_=merged.poses(name,time);points=[]
        for buffer,(xyz,_,_) in enumerate(geometry):
            for vertex in sorted({0,len(xyz)//3,len(xyz)//2,len(xyz)-1}):
                p=xyz[vertex].copy();p[2]*=-1
                points.append({'buffer':buffer,'vertex':vertex,'xyz':p.tolist()})
        golden.append({'clip':name,'time':time,'points':points})
    (output/'GOLDEN_PRIVATE.json').write_text(json.dumps(golden))
    (output/'viewmodel-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report));return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rifle',type=Path,required=True)
    p.add_argument('--hands',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();export(a.rifle,a.hands,a.output)
