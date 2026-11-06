#!/usr/bin/env python3
"""Static raw-model inspection through the same textured depth renderer.

The former 65,000-triangle painter limit rejected the 144,134-triangle HD
rifle before pose/ADS gates could run. Raw model rest views do not certify ADS.
"""
import argparse
from pathlib import Path
import numpy as np
from voxelize import read_glb,read_accessor
from texture_atlas import embedded_surface
from render_pose_sequence import camera_params
from depth_preview import DepthPreview


def render(file,output,views):
    doc,raw=read_glb(file);geometry=[];surfaces=[]
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            attrs=primitive['attributes']
            xyz=np.asarray(read_accessor(doc,raw,attrs['POSITION']))
            ix=np.asarray(read_accessor(doc,raw,primitive['indices'])).reshape(-1)
            colors=(np.asarray(read_accessor(doc,raw,attrs['COLOR_0']))[:,:3]
                    if 'COLOR_0' in attrs else np.ones((len(xyz),3)))
            factor=doc['materials'][primitive.get('material',0)].get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1])
            geometry.append((xyz,ix,colors*np.array(factor[:3])))
            surfaces.append(embedded_surface(doc,raw,primitive))
    points=np.vstack([g[0] for g in geometry])
    preview=DepthPreview();preview.set_surfaces(surfaces)
    try:
        reports=[]
        for name,orientation in views:
            report=preview.orthographic(geometry,camera_params(points,orientation),
                'AK47 | RAW MODEL REST | STATIC GEOMETRY INSPECTION',output/name)
            reports.append({'file':name,**report})
        return reports
    finally:preview.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True)
    p.add_argument('--hands',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    reports=render(a.input,a.output,[('ak47_cod4_blockstyle_3quarter.png',(28,25)),
        ('ak47_cod4_blockstyle_profile.png',(0,5)),('ak47_cod4_blockstyle_top.png',(3,82))])
    if a.hands and a.hands.is_file():
        reports+=render(a.hands,a.output,[('ak47_cod4_blockstyle_hands.png',(30,25))])
    for report in reports:print(report)


if __name__=='__main__':main()
