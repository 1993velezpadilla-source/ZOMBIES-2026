"""Full-resolution photographic AK texture bake, not a 512px label.

V4 technically shipped a 512x512 picture, but its front steel had just
128x256 texels; plus Luanti's generic model shader ignored all normals.
V5 uses 2048x2048 for the gun (512x1024 FRONT steel, 1024x1024 walnut
and magazine), a dedicated 1024x1024 hand map, and AK-only lit shaders.

UV island boundaries and topology remain identical as fractions, so the
existing source-derived weighted skeleton and XANIM are unaffected.
"""
from __future__ import annotations
import numpy as np
from PIL import Image

from material_v2 import make_rifle_atlas as old_rifle, make_hand_atlas as old_hands
from material_v2 import HAND_TILES as OLD_HAND_TILES
from material_v3 import photo_library,crop_surface
from texture_atlas import TILES as OLD_TILES

RIFLE_SIZE=2048
HAND_SIZE=1024
PADDING=12
TILES={k:tuple(x*(RIFLE_SIZE//512) for x in box) for k,box in OLD_TILES.items()}
HAND_TILES={k:tuple(x*(HAND_SIZE//512) for x in box) for k,box in OLD_HAND_TILES.items()}
SIZE=RIFLE_SIZE # used only for the rifle exporter UV scale


def _photo_tile(photo:Image.Image,shape,seed:int,rot:bool=False):
    w,h=shape
    return np.asarray(crop_surface(photo,(w,h),seed,rotate=rot),
                      dtype=np.float32)


def _bake(canvas:Image.Image,photographs:dict,kind:str,box,underlay:Image.Image):
    left,top,right,bottom=box
    width,height=right-left,bottom-top
    seed={'wood':4,'receiver':7,'steel':11,'magazine':17,
          'skin':23,'cuff':29}[kind]
    picture=photographs['wood' if kind=='wood' else
                        'leather' if kind in ('skin','cuff') else 'metal']
    photo=_photo_tile(picture,(width,height),seed,rot=kind=='wood')
    base=np.asarray(underlay.crop(box),dtype=np.float32)
    centered=photo-photo.mean(axis=(0,1),keepdims=True)
    y,x=np.mgrid[:height,:width]
    # No fake high-frequency noise is upscaled from a 512px palette: original
    # pinned 1K photographs are sampled at final output resolution.
    if kind=='wood':
        color=np.array([108,64,39],dtype=np.float32)
        detail=np.clip(.60*centered,-35,32)
        gradient=(1.0-np.abs(2*y/height-1))*4
        target=.23*base+.77*color+detail+gradient[...,None]
    elif kind in ('receiver','steel','magazine'):
        # Preserve rich black bluing but add fine wear, not the earlier large
        # bright-white patches. The same Rusty Metal 04 CC0 source remains.
        color=np.array({'receiver':[65,70,75],'steel':[81,86,90],
                        'magazine':[54,60,64]}[kind],dtype=np.float32)
        luminance=photo[:,:,0]*.2126+photo[:,:,1]*.7152+photo[:,:,2]*.0722
        fine=np.clip(.34*(luminance-luminance.mean()),-28,27)
        warm=np.maximum(0,photo[:,:,0]-(photo[:,:,1]+photo[:,:,2])*.5)
        rust=np.clip((warm-6)/32,0,1)*np.clip((175-luminance)/100,0,1)
        # Thin directional brushed-steel wear + softer highlights from source.
        brush=(np.sin(y*.17+x*.012)+np.sin(y*.037-x*.07))*1.1
        target=.11*base+.89*color+fine[...,None]+brush[...,None]
        target=target+rust[...,None]*np.array([14,5,-4],dtype=np.float32)
    elif kind=='skin':
        color=np.array([188,136,105],dtype=np.float32)
        pores=np.clip(.22*centered.mean(axis=2,keepdims=True),-10,10)
        target=.34*base+.66*color+pores
    else:
        color=np.array([42,42,45],dtype=np.float32)
        weave=np.clip(.35*centered.mean(axis=2,keepdims=True),-15,15)
        target=.25*base+.75*color+weave
    # Bounded gradient prevents the source's bright paint flecks becoming
    # a noisy orange/white patchwork on close-up iron sights.
    canvas.paste(Image.fromarray(np.uint8(np.clip(target,0,255)),'RGB'),(left,top))


def make_rifle_atlas()->Image.Image:
    base=old_rifle().resize((RIFLE_SIZE,RIFLE_SIZE),Image.Resampling.LANCZOS)
    atlas=base.copy()
    photos=photo_library()
    if not photos:return atlas
    for kind,box in TILES.items():
        _bake(atlas,photos,kind,box,base)
    return atlas


def make_hand_atlas()->Image.Image:
    base=old_hands().resize((HAND_SIZE,HAND_SIZE),Image.Resampling.LANCZOS)
    atlas=base.copy()
    photos=photo_library()
    if photos:
        for kind,box in HAND_TILES.items():
            _bake(atlas,photos,kind,box,base)
    # Dark sleeve -> warm skin transition runs continuously within BOTH hand
    # islands, independent of every triangle's dominant bone weight.
    pixels=np.array(atlas,dtype=np.float32)
    top,bottom=HAND_TILES['skin'][1],HAND_TILES['skin'][3]
    half=HAND_SIZE//2
    for side in range(2):
        l=half*side
        x=np.arange(half,dtype=np.float32)/half
        blend=np.clip((x-.15)/.25,0.,1.)
        blend=blend*blend*(3.-2.*blend)
        pale=pixels[top:bottom,l:l+half]
        sleeve=np.array([40.,41.,44.],dtype=np.float32)
        pixels[top:bottom,l:l+half]=blend[None,:,None]*pale+(1-blend[None,:,None])*sleeve
    return Image.fromarray(np.uint8(np.clip(pixels,0,255)),'RGB')


def hand_uv(vertices,normals,joints,weights,names):
    """Two separate continuous hand UV islands, using 1024 actual pixels."""
    vertices=np.asarray(vertices,dtype=np.float64)
    if len(vertices)%3:raise ValueError('hands: vertices must be triangles')
    if len(vertices)==0:return np.empty((0,2),dtype=np.float64)
    out=np.zeros((len(vertices),2),dtype=np.float64)
    side_by_tri=np.array([0 if vertices[k:k+3,2].mean()<0 else 1
                         for k in range(0,len(vertices),3)])
    sides=np.repeat(side_by_tri,3)
    ranges={}
    for side in (0,1):
        a=vertices[sides==side][:,[0,1]]
        if len(a):ranges[side]=(a.min(0),np.maximum(a.max(0)-a.min(0),.12))
    for start in range(0,len(vertices),3):
        side=side_by_tri[start//3]
        low,span=ranges[side]
        xy=np.clip((vertices[start:start+3][:,[0,1]]-low)/span,0,1)
        xy[:,1]=1-xy[:,1]
        x0,y0,x1,y1=HAND_TILES['skin']
        segment=(x1-x0)//2
        x0=x0+side*segment
        x1=x0+segment
        out[start:start+3]=(np.array([x0+PADDING+.5,y0+PADDING+.5])+
           xy*np.array([x1-x0-2*PADDING-1,
                        y1-y0-2*PADDING-1]))/HAND_SIZE
    return out
