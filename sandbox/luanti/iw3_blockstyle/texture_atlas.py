"""Original 512px wood/metal atlas, UV-mapped onto the existing skinned shell.

No source-game texture is used. Positions, topology, bones and animation bytes
are retained; only UVs and material/color bindings change. Private GLB outputs
must not be committed or uploaded as public Actions artifacts.
"""
from __future__ import annotations

from collections import Counter
from io import BytesIO
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw
from voxelize import pack_new, read_accessor, read_glb, write_glb

SIZE = 512
PADDING = 4
TILES = {
    'receiver': (0, 0, 384, 256),
    'steel': (384, 0, 512, 256),
    'wood': (0, 256, 256, 512),
    'magazine': (256, 256, 512, 512),
}


def make_atlas():
    """Paint at native resolution; seeded fine grain is never upscaled."""
    atlas = Image.new('RGB', (SIZE, SIZE))
    rng = np.random.default_rng(470512)
    for kind, box in TILES.items():
        width, height = box[2]-box[0], box[3]-box[1]
        y, x = np.mgrid[:height, :width]
        if kind == 'wood':
            grain = np.sin(y*.41 + 2.8*np.sin(x*.022) + .5*np.sin(x*.079))
            fine = np.sin(y*1.59 + 1.5*np.sin(x*.031))
            value = 7*grain + 2*fine + rng.normal(0, 1.4, x.shape)
            base = np.array([151., 81., 43.])
            rgb = base + value[..., None]*[1., .66, .39]
        elif kind == 'magazine':
            value = rng.normal(0, 1., x.shape) + 1.2*np.sin(y*.7)
            rgb = np.array([65., 77., 85.]) + value[..., None]
        elif kind == 'steel':
            value = 2.2*np.sin(y*.17) + rng.normal(0, .8, x.shape)
            rgb = np.array([98., 113., 123.]) + value[..., None]
        else:
            value = 1.7*np.sin(y*.47) + rng.normal(0, .8, x.shape)
            rgb = np.array([64., 77., 87.]) + value[..., None]
        tile = Image.fromarray(np.clip(rgb, 0, 255).astype('u1'))
        draw = ImageDraw.Draw(tile)
        if kind == 'wood':
            for cy, cx in ((69, 191), (183, 57)):
                for radius in (4, 8, 14, 22):
                    draw.ellipse((cx-radius*2, cy-radius*.4,
                                  cx+radius*2, cy+radius*.4),
                                 outline=(122+radius, 64+radius//2, 34+radius//3))
        elif kind == 'magazine':
            # Long pressed-steel grooves, following a mild curve.
            for u in (43, 79, 115, 151, 187, 223):
                path = [(u+int(8*np.sin(v/height*np.pi)), v)
                        for v in range(18, height-18)]
                draw.line(path, fill=(43, 53, 61), width=5)
                draw.line([(px-3, py) for px, py in path],
                          fill=(94, 107, 115), width=1)
            draw.line((12, 12, width-12, 12), fill=(102, 113, 118), width=2)
            draw.line((12, height-12, width-12, height-12), fill=(40, 50, 58), width=3)
        elif kind == 'receiver':
            for v in (40, 72, 193, 219):
                draw.line((12, v, width-12, v), fill=(45, 57, 68), width=2)
                draw.line((12, v+2, width-12, v+2), fill=(84, 97, 106), width=1)
            for u, v in ((48, 99), (149, 99), (303, 165)):
                draw.ellipse((u-3, v-3, u+3, v+3), fill=(40, 51, 60),
                             outline=(100, 111, 120))
        else:
            for v in (30, 62, 190, 223):
                draw.line((8, v, width-8, v), fill=(77, 91, 103), width=1)
        # Extruded borders isolate atlas islands under linear filtering.
        p = PADDING
        tile.paste(tile.crop((p, p, width-p, p+1)).resize((width-2*p, p)), (p, 0))
        tile.paste(tile.crop((p, height-p-1, width-p, height-p)).resize((width-2*p, p)), (p, height-p))
        tile.paste(tile.crop((p, 0, p+1, height)).resize((p, height)), (0, 0))
        tile.paste(tile.crop((width-p-1, 0, width-p, height)).resize((p, height)), (width-p, 0))
        atlas.paste(tile, box[:2])
    return atlas


def classify_faces(xyz, colors, joint_names, joints, material, lo, hi):
    """Every emitted quad gets one material island, including moving parts."""
    centers = xyz.reshape(-1, 4, 3).mean(axis=1)
    tint = colors.reshape(-1, 4, colors.shape[1]).mean(axis=1)
    bone = joints[::4, 0]
    f = (centers[:, 0]-lo[0])/max(1e-9, hi[0]-lo[0])
    regions = np.full(len(centers), 'receiver', dtype='U10')
    regions[(f > .76) | ('misc' in material)] = 'steel'
    regions[(f < .245) | ((tint[:, 0] > tint[:, 1]*1.45) &
                                   (tint[:, 0] > tint[:, 2]*1.9))] = 'wood'
    for j, name in enumerate(joint_names):
        mask = bone == j
        if 'clip' in name or 'mag' in name:
            regions[mask] = 'magazine'
        elif 'bolt' in name or 'trigger' in name:
            regions[mask] = 'steel'
    return np.repeat(regions, 4)


def apply_texture(source: Path, target: Path, png: Path | None = None):
    doc, old_binary = read_glb(source)
    raw = bytearray(old_binary)
    primitives = [p for m in doc['meshes'] for p in m['primitives']]
    if any('baseColorTexture' in m.get('pbrMetallicRoughness', {})
           for m in doc.get('materials', [])):
        raise ValueError('texture atlas expects the untextured voxel shell')
    all_xyz = [np.asarray(read_accessor(doc, raw, p['attributes']['POSITION']))
               for p in primitives]
    lo = np.vstack(all_xyz).min(0); hi = np.vstack(all_xyz).max(0)
    skin = doc['skins'][0]
    names = [doc['nodes'][j].get('name', '').lower() for j in skin['joints']]
    records = []
    for primitive, xyz in zip(primitives, all_xyz):
        attrs = primitive['attributes']
        if len(xyz) % 4:
            raise ValueError('atlas mapping requires the emitted four-vertex quads')
        normals = np.asarray(read_accessor(doc, raw, attrs['NORMAL']))
        colors = np.asarray(read_accessor(doc, raw, attrs['COLOR_0']))
        joints = np.asarray(read_accessor(doc, raw, attrs['JOINTS_0']), dtype=int)
        material = doc['materials'][primitive['material']].get('name', '').lower()
        regions = classify_faces(xyz, colors, names, joints, material, lo, hi)
        records.append((primitive, xyz, normals, regions))
    bounds = {}
    for kind in TILES:
        pieces = [xyz[regions == kind] for _, xyz, _, regions in records
                  if np.any(regions == kind)]
        if pieces:
            pts = np.vstack(pieces)
            bounds[kind] = (pts.min(0), np.maximum(pts.max(0)-pts.min(0), .1))
    counts = Counter()
    for primitive, xyz, normals, regions in records:
        uv = np.zeros((len(xyz), 2), dtype=float)
        dominant = np.argmax(np.abs(normals), axis=1)
        for kind, tile in TILES.items():
            for axis, axes in ((0, (2, 1)), (1, (0, 2)), (2, (0, 1))):
                mask = (regions == kind) & (dominant == axis)
                if not np.any(mask):
                    continue
                start, span = bounds[kind]
                xy = np.clip((xyz[mask][:, axes]-start[list(axes)])/span[list(axes)], 0, 1)
                # glTF UV origin is the top-left of the decoded image.
                xy[:, 1] = 1-xy[:, 1]
                left, top, right, bottom = tile
                uv[mask] = ([left+PADDING+.5, top+PADDING+.5] +
                            xy*[right-left-2*PADDING-1, bottom-top-2*PADDING-1])/SIZE
                counts[kind] += int(np.count_nonzero(mask)//4)
        primitive['attributes']['TEXCOORD_0'] = pack_new(doc, raw, uv.tolist(), 'VEC2', target=34962)
        # glTF multiplies base-color texture by COLOR_0; retaining the old dark
        # palette would tint the new material twice.
        primitive['attributes'].pop('COLOR_0')
    atlas = make_atlas()
    png_bytes = BytesIO(); atlas.save(png_bytes, format='PNG', optimize=True)
    encoded = png_bytes.getvalue()
    if png is not None:
        png.parent.mkdir(parents=True, exist_ok=True); png.write_bytes(encoded)
    while len(raw) % 4:
        raw.append(0)
    view_id = len(doc['bufferViews'])
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(raw), 'byteLength': len(encoded)})
    raw.extend(encoded)
    doc['images'] = [{'name': 'AK47_original_materials_512', 'bufferView': view_id,
                      'mimeType': 'image/png'}]
    doc['samplers'] = [{'magFilter': 9729, 'minFilter': 9729,
                        'wrapS': 33071, 'wrapT': 33071}]
    doc['textures'] = [{'sampler': 0, 'source': 0}]
    for material in doc['materials']:
        material['pbrMetallicRoughness'] = {'baseColorTexture': {'index': 0, 'texCoord': 0},
            'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 0., 'roughnessFactor': .8}
    target.parent.mkdir(parents=True, exist_ok=True)
    write_glb(target, doc, raw)
    return {'width': SIZE, 'height': SIZE, 'format': 'embedded PNG',
            'generated_at_native_resolution': True, 'source_game_texture_used': False,
            'uv_origin': 'glTF top-left', 'uv_mapping': 'rest-space planar per material and face axis',
            'edge_padding_pixels': PADDING, 'faces_per_region': dict(counts),
            'atlas_sha256': hashlib.sha256(encoded).hexdigest(),
            'triangles': sum(len(read_accessor(doc, raw, p['indices']))//3 for p in primitives),
            'animations': len(doc.get('animations', [])), 'private_binary_outputs': True}


def embedded_surface(doc, raw, primitive):
    """Decode the exact embedded GLB image/UVs for the depth renderer."""
    material = doc.get('materials', [{}])[primitive.get('material', 0)]
    texture = material.get('pbrMetallicRoughness', {}).get('baseColorTexture')
    if texture is None:
        return None
    if texture.get('texCoord', 0) != 0:
        raise ValueError('preview supports TEXCOORD_0 only')
    image = doc['images'][doc['textures'][texture['index']]['source']]
    if 'bufferView' not in image:
        raise ValueError('textured preview requires an embedded image')
    view = doc['bufferViews'][image['bufferView']]
    offset = view.get('byteOffset', 0)
    encoded = bytes(raw[offset:offset+view['byteLength']])
    with Image.open(BytesIO(encoded)) as im:
        im.load(); pixels = im.convert('RGB')
    uv = np.asarray(read_accessor(doc, raw, primitive['attributes']['TEXCOORD_0']), dtype='f4')
    return {'uv': uv, 'image': pixels, 'key': hashlib.sha256(encoded).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--png', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = apply_texture(args.input, args.output, args.png)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
