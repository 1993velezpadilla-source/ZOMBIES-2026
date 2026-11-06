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
        # Deep walnut: the previous saturated orange made furniture plastic.
        # Preserve photo grain and weathered pores with directional dark fibers.
        baseline=np.array([103,60,37],dtype=np.float32)
        detail=.43*(photographic-photographic.mean(axis=(0,1),keepdims=True))
        outline=.17*painted+.83*baseline
        detail=np.clip(detail,-25,22)
    elif kind in ('receiver','magazine','steel'):
        # Keep the photograph from Rusty Metal 04 as real weathering, NOT the
        # base coat. Previously 90% photo chroma painted the whole rifle white.
        # This is black blued steel first, with restrained rust on dark areas.
        baseline=np.array({'receiver':[53,60,64],
                           'magazine':[43,49,52],
                           'steel':[69,75,79]}[kind],dtype=np.float32)
        luma=(.2126*photographic[:,:,0]+.7152*photographic[:,:,1]
              +.0722*photographic[:,:,2])
        coarse=np.clip((luma-np.mean(luma))*.20,-13,13)[...,None]
        # Ignore very bright specks: those were the white paint chips.
        # Colorize genuinely warmer rust pixels only, with bounded strength.
        red_excess=np.maximum(0,photographic[:,:,0] -
                              .5*(photographic[:,:,1]+photographic[:,:,2]))
        rust=np.clip((red_excess-7)/48,0,1)*np.clip((190-luma)/90,0,1)
        rust=rust[...,None]
        outline=.15*painted+.85*baseline
        detail=np.broadcast_to(coarse,photographic.shape).copy()
        detail+=rust*np.array([22.,6.,-7.],dtype=np.float32)
    elif kind=='skin':
        # Photo leather is *microtexture only*, not a replacement for skin.
        # Avoid coarse dark spots projected onto every finger.
        baseline=np.array([177,125,99],dtype=np.float32)
        detail=np.clip(.13*centered.mean(2,keepdims=True),-8,8)
        outline=.40*painted+.60*baseline
    else:
        baseline=np.array([40,43,47],dtype=np.float32)
        detail=np.clip(.35*centered.mean(2,keepdims=True),-16,16)
        outline=.36*painted+.64*baseline
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
    # Build continuous sleeve-to-skin gradient INSIDE the two skin UV
    # islands. Do not label arbitrary neighboring triangles as glove/skin:
    # that caused the large black sawtooth edges seen during reload.
    pixels=np.asarray(atlas,dtype=np.float32).copy()
    # x within each half maps wrist -> palm. Keep most of the fingers skin.
    for side in (0,1):
        left=side*(SIZE//2)
        right=(side+1)*(SIZE//2)
        width=right-left
        x=np.arange(width,dtype=np.float32)
        # 0..0.18 dark cuff, smooth transition from 0.18..0.37
        t=np.clip((x/width-.16)/.22,0,1)
        t=t*t*(3-2*t)
        blend=t[None,:,None]
        base=pixels[0:HAND_TILES['skin'][3],left:right,:]
        charcoal=np.array([41,42,43],dtype=np.float32)
        charcoal=charcoal[None,None,:]+(base-base.mean(axis=(0,1),keepdims=True))*.12
        pixels[0:HAND_TILES['skin'][3],left:right,:]=blend*base+(1-blend)*charcoal
    return Image.fromarray(np.uint8(np.clip(pixels,0,255)),'RGB')

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
        # A continuous UV island per hand; cuff/sleeve shading is painted as
        # a smooth gradient on the atlas instead of triangle-by-triangle tags.
        # 3D hands and finger weights are left completely unchanged.
        kind='skin'
        side=side_by_tri[start//3]
        low,span=bounds[side]
        uv=np.clip((tri[:,[0,1]]-low)/span,0,1)
        uv[:,1]=1-uv[:,1]
        x0,y0,x1,y1=HAND_TILES[kind]
        # Each hand gets half the same contiguous skin/sleeve region.
        half=(x1-x0)//2
        x0+=side*half
        x1=x0+half
        pad=5
        out[start:start+3]=(np.array([x0+pad+.5,y0+pad+.5])+
                    uv*np.array([x1-x0-2*pad-1,y1-y0-2*pad-1]))/SIZE
    return out
