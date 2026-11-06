"""Original, independently painted 512px AK47 and hand texture atlases.

Not copied from COD4 or a third-party mod. Baked edge light, metal wear and
walnut grain work on Luanti's standard GLB material shader (no PBR claim).
UV islands are named material regions, with a separate skin/cuff atlas.
"""
from __future__ import annotations
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
import sys
BLOCK=Path(__file__).resolve().parents[1]/'iw3_blockstyle'
sys.path.insert(0,str(BLOCK))
from texture_atlas import TILES, SIZE, PADDING

HAND_TILES={'skin':(0,0,512,380),'cuff':(0,380,512,512)}

def _tile(kind, width, height, rng):
    y,x=np.mgrid[:height,:width]
    grain=rng.normal(0,1.0,(height,width))
    norm_y=(y-height/2)/height
    if kind=='wood':
        band=np.sin(y*.20+3.1*np.sin(x*.021)+1.9*np.sin(x*.064))
        fine=np.sin(y*.73+2*np.sin(x*.038))
        knots=np.cos((x-width*.55)**2*.0008+(y-height*.3)**2*.003)
        light=11*band+3.7*fine+2.1*knots+grain*2.1
        base=np.array([146.,83.,41.]); shade=light[...,None]*np.array([1.,.72,.45])
        shade+=(1-abs(norm_y)[...,None])*np.array([11.,6.,1.])
    elif kind=='receiver':
        brush=2.4*np.cos(y*.62)+1.5*np.sin(x*.15)
        light=brush+grain*1.8+7*np.maximum(0,1-4*abs(norm_y))
        base=np.array([65.,75.,77.]); shade=light[...,None]*np.array([1.0,1.,.9])
    elif kind=='steel':
        light=6*np.sin(y*.093)+2.1*np.cos(x*.16)+grain*2.0
        base=np.array([94.,103.,110.]);shade=light[...,None]
    elif kind=='magazine':
        base=np.array([55.,62.,66.]);shade=(grain*2+4*np.sin(x*.012))[...,None]*np.ones(3)
    elif kind=='skin':
        # Warm adult skin instead of the previous 16x1 near-black palette.
        pores=grain*1.35+1.1*np.sin(x*.18+y*.15)
        base=np.array([179.,128.,96.])
        gradient=(5-12*abs(norm_y))[...,None]*np.array([1.,.65,.45])
        shade=pores[...,None]+gradient
    else:  # dark fabric cuff at wrists only
        base=np.array([50.,48.,47.])
        fibers=4*np.sin((x+y)*.60)+grain*2
        shade=fibers[...,None]*np.array([.9,.9,1.0])
    out=np.uint8(np.clip(base+shade,0,255))
    return Image.fromarray(out,'RGB')

def _draw_details(kind,tile,rng):
    dr=ImageDraw.Draw(tile,'RGBA');w,h=tile.size
    if kind in ('receiver','steel','magazine'):
        for _ in range(65 if kind=='receiver' else 24):
            x=int(rng.integers(7,w-7)); y=int(rng.integers(5,h-5))
            ln=int(rng.integers(2,17))
            dr.line((x,y,x+ln,y),fill=(177,191,197,int(rng.integers(24,72))),width=1)
        if kind=='magazine':
            for xx in range(24,w,32):
                dr.line((xx,9,xx+7,h-9),fill=(19,24,28,80),width=4)
                dr.line((xx+4,9,xx+11,h-9),fill=(194,205,207,52),width=1)
    if kind=='wood':
        for _ in range(16):
            cx=int(rng.integers(0,w));cy=int(rng.integers(0,h))
            dr.line((cx,cy,cx+int(rng.integers(7,35)),cy+int(rng.integers(-5,6))),
                    fill=(59,24,11,40),width=1)
        for ky in (69,172):
            dr.arc((60,ky-13,220,ky+13),20,160,fill=(60,32,17,80),width=2)
    if kind=='skin':
        for _ in range(95):
            xx=int(rng.integers(12,w-12)); yy=int(rng.integers(12,h-12))
            dr.line((xx,yy,xx+int(rng.integers(1,6)),yy+1),fill=(97,57,47,18),width=1)
    if kind=='cuff':
        for xx in range(0,w,9):
            dr.line((xx,0,xx+int(h*.17),h),fill=(112,105,97,34),width=1)
    return tile

def _fill_atlas(tiles):
    rng=np.random.default_rng(470516)
    atlas=Image.new('RGB',(SIZE,SIZE))
    for kind,(left,top,right,bottom) in tiles.items():
        width,height=right-left,bottom-top
        tile=_draw_details(kind,_tile(kind,width,height,rng),rng)
        # Texture sampling is clamped and islands have explicit extruded edges.
        p=PADDING
        tile.paste(tile.crop((p,p,width-p,p+1)).resize((width-2*p,p)),(p,0))
        tile.paste(tile.crop((p,height-p-1,width-p,height-p)).resize((width-2*p,p)),(p,height-p))
        tile.paste(tile.crop((p,0,p+1,height)).resize((p,height)),(0,0))
        tile.paste(tile.crop((width-p-1,0,width-p,height)).resize((p,height)),(width-p,0))
        atlas.paste(tile,(left,top))
    return atlas

def make_rifle_atlas():
    return _fill_atlas(TILES)

def make_hand_atlas():
    return _fill_atlas(HAND_TILES)

def hand_uv(vertices,normals,joints,weights,names):
    """Per-triangle projection of original hand polygons into SKIN / CUFF UVs.

    The previous exporter gave *all 2932 hand triangles* one dark texel.
    Triangles are already expanded by the skinned converter: no skin loss.
    """
    if len(vertices)%3:raise ValueError('hand vertex triangle count')
    result=np.zeros((len(vertices),2),dtype=float)
    lower=vertices.min(0);upper=vertices.max(0)
    span=np.maximum(upper-lower,.25)
    for n in range(0,len(vertices),3):
        verts=vertices[n:n+3]
        dominant=int(joints[n,np.argmax(weights[n])])
        name=names[dominant] if dominant<len(names) else ''
        # Keep a modest dark cuff on wrists; palms and fingers have skin tone.
        kind='cuff' if 'wrist' in name and verts[:,0].mean()<15.15 else 'skin'
        tile=HAND_TILES[kind]
        # The model places two mirrored hands at +/- Z. Normalize absolute Z
        # separately rather than spreading small details across both hands.
        vals=np.column_stack((verts[:,0],verts[:,1]))
        vals[:,0]=(vals[:,0]-lower[0])/span[0]
        vals[:,1]=1-(vals[:,1]-lower[1])/span[1]
        left,top,right,bottom=tile
        result[n:n+3]=(np.array([left+PADDING+.5,top+PADDING+.5])+
             np.clip(vals,0,1)*np.array([right-left-2*PADDING-1,bottom-top-2*PADDING-1]))/SIZE
    return result
