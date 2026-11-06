"""Two independent reload timelines and photo-based materials regression."""
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from make_reload_audio import render_sequence, TIMELINES
from material_v3 import make_rifle_atlas, make_hand_atlas, hand_uv
from material_v2 import make_rifle_atlas as original_rifle, make_hand_atlas as original_hands
from photo_materials import SOURCES
from export_viewmodel import source_triangle_uv


class NaturalReloadTests(unittest.TestCase):
    def test_magazine_sound_is_not_pitch_shifted_and_empty_has_late_bolt(self):
        rate=8000
        mag=np.zeros((16000,1),np.float32)
        mag[32:80,0]=0.24
        bolt=np.zeros((3200,1),np.float32)
        bolt[:60,0]=0.42
        normal,n=render_sequence(mag,bolt,rate,'normal')
        empty,e=render_sequence(mag,bolt,rate,'empty')
        self.assertEqual(len(normal),round((83/30)*rate))
        self.assertEqual(len(empty),round((106/30)*rate))
        self.assertEqual(n['extra_bolt_samples'],0)
        self.assertGreater(e['extra_bolt_samples'],0)
        for clip,entry in ((normal,n),(empty,e)):
            start=entry['magazine_offset_samples']
            np.testing.assert_allclose(clip[start:start+len(mag)],mag*.93,rtol=0,atol=1e-6)
            self.assertFalse(entry['time_stretch_applied'])
            self.assertTrue(entry['pitch_unchanged'])
        self.assertGreater(float(empty[round(TIMELINES['empty']['bolt_onset_s']*rate),0]),.33)
        self.assertAlmostEqual(float(normal[-1,0]),0)

    def test_invalid_audio_input_is_rejected(self):
        with self.assertRaises(ValueError):
            render_sequence(np.zeros((10,1)),np.zeros((10,2)),8000,'empty')


class PhotoMaterialsTests(unittest.TestCase):
    def test_pinned_rusty_metal_04_asset(self):
        self.assertEqual(SOURCES['metal']['asset'],'rusty_metal_04')
        self.assertEqual(SOURCES['metal']['md5'],'91832efd8e5896387e2af18a5b49b895')
        self.assertEqual(SOURCES['metal']['bytes'],938338)

    def test_rust_photo_bakes_as_subtle_wear_not_white_paint(self):
        # Simulate the severe brown/blue/white contrast of the source image.
        # Receiver should remain blued steel, not an all-over bright mosaic.
        photo=np.empty((1024,1024,3),dtype=np.uint8)
        photo[:350,:]=[174,70,42]
        photo[350:700,:]=[45,87,127]
        photo[700:,:]=[241,240,235]
        wood=np.zeros((1024,1024,3),dtype=np.uint8)+np.array([140,80,30],dtype=np.uint8)
        fake={'wood':Image.fromarray(wood),'metal':Image.fromarray(photo),
              'leather':Image.fromarray(wood)}
        with patch('material_v3.photo_library',return_value=fake):
            atlas=np.asarray(make_rifle_atlas(),dtype=np.float32)
        receiver=atlas[10:245,10:370]
        self.assertLess(float(np.percentile(receiver,99)),140,
                        'white rust flakes have taken over the whole metal')
        self.assertLess(float(np.median(receiver)),85)
        chroma=receiver[:,:,0]-receiver[:,:,2]
        self.assertGreater(float(np.ptp(chroma)),6,
                           'photo wear should be present, not purely flat gray')

    def test_hand_cuff_gradient_does_not_change_material_per_triangle(self):
        rng=np.random.default_rng(1280)
        fake={k:Image.fromarray(rng.integers(100,150,(1024,1024,3),dtype=np.uint8))
              for k in ('wood','metal','leather')}
        with patch('material_v3.photo_library',return_value=fake):
            tex=np.asarray(make_hand_atlas(),dtype=float)
        # Left-hand skin atlas X=0..255. Cuff is dark at the wrist,
        # skin at the fingertips with a continuous soft transition.
        wrist=tex[80:300,12:24].mean()
        finger=tex[80:300,207:227].mean()
        transition=tex[80:300,68:78].mean()
        self.assertLess(wrist,70)
        self.assertGreater(finger,110)
        self.assertGreater(transition,wrist)
        self.assertLess(transition,finger)
        tri=np.array([[1,0,-1],[2,0,-1],[1,1,-1],
                      [1.2,0,-1],[2.1,0,-1],[1.2,1,-1]],float)
        joints=np.zeros((len(tri),4),int)
        joints[3:,:1]=1   # adjacent bone weight shifts to sleeve/wrist
        weights=np.tile([1.,0.,0.,0.],(len(tri),1))
        uvs=hand_uv(tri,np.tile([0.,0.,1.],(len(tri),1)),
                    joints,weights,['j_finger','j_wrist'])
        # A wrist joint no longer pushes the triangle into separate cuff UVs.
        self.assertTrue(np.all(uvs[:,1]<.74),uvs)

    def test_photo_bake_not_just_procedural_512(self):
        rng=np.random.default_rng(4726)
        fake={
            'wood':Image.fromarray(rng.integers(40,220,(1024,1024,3),dtype=np.uint8)),
            'metal':Image.fromarray(rng.integers(30,200,(1024,1024,3),dtype=np.uint8)),
            'leather':Image.fromarray(rng.integers(60,190,(1024,1024,3),dtype=np.uint8)),
        }
        with patch('material_v3.photo_library',return_value=fake):
            new=np.array(make_rifle_atlas())
            hands=np.array(make_hand_atlas())
        self.assertEqual(new.shape,(512,512,3))
        self.assertEqual(hands.shape,(512,512,3))
        orig=np.array(original_rifle())
        original_skin=np.array(original_hands())
        self.assertGreater(float(np.mean(np.abs(new.astype(float)-orig.astype(float)))),5)
        self.assertGreater(float(np.mean(np.abs(hands.astype(float)-original_skin.astype(float)))),2)

    def test_uvs_are_per_primitive_not_global_box_and_per_hand(self):
        vertices=np.array([[10,0,1],[10.6,0,1],[10,.5,1]],float)
        normal=np.array([[0,0,1]]*3,float)
        joints=np.zeros((3,4),int)
        weights=np.array([[1,0,0,0]]*3,float)
        full_low=np.array([-15,-5,-3]);full_hi=np.array([40,5,3])
        # Full gun UV wastes almost all wood tile on one tiny part.
        global_uv=source_triangle_uv(vertices,normal,joints,weights,['wood'],'wood',full_low,full_hi,
                                      forced_tile='wood')
        close_uv=source_triangle_uv(vertices,normal,joints,weights,['wood'],'wood',full_low,full_hi,
                                     forced_tile='wood',uv_lower=vertices.min(0),
                                     uv_upper=vertices.max(0))
        self.assertGreater(float(np.ptp(close_uv[:,0])),float(np.ptp(global_uv[:,0]))*10)
        pair=np.vstack([vertices,vertices*np.array([1,1,-1])])
        pair_joints=np.zeros((6,4),int)
        pair_weights=np.array([[1,0,0,0]]*6,float)
        uv=hand_uv(pair,np.tile(normal,(2,1)),pair_joints,pair_weights,['finger_l'])
        self.assertTrue(np.all((uv>=0)&(uv<=1)))
        self.assertNotAlmostEqual(float(uv[0,0]),float(uv[3,0]),places=3)


if __name__=='__main__':
    unittest.main()
