"""Material regression: actually textured hands and wooden AK furniture."""
import unittest
import numpy as np
from material_v2 import make_rifle_atlas, make_hand_atlas, hand_uv
from export_viewmodel import source_triangle_uv

class MaterialTests(unittest.TestCase):
    def test_atlases_are_detailed_512_not_placeholder(self):
        rifle=np.asarray(make_rifle_atlas())
        hands=np.asarray(make_hand_atlas())
        self.assertEqual(rifle.shape,(512,512,3))
        self.assertEqual(hands.shape,(512,512,3))
        wood=rifle[260:480,5:245].mean(axis=(0,1))
        metal=rifle[5:240,5:350].mean(axis=(0,1))
        skin=hands[7:362].mean(axis=(0,1))
        cuff=hands[390:].mean(axis=(0,1))
        self.assertGreater(wood[0],wood[1]*1.5)
        self.assertGreater(wood[1],wood[2]*1.6)
        self.assertGreater(skin[0],skin[2]*1.5)
        self.assertGreater(skin[0],cuff[0]*2)
        self.assertGreater(np.std(rifle[5:235,:350]),5)
        self.assertGreater(np.std(hands[:360]),6)

    def test_furniture_uses_wood_tile(self):
        vertices=np.array([[1,0,0],[2,0,0],[1,1,0]],dtype=float)
        normals=np.repeat([[0,0,1]],3,axis=0)
        joints=np.zeros((3,4),dtype=int)
        weights=np.repeat([[1,0,0,0]],3,axis=0)
        uv=source_triangle_uv(vertices,normals,joints,weights,['j_gun'],'',
              np.array([-14,-8,-2]),np.array([26,4,2]),forced_tile='wood')
        self.assertTrue(np.all(uv[:,0]<.5))
        self.assertTrue(np.all(uv[:,1]>.5))

    def test_hands_have_skin_coverage_not_one_dark_pixel(self):
        v=np.array([[13,-15,-7],[14,-15,-7],[14,-14,-7],
                    [18,-13,7],[19,-13,7],[19,-12,7]],dtype=float)
        n=np.repeat([[0,0,1]],6,axis=0)
        joints=np.zeros((6,4),dtype=int);joints[3:,0]=1
        weights=np.repeat([[1,0,0,0]],6,axis=0)
        uv=hand_uv(v,n,joints,weights,['j_wrist_le','j_index_ri_0'])
        self.assertTrue(np.all(uv[0:3,1]>=.74))  # cuff
        self.assertTrue(np.all(uv[3:,1]<.74))     # skin
        self.assertGreater(len(set(map(tuple,uv))),2)

if __name__=='__main__':unittest.main()
