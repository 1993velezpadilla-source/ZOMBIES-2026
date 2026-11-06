"""Verify embedded texture use, UV orientation and rig/geometry preservation."""
from pathlib import Path
import tempfile
import unittest
import numpy as np
from PIL import Image
from voxelize import pack_new, read_glb, read_accessor, write_glb
from texture_atlas import apply_texture, embedded_surface, make_atlas, TILES
from render_pose_sequence import PoseScene


class TextureTests(unittest.TestCase):
    def test_native_512_atlas_has_distinct_fine_material_detail(self):
        image = make_atlas()
        self.assertEqual(image.size, (512, 512))
        for tile in TILES.values():
            pixels = np.asarray(image.crop(tile))
            self.assertGreater(len(np.unique(pixels.reshape(-1, 3), axis=0)), 8)
            self.assertGreater(float(np.abs(np.diff(pixels.astype(float), axis=0)).mean()), .4)

    def test_embedding_preserves_rig_animation_and_position_accessors(self):
        doc = {'asset': {'version': '2.0'}, 'buffers': [{'byteLength': 0}],
               'bufferViews': [], 'accessors': [], 'materials': [{'name': 'wood'}],
               'nodes': [{'name': 'j_gun'}, {'mesh': 0, 'skin': 0}],
               'skins': [{'joints': [0]}], 'scenes': [{'nodes': [0, 1]}], 'scene': 0}
        raw = bytearray()
        attrs = {
            'POSITION': pack_new(doc, raw, [(0,0,0),(2,0,0),(2,2,0),(0,2,0)], 'VEC3'),
            'NORMAL': pack_new(doc, raw, [(0,0,1)]*4, 'VEC3'),
            'COLOR_0': pack_new(doc, raw, [(.6,.3,.15,1)]*4, 'VEC4'),
            'TEXCOORD_0': pack_new(doc, raw, [(0,0),(1,0),(1,1),(0,1)], 'VEC2'),
            'JOINTS_0': pack_new(doc, raw, [(0,0,0,0)]*4, 'VEC4', 5123),
            'WEIGHTS_0': pack_new(doc, raw, [(1,0,0,0)]*4, 'VEC4')}
        indices = pack_new(doc, raw, [(i,) for i in (0,1,2,0,2,3)], 'SCALAR', 5125)
        doc['meshes'] = [{'primitives': [{'attributes': attrs, 'indices': indices, 'material': 0}]}]
        time = pack_new(doc, raw, [(0,), (1,)], 'SCALAR')
        move = pack_new(doc, raw, [(0,0,0), (0,0,3)], 'VEC3')
        doc['animations'] = [{'name': 'move', 'samplers': [{'input': time, 'output': move}],
                              'channels': [{'sampler': 0, 'target': {'node': 0, 'path': 'translation'}}]}]
        with tempfile.TemporaryDirectory() as folder:
            old = Path(folder)/'old.glb'; new = Path(folder)/'new.glb'
            write_glb(old, doc, raw)
            report = apply_texture(old, new)
            before, old_raw = read_glb(old); after, new_raw = read_glb(new)
            for key in ('nodes', 'skins', 'animations'):
                self.assertEqual(before[key], after[key])
            self.assertEqual(new_raw[:len(old_raw)], old_raw)
            a = PoseScene(old); b = PoseScene(new)
            for t in (0., .5, 1.):
                np.testing.assert_array_equal(a.poses('move', t)[1], b.poses('move', t)[1])
            primitive = after['meshes'][0]['primitives'][0]
            uv = np.asarray(read_accessor(after, new_raw, primitive['attributes']['TEXCOORD_0']))
            self.assertTrue(np.all((uv >= 0) & (uv <= 1)))
            self.assertNotIn('COLOR_0', primitive['attributes'])
            self.assertEqual(embedded_surface(after, new_raw, primitive)['image'].size, (512,512))
            self.assertEqual(report['animations'], 1)
            self.assertEqual(report['triangles'], 2)

    def test_gpu_samples_image_with_gltf_top_left_uv_origin(self):
        from depth_preview import DepthPreview
        image = Image.fromarray(np.array([[[255,0,0],[0,255,0]],
                                         [[0,0,255],[255,255,0]]], dtype='u1'))
        xyz = np.array([(2,-.7,-.7),(2,-.7,.7),(2,.7,.7),(2,.7,-.7)])
        geometry = [(xyz, np.array([0,1,2,0,2,3]), np.ones((4,3)))]
        renderer = DepthPreview()
        try:
            renderer.set_surfaces([{'uv': np.array([(0,1),(1,1),(1,0),(0,0)]),
                                    'image': image, 'key': 'orientation-test'}])
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder)/'sample.png'
                report = renderer.render(geometry, np.zeros(3), 1, 'texture test', path,
                                         forward_override=[1,0,0])
                with Image.open(path) as im:
                    pixels = np.asarray(im)
                for y, x, channel in ((160,380,0),(160,720,1),(510,380,2)):
                    self.assertGreater(int(pixels[y,x,channel]), 180)
                    self.assertLess(int(pixels[y,x,(channel+1)%3]), 20)
                self.assertEqual(report['textured_primitives'], 1)
                self.assertEqual(report['texture_sizes'], [[2,2]])
        finally:
            renderer.close()


if __name__ == '__main__':
    unittest.main()
