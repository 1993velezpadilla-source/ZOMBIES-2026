"""Sparse ADS layering and complete-clip export regressions."""
from pathlib import Path
import tempfile
import unittest
import numpy as np
from voxelize import pack_new,read_glb,write_glb
from render_pose_sequence import PoseScene,quat_matrix
from ads_pipeline import quaternion,correction_matrix,bake,IDLE,UP,DOWN,FIRE,NAMES


def fixture(path):
    doc={'asset':{'version':'2.0'},'buffers':[{'byteLength':0}],
         'bufferViews':[],'accessors':[],'materials':[{}],
         'nodes':[{'name':'tag_view','children':[1]},
                  {'name':'tag_ads','children':[2]}, {'name':'wrist'},
                  {'mesh':0,'skin':0}],
         'skins':[{'joints':[0,1,2]}],'scenes':[{'nodes':[0,3]}],'scene':0}
    raw=bytearray()
    attrs={'POSITION':pack_new(doc,raw,[(0,0,0),(1,0,0),(0,1,0)],'VEC3'),
           'JOINTS_0':pack_new(doc,raw,[(2,0,0,0)]*3,'VEC4',5123),
           'WEIGHTS_0':pack_new(doc,raw,[(1,0,0,0)]*3,'VEC4')}
    ix=pack_new(doc,raw,[(0,),(1,),(2,)],'SCALAR',5125)
    doc['meshes']=[{'primitives':[{'attributes':attrs,'indices':ix,'material':0}]}]
    times=pack_new(doc,raw,[(0,),(1,)],'SCALAR')
    doc['animations']=[]
    for name,node,rows in [(IDLE,2,[(5,2,1)]*2),(FIRE,2,[(5,2,1)]*2),
                            (UP,1,[(0,0,0),(2,0,0)]),(DOWN,1,[(2,0,0),(0,0,0)])]:
        out=pack_new(doc,raw,rows,'VEC3')
        doc['animations'].append({'name':name,'samplers':[{'input':times,'output':out}],
                                 'channels':[{'sampler':0,'target':{'node':node,'path':'translation'}}]})
    write_glb(path,doc,raw)


class AdsTests(unittest.TestCase):
    def test_sparse_ads_preserves_the_base_hand_pose(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'rig.glb';fixture(path);scene=PoseScene(path)
            np.testing.assert_allclose(scene.world(UP,1)[2][:3,3],[2,0,0])
            np.testing.assert_allclose(scene.world(IDLE,0,layers=((UP,1),))[2][:3,3],[7,2,1])
            np.testing.assert_allclose(scene.poses(IDLE,0,layers=((UP,1),))[1][0],[7,2,1])

    def test_complete_ads_clips_preserve_sources_and_match_at_boundaries(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'rig.glb';target=Path(folder)/'baked.glb';fixture(source)
            identity={'rotation_quaternion':[0,0,0,1],'translation':[0,0,0]}
            durations={'hip':1.,'enter':.25,'hold':1.,'fire':1.,'exit':.25}
            bake(source,target,hands=True,config=identity,durations=durations)
            old,old_raw=read_glb(source);new,new_raw=read_glb(target)
            self.assertEqual(new['animations'][:4],old['animations'])
            self.assertEqual(new_raw[:len(old_raw)],old_raw)
            s=PoseScene(target)
            for phase,t,expected in [('hip',0,[5,2,1]),('enter',.125,[6,2,1]),
                                       ('enter',.25,[7,2,1]),('hold',0,[7,2,1]),
                                       ('fire',0,[7,2,1]),('exit',0,[7,2,1]),
                                       ('exit',.25,[5,2,1])]:
                np.testing.assert_allclose(s.world(NAMES[phase],t)[2][:3,3],expected,atol=1e-6)

    def test_fixed_calibration_rotation_handles_half_turns_and_zero_fraction(self):
        for q in ([0,0,0,1],[1,0,0,0],[0,1,0,0],[0,0,1,0],[.5,.5,.5,.5]):
            np.testing.assert_allclose(quat_matrix(quaternion(quat_matrix(q))),quat_matrix(q),atol=1e-12)
        config={'rotation_quaternion':[0,0,np.sin(.1),np.cos(.1)],'translation':[1,2,3]}
        np.testing.assert_allclose(correction_matrix(config,0),np.eye(4),atol=1e-12)
        np.testing.assert_allclose(correction_matrix(config,1)[:3,3],[1,2,3])


if __name__=='__main__':unittest.main()
