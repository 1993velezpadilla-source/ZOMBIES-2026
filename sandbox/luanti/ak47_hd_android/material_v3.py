"""Photo-based 512x512 AK47 and adult hand atlases with denser UV islands.

Photographic microdetail is CC0 Poly Haven; no game IP is included.
Keep the original animation/geometry and 59-60 FPS render path intact.
Luanti's material loader currently consumes baseColor only; these are color
atlases, not unsupported claims of PBR / real-time ray tracing.
"""
from __future__ import annotations
import os
from pathlib import Path
import numpy as np
from PIL import Image

from material_v2 import make_rifle_atlas as procedural_rifle
from material_v2 import make_hand_atlas as procedural_hands
from material_v2 import HAND_TILES, SIZE
from texture_atlas import TILES
from photo_materials import SOURCES, verify_image_bytes

P=(255,255,255)

def photo_library():
    folder=os.environ.get('AK47_CC0_TEXTURE_DIR')
    required=os.environ.get('AK47_REQUIRE_CC0_PHOTOS')=='1'
    if not folder:
        if required: raise RuntimeError('AK47_CC0_TEXTURE_DIR must point to verified CC0 photos')
        return {}
    root=Path(folder)
    materials={}
    for name in SOURCES:
        path=root/(name+'.jpg')
        if not path.is_file():
            if required:raise FileNotFoundError(path)
            return {}
        data=path.read_bytes()
        verify_image_bytes(data,name)
        with Image.open(path) as image:
            materials[name]=image.convert('RGB')
    return materials

def crop_surface(photo,size,seed,rotate=False):
    """Crop a large photograph rather than downscaling it into muddy noise."""
    w,h=photo.size
    edge=int(min(w,h)*.78)
    x=max(0,min(w-edge,int((seed*.113%1)*(w-edge))))
    y=max(0,min(h-edge,int((seed*.317%1)*(h-edge))))
    out=photo.crop((x,y,x+edge,y+edge))
    if rotate:out=out.transpose(Image.Transpose.ROTATE_90)
    return out.resize(size,Image.Resampling.LANCZOS)

def replace_region(canvas,base,photo,box,kind):
    x0,y0,x1,y1=box
    size=(x1-x0,y1-y0)
    photographic=np.asarray(crop_surface(photo,size,{'wood':4,'receiver':7,'steel':11,'magazine':17,
                                                     'skin':23,'cuff':29}[kind],rotate=kind=='wood'),
                           dtype=np.float32)
    painted=np.asarray(base.crop(box),dtype=np.float32)
    # Preserve the measured photographic grain/irregularities rather than
    # just sprinkling random pixels over the previous flat palette.
    mean=photographic.reshape(-1,3).mean(0)
    centered=photographic-mean
    if kind=='wood':
        baseline=np.array([143,80,43],dtype=np.float32)
        detail=.82*centered
        outline=.22*painted+.78*baseline
    elif kind in ('receiver','magazine','steel'):
        baseline={'receiver':[67,77,79],'magazine':[51,60,65],'steel':[102,112,118]}[kind]
        detail=.60*centered.mean(2,keepdims=True)
        outline=.22*painted+.78*np.array(baseline,dtype=np.float32)
    elif kind=='skin':
        # Fine real-photo leather pores are used only as a low-strength
        # microdetail source, recolored to skin; not a photographic hand.
        baseline=np.array([186,130,102],dtype=np.float32)
        detail=.24*centered.mean(2,keepdims=True)
        outline=.55*painted+.45*baseline
    else:
        baseline=np.array([49,48,50],dtype=np.float32)
        detail=.56*centered.mean(2,keepdims=True)
        outline=.37*painted+.63*baseline
    shaded=np.uint8(np.clip(outline+detail,0,255))
    canvas.paste(Image.fromarray(shaded,'RGB'),(x0,y0))

def make_rifle_atlas():
    atlas=procedural_rifle()
    photo=photo_library()
    if photo:
        original=atlas.copy()
        for kind,box in TILES.items():
            source='wood' if kind=='wood' else 'metal'
            replace_region(atlas,original,photo[source],box,kind)
    return atlas

def make_hand_atlas():
    atlas=procedural_hands()
    photos=photo_library()
    if photos:
        original=atlas.copy()
        for kind,box in HAND_TILES.items():
            replace_region(atlas,original,photos['leather'],box,kind)
    return atlas

def hand_uv(vertices,normals,joints,weights,names):
    """Hand-local UV projection allocating separate left/right skin halves.

    Previous global bounding box put nearly all pixels on the same few texels.
    Grouping by +/- Z preserves resolution independently on the two hands.
    """
    if len(vertices)%3:raise ValueError('hand triangle count is not divisible by 3')
    if len(vertices)==0:return np.empty((0,2),dtype=np.float64)
    out=np.zeros((len(vertices),2),dtype=np.float64)
    side_by_tri=np.array([0 if vertices[k:k+3,2].mean()<0 else 1
                         for k in range(0,len(vertices),3)])
    side_by_vertex=np.repeat(side_by_tri,3)
    bounds={}
    for side in (0,1):
        selected=vertices[side_by_vertex==side]
        if len(selected):
            low=selected[:,[0,1]].min(0); high=selected[:,[0,1]].max(0)
            bounds[side]=(low,np.maximum(high-low,.12))
    if not bounds: raise ValueError('no hand vertices')
    for start in range(0,len(vertices),3):
        tri=vertices[start:start+3]
        joint=int(joints[start,np.argmax(weights[start])])
        name=names[joint] if joint<len(names) else ''
        # Wrist cuffs stay dark; fingers and palms never borrow the cuff tile.
        is_cuff='wrist' in name or 'sleeve' in name or 'glove' in name
        kind='cuff' if is_cuff else 'skin'
        side=side_by_tri[start//3]
        low,span=bounds[side]
        uv=np.clip((tri[:,[0,1]]-low)/span,0,1)
        uv[:,1]=1-uv[:,1]
        x0,y0,x1,y1=HAND_TILES[kind]
        if kind=='skin':
            # Half the atlas per hand gives stable seams even when mirrored.
            half=(x1-x0)//2
            x0+=side*half
            x1=x0+half
        pad=5
        out[start:start+3]=(np.array([x0+pad+.5,y0+pad+.5])+
                    uv*np.array([x1-x0-2*pad-1,y1-y0-2*pad-1]))/SIZE
    return out
