"""Prevent returning 512px subdivided atlases or normal-free model shaders."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np
from PIL import Image

import material_v5
from material_v5 import TILES, RIFLE_SIZE, HAND_SIZE, hand_uv
from patch_lit_shader import patch as patch_shader, RIFLE_FRAGMENT, SKIN_FRAGMENT


class HighResArtworkTests(unittest.TestCase):
    def test_real_texture_space_per_material(self):
        self.assertEqual(RIFLE_SIZE,2048)
        self.assertEqual(HAND_SIZE,1024)
        self.assertGreaterEqual(TILES['receiver'][2]-TILES['receiver'][0],1400)
        self.assertGreaterEqual(TILES['steel'][2]-TILES['steel'][0],500)
        self.assertGreaterEqual(TILES['wood'][2]-TILES['wood'][0],1024)
        self.assertGreaterEqual(TILES['magazine'][2]-TILES['magazine'][0],1024)

    def test_2k_photos_are_baked_at_native_output_resolution(self):
        rng=np.random.default_rng(4706)
        photos={kind:Image.fromarray(rng.integers(20,225,(1024,1024,3),dtype=np.uint8))
                for kind in ('metal','wood','leather')}
        with patch('material_v5.photo_library',return_value=photos):
            rifle=material_v5.make_rifle_atlas()
            hands=material_v5.make_hand_atlas()
        self.assertEqual(rifle.size,(2048,2048))
        self.assertEqual(hands.size,(1024,1024))
        r=np.asarray(rifle)
        h=np.asarray(hands)
        self.assertGreater(float(r[100:800,100:800].std()),4.5)
        self.assertGreater(float(h[60:700,100:900].std()),5.5)
        self.assertLess(float(np.percentile(r[20:900,20:1450],99)),155,
                        'photo white paint-chips cannot cover black metal')

    def test_hands_use_consistent_contiguous_skin_islands(self):
        pos=np.array([[1,0,-3],[2,0,-3],[1,1,-3],
                      [1.1,0,-3],[2,0,-3],[1,1,-3],
                      [1,0,3],[2,0,3],[1,1,3]],float)
        joints=np.zeros((9,4),int); joints[3:6,0]=1
        weights=np.tile([1.,0.,0.,0.],(9,1))
        uv=hand_uv(pos,None,joints,weights,['j_hand','j_wrist'])
        self.assertEqual(uv.shape,(9,2))
        self.assertTrue(np.all((uv>=0.)&(uv<=1.)))
        np.testing.assert_allclose(uv[:3],uv[3:6],atol=.00001)


class LitShaderTests(unittest.TestCase):
    def test_ak_only_shader_keeps_upstream_vertex_skinning(self):
        with TemporaryDirectory() as path:
            p=Path(path)/'client/shaders/fs_model_shader'
            p.mkdir(parents=True)
            vertex='TEST gl_Position = mWorldViewProj * skinPos;\n'
            frag='// TODO use vNormal for directional lighting, c.f. drawItemStack()\n'
            (p/'opengl_vertex.glsl').write_text(vertex)
            (p/'opengl_fragment.glsl').write_text(frag)
            patch_shader(Path(path))
            for name in ('ak47_lit_model_shader','ak47_lit_skin_shader'):
                file=p.parent/name
                self.assertEqual((file/'opengl_vertex.glsl').read_text(),vertex)
                self.assertIn('normalize(vNormal)',(file/'opengl_fragment.glsl').read_text())
            self.assertEqual((p/'opengl_fragment.glsl').read_text(),frag,
                             'never modify generic model shaders')
        self.assertIn('gl_FragColor',RIFLE_FRAGMENT)
        self.assertIn('gl_FragColor',SKIN_FRAGMENT)


if __name__=='__main__':
    unittest.main()
