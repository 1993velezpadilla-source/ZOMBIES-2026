"""Independent kinematic, clipping, camera-selection and playback regressions."""
import math
from pathlib import Path
from types import SimpleNamespace as NS
import tempfile
import unittest
import numpy as np
from PIL import Image
from iw3_gltf_animation_bridge import add_animation, write_glb
from oat_coordinates import oat_root_tracks
from voxelize import pack_new
from render_pose_sequence import PoseScene
from render_fps_camera_probe import projection_basis, render_perspective
from fps_composition_gate import gif_timing, projected_stats, rank_cameras

C=np.array([[1.,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]])

def transform(translation,axis,angle):
    c=math.cos(angle);s=math.sin(angle);m=np.eye(4)
    m[:3,:3]=([[c,-s,0],[s,c,0],[0,0,1]] if axis=='z'
               else [[1,0,0],[0,c,-s],[0,s,c]])
    m[:3,3]=translation
    return m

def track(a,b):return NS(indices=[0,30],values=[a,b])

class PipelineTests(unittest.TestCase):
    def test_oat_animation_matches_native_skin_in_y_up(self):
        # Independent native scene: an animated root, animated child and a
        # triangle bound to the child. Exported bind frames follow OAT exactly.
        bind0=transform([1,2,3],'z',0);bind1=bind0@transform([2,0,1],'x',0)
        native=np.array([[3.,2.,4.,1.],[4.,2.,4.,1.],[3.,3.,4.,1.]])
        doc={'asset':{'version':'2.0'},'buffers':[{'byteLength':0}],
             'bufferViews':[],'accessors':[],'materials':[{}],
             'nodes':[{'name':'root','translation':[1,3,-2],
                       'rotation':[-math.sqrt(.5),0,0,math.sqrt(.5)],'children':[1]},
                      {'name':'child','translation':[2,0,1]},
                      {'mesh':0,'skin':0},{'children':[0,2]}],
             'skins':[{'joints':[0,1]}],'scenes':[{'nodes':[3]}],'scene':0}
        raw=bytearray()
        doc['skins'][0]['inverseBindMatrices']=pack_new(doc,raw,
            [np.linalg.inv(C@m).reshape(-1,order='F').tolist() for m in (bind0,bind1)],'MAT4')
        attrs={'POSITION':pack_new(doc,raw,(native@C.T)[:,:3].tolist(),'VEC3'),
            'JOINTS_0':pack_new(doc,raw,[[1,0,0,0]]*3,'VEC4',5123),
            'WEIGHTS_0':pack_new(doc,raw,[[1,0,0,0]]*3,'VEC4')}
        doc['meshes']=[{'primitives':[{'attributes':attrs}]}]
        animation=NS(frame_count=30,fps=30,bones=[
            NS(name='root',rotations=track((0,0,0,1),(0,0,math.sqrt(.5),math.sqrt(.5))),
               translations=track((1,2,3),(2,3,4))),
            NS(name='child',rotations=track((0,0,0,1),(.5,0,0,math.sqrt(.75))),
               translations=track((2,0,1),(3,1,2)))])
        converted,roots=oat_root_tracks(doc,animation)
        self.assertEqual(roots,['root'])
        self.assertEqual(converted.bones[1].rotations.values,animation.bones[1].rotations.values)
        self.assertEqual(animation.bones[0].translations.values[0],(1,2,3))
        add_animation(doc,raw,converted,label='test')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'rig.glb';write_glb(path,doc,raw);scene=PoseScene(path)
            for t in (0.,.25,.5,.75,1.):
                root=transform([1+t,2+t,3+t],'z',t*math.pi/2)
                child=transform([2+t,t,1+t],'x',t*math.pi/3)
                expected=(native@(C@root@child@np.linalg.inv(bind1)).T)[:,:3]
                np.testing.assert_allclose(scene.poses('test',t)[1],expected,atol=2e-6)

    def test_y_up_basis_and_near_plane_render(self):
        right,up,front=projection_basis(1,[1,0,0])
        np.testing.assert_allclose(up,[0,1,0]);np.testing.assert_allclose(right,[0,0,1])
        geometry=[(np.array([[1.,-.2,-.2],[1.,.2,-.2],[-1.,0,.2]]),
                   np.array([0,1,2]),np.ones((3,3)))]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'clip.png'
            report=render_perspective(geometry,np.zeros(3),1,'near clip',path)
            self.assertEqual(report['drawn_faces'],1)
            with Image.open(path) as image:self.assertEqual(image.size,(1100,640))

    def test_clipped_pose_is_penalized(self):
        pts=np.array([[-.3,-.3,1.],[.3,-.3,1.],[-.3,.1,1.],[.3,.1,1.]])
        fitted=projected_stats(pts,np.zeros(3))
        clipped=projected_stats(pts,np.array([-.9,0,0]))
        self.assertGreater(clipped['score'],fitted['score'])
        self.assertGreater(clipped['overflow'],0)
        # A mid-reload movement must change selection even with identical idle.
        front=np.array([1.,0,0]);rear=np.zeros(3)
        old=rank_cameras([('idle',0,pts)],front,rear,1.)[0]
        moved=pts+np.array([1.,0,0])
        new=rank_cameras([('idle',0,pts),('reload',.5,moved)],front,rear,1.)[0]
        self.assertNotEqual(old['eye_xyz'],new['eye_xyz'])

    def test_gif_timing_matches_source(self):
        for duration,fps in ((83/30,24),(106/30,12)):
            delays=gif_timing(duration,math.ceil(duration*fps))
            self.assertLessEqual(abs(sum(delays)/1000-duration),.005001)
            self.assertTrue(all(d>=10 and d%10==0 for d in delays))

if __name__=='__main__':unittest.main()
