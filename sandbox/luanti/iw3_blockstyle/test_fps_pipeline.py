"""Independent kinematic, clipping, camera-selection and playback regressions."""
import math
from pathlib import Path
from types import SimpleNamespace as NS
import tempfile
import unittest
import numpy as np
from PIL import Image
from iw3_gltf_animation_bridge import add_animation, write_glb
from oat_coordinates import oat_animation_tracks, install_native_rest
from voxelize import pack_new,exposed_box_faces,surface_cells,voxelize
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
    def test_depth_preview_is_independent_of_triangle_draw_order(self):
        from depth_preview import DepthPreview
        renderer=DepthPreview()
        near=np.array([[2.,-.5,-.5],[2.,-.5,.5],[2.,.5,0.]])
        far=near*2
        indices=np.array([0,1,2])
        red=(far,indices,np.array([[1.,0,0]]*3))
        green=(near,indices,np.array([[0.,1,0]]*3))
        try:
            images=[]
            with tempfile.TemporaryDirectory() as folder:
                for i,geometry in enumerate(([red,green],[green,red])):
                    p=Path(folder)/f'depth_{i}.png'
                    renderer.render(geometry,np.zeros(3),1,'depth test',p)
                    with Image.open(p) as im:images.append(np.asarray(im).copy())
            np.testing.assert_array_equal(images[0],images[1])
            pixel=images[0][335,550]
            self.assertGreater(int(pixel[1]),int(pixel[0])+100)
        finally:renderer.close()

    def test_hidden_face_culling_preserves_moving_joint_boundaries(self):
        box=(0,0,0,0,1)
        same={(0,0,0,0),(0,1,0,0)}
        self.assertEqual(exposed_box_faces(same,box),[0,1,2,4,5])
        moving={(0,0,0,0),(1,1,0,0)}
        self.assertEqual(exposed_box_faces(moving,box),list(range(6)))
        # A partially covered long side must not disappear.
        partial={(0,0,0,0),(0,0,0,1),(0,1,0,0)}
        self.assertIn(3,exposed_box_faces(partial,(0,0,0,0,2)))

    def test_dense_surface_sampling_does_not_leave_large_triangle_holes(self):
        tris=[([(0,0,0),(128,0,0),(128,128,0)],0),
              ([(0,0,0),(128,128,0),(0,128,0)],0)]
        cells=surface_cells(tris,1.,max_steps=512,max_points=100000)
        self.assertTrue(all((0,x,64,0) in cells for x in range(8,120)))

    def test_strict_detail_rejects_silent_budget_downgrade(self):
        doc={'asset':{'version':'2.0'},'buffers':[{'byteLength':0}],
             'bufferViews':[],'accessors':[],'materials':[{}],
             'nodes':[{'mesh':0}],'scenes':[{'nodes':[0]}],'scene':0}
        raw=bytearray()
        aid=pack_new(doc,raw,[(0,0,0),(1,0,0),(0,1,0)],'VEC3')
        doc['meshes']=[{'primitives':[{'attributes':{'POSITION':aid}}]}]
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.glb';write_glb(source,doc,raw)
            with self.assertRaisesRegex(ValueError,'requested density 64'):
                voxelize(source,Path(folder)/'target.glb',density=64,
                         max_cubes=1,allow_lod=False)

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
               translations=track((0,0,0),(1,1,1)))])
        converted,info=oat_animation_tracks(doc,animation)
        self.assertEqual(info['oat_root_tracks_converted'],['root'])
        self.assertEqual(info['bind_offsets_added_to_translation_tracks'],['child'])
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

    def test_no_quat_is_identity_and_missing_trans_preserves_bind(self):
        doc={'nodes':[{'name':'root','children':[1]},
                      {'name':'child','translation':[4,5,6],
                       'rotation':[0,0,.5,math.sqrt(.75)]}],
             'skins':[{'joints':[0,1]}]}
        anim=NS(bones=[NS(name='child',rotations=None,translations=None)])
        converted,info=oat_animation_tracks(doc,anim)
        self.assertEqual(converted.bones[0].rotations.values,[(0.,0.,0.,1.)])
        self.assertIsNone(converted.bones[0].translations)
        self.assertEqual(info['no_quat_identity_tracks'],['child'])

    def test_native_runtime_offsets_are_independent_of_exported_bind(self):
        doc={'nodes':[{'name':'root','children':[1]},
                      {'name':'child','translation':[10,20,30]}],
             'skins':[{'joints':[0,1]}]}
        sidecar={'native_model_locals':True,'bones':[
            {'name':'root','translation':[0,0,0],'rotation':[0,0,0,1]},
            {'name':'child','translation':[0,0,0],'rotation':[0,0,0,1]}]}
        info=install_native_rest(doc,sidecar)
        self.assertGreater(info['maximum_exported_bind_vs_native_local_translation_difference'],30.)
        animation=NS(bones=[NS(name='child',rotations=None,translations=track((1,2,3),(2,3,4)))])
        converted,_=oat_animation_tracks(doc,animation)
        self.assertEqual(converted.bones[0].translations.values[0],(1,2,3))

    def test_iw3_model_attachment_converts_export_basis_once(self):
        from render_mounted_viewhands import OAT_TO_NATIVE, transform_points
        native_point=np.array([[2.,3.,4.]])
        hand_native=transform([5,6,7],'z',math.pi/3)
        hand_gltf=C@hand_native
        exported=transform_points(native_point,C)
        actual=transform_points(exported,hand_gltf@OAT_TO_NATIVE)
        expected=transform_points(native_point,C@hand_native)
        np.testing.assert_allclose(actual,expected,atol=1e-10)

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
