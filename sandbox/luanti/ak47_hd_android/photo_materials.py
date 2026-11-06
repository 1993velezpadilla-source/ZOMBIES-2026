"""Fetch verified CC0 photographic material maps for private Luanti AK47 test.

Source: Poly Haven (https://polyhaven.com/license), all assets CC0 1.0.
These are textures for our *own* material layout, NOT Call of Duty textures.
Download exact, pinned 1K albedos; never trust an unverified remote response.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request,urlopen

from PIL import Image

SOURCES={
    'wood':{
      'asset':'wood_table_001','channel':'Diffuse',
      'url':'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/wood_table_001/wood_table_001_diff_1k.jpg',
      'md5':'56652a7339b16a76afad20d3585f66ea',
      'bytes':215573
    },
    'metal':{
      'asset':'metal_plate','channel':'Diffuse',
      'url':'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/metal_plate/metal_plate_diff_1k.jpg',
      'md5':'bd9daf4c04046ca392a38b8df955ed26',
      'bytes':692234
    },
    'leather':{
      'asset':'leather_red_02','channel':'coll1',
      'url':'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/leather_red_02/leather_red_02_coll1_1k.jpg',
      'md5':'a91110dd3cea1bfb5d8f34b5c3c6536d',
      'bytes':1002834
    }
}

def verify_image_bytes(blob:bytes,name:str):
    spec=SOURCES[name]
    if len(blob)!=spec['bytes'] or hashlib.md5(blob).hexdigest()!=spec['md5']:
        raise ValueError(f'{name}: downloaded photograph does not match pinned CC0 asset')
    with Image.open(io.BytesIO(blob)) as image:
        image.verify()
    with Image.open(io.BytesIO(blob)) as image:
        if min(image.size)<1000:
            raise ValueError(f'{name}: source image too small {image.size}')
        return image.size

def prepare(out:Path):
    out.mkdir(parents=True,exist_ok=True)
    report={}
    for name,spec in SOURCES.items():
        dest=out/f'{name}.jpg'
        if dest.exists():
            blob=dest.read_bytes()
        else:
            req=Request(spec['url'],headers={'User-Agent':'AK47-Luanti-CC0-Material-Research/1.0'})
            with urlopen(req,timeout=45) as response:
                blob=response.read(8_000_000)
            dest.write_bytes(blob)
        dimensions=verify_image_bytes(blob,name)
        report[name]={'source':spec['asset'],'color_map':spec['channel'],
                      'dimensions':dimensions,'bytes':len(blob),'verified_md5':spec['md5']}
    (out/'sources.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('CC0_REAL_PHOTOGRAPH_TEXTURES_VERIFIED '+json.dumps(report,sort_keys=True))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    prepare(parser.parse_args().output)
