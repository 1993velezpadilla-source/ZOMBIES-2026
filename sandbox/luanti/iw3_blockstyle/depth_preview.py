"""Depth-tested EGL preview of actual posed GLB vertices; not game footage.

The dense rifle needs a real depth buffer: triangle-average painter sorting
can draw internal long faces over the exterior. Both comparison models use
this same renderer, lighting, projection and resolution.
"""
import math
import numpy as np
from PIL import Image,ImageDraw
from render_fps_camera_probe import projection_basis

class DepthPreview:
    def __init__(self,width=1100,height=640):
        import moderngl
        self.gl=moderngl;self.width=width;self.height=height
        self.ctx=moderngl.create_standalone_context(backend='egl')
        self.backend=self.ctx.info['GL_RENDERER']
        self.program=self.ctx.program(vertex_shader='''#version 330
            uniform mat4 clip_from_world;
            in vec3 in_position;
            in vec3 in_color;
            out vec3 color;
            out vec3 position;
            void main(){
                position=in_position;color=in_color;
                gl_Position=clip_from_world*vec4(in_position,1.0);
            }''',fragment_shader='''#version 330
            in vec3 color;
            in vec3 position;
            out vec4 frag;
            void main(){
                vec3 normal=normalize(cross(dFdx(position),dFdy(position)));
                vec3 light=normalize(vec3(-0.45,0.8,0.4));
                float shade=0.68+0.32*abs(dot(normal,light));
                frag=vec4(color*shade,1.0);
            }''')
        samples=min(4,self.ctx.info.get('GL_MAX_SAMPLES',0))
        self.samples=samples
        self.color=self.ctx.renderbuffer((width,height),4,samples=samples)
        self.depth=self.ctx.depth_renderbuffer((width,height),samples=samples)
        self.fbo=self.ctx.framebuffer([self.color],self.depth)
        self.resolve=self.ctx.simple_framebuffer((width,height),components=4)
        self.buffers={}

    def _draw(self,geometry,matrix,label,outfile,caption):
        self.fbo.use();self.ctx.viewport=(0,0,self.width,self.height)
        self.ctx.enable(self.gl.DEPTH_TEST);self.ctx.disable(self.gl.CULL_FACE)
        self.ctx.depth_func='<='
        self.fbo.clear(21/255,24/255,31/255,1.,depth=1.)
        self.program['clip_from_world'].write(np.asarray(matrix,dtype='f4').T.tobytes())
        faces=0
        for i,(xyz,indices,colors) in enumerate(geometry):
            data=np.concatenate((xyz,colors[:,:3]),axis=1).astype('f4').tobytes()
            index_data=np.asarray(indices,dtype='u4').tobytes()
            old=self.buffers.get(i)
            if old is None or (old[0].size,old[1].size)!=(len(data),len(index_data)):
                if old:
                    for value in reversed(old):value.release()
                vbo=self.ctx.buffer(data);ibo=self.ctx.buffer(index_data)
                vao=self.ctx.vertex_array(self.program,[(vbo,'3f 3f','in_position','in_color')],ibo)
                self.buffers[i]=(vbo,ibo,vao)
            else:
                vbo,ibo,vao=old;vbo.write(data);ibo.write(index_data)
            self.buffers[i][2].render(self.gl.TRIANGLES)
            faces+=len(indices)//3
        self.ctx.copy_framebuffer(self.resolve,self.fbo)
        image=Image.frombytes('RGB',(self.width,self.height),self.resolve.read(components=3,alignment=1))
        image=image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        geometry_pixels=int(np.count_nonzero(np.any(np.asarray(image)!=[21,24,31],axis=2)))
        draw=ImageDraw.Draw(image)
        draw.rectangle((0,0,self.width,76),fill=(14,17,22))
        draw.text((18,16),label,fill=(233,238,246))
        draw.text((18,43),caption,fill=(179,196,210))
        draw.rectangle((0,self.height-50,self.width,self.height),fill=(14,17,22))
        draw.text((18,self.height-32),'REAL GLB + SOURCE XANIM | DEPTH-TESTED PREVIEW | NOT GAME FOOTAGE',fill=(237,186,109))
        if outfile is not None:
            outfile.parent.mkdir(parents=True,exist_ok=True);image.save(outfile,optimize=True)
        return image,{'source_faces':faces,'drawn_faces':faces,'geometry_pixels':geometry_pixels,
                      'face_count_means':'submitted to depth-tested rasterizer, not visible pixel count',
                      'renderer':'OpenGL EGL','backend':self.backend}

    def render(self,geometry,camera,sign,label,outfile,fov=75.,forward_override=None,roll_degrees=0):
        basis=np.asarray(projection_basis(sign,forward_override,roll_degrees))
        view=np.eye(4);view[:3,:3]=basis;view[:3,3]=-basis@np.asarray(camera)
        near,far=.25,400.
        scale=1./math.tan(math.radians(fov*.5))
        projection=np.zeros((4,4));projection[0,0]=scale
        projection[1,1]=scale*self.width/self.height
        projection[1,2]=-30./self.height
        projection[2,2]=(far+near)/(far-near);projection[2,3]=-2*far*near/(far-near)
        projection[3,2]=1.
        _,report=self._draw(geometry,projection@view,label,outfile,
                           f'Actual posed geometry | {fov:g} deg FOV | fixed camera | depth buffer + {self.samples}x MSAA')
        return report

    def orthographic(self,geometry,camera,label,outfile):
        axis,vertical,side,yaw,elevation,cx,cy,scale=camera
        right=np.zeros(3);up=np.zeros(3);front=np.zeros(3)
        right[axis]=math.cos(yaw);right[side]=math.sin(yaw)
        up[axis]=math.sin(elevation)*math.sin(yaw)
        up[side]=-math.sin(elevation)*math.cos(yaw);up[vertical]=math.cos(elevation)
        front[axis]=math.cos(elevation)*math.sin(yaw)
        front[side]=-math.cos(elevation)*math.cos(yaw);front[vertical]=-math.sin(elevation)
        matrix=np.zeros((4,4));matrix[3,3]=1.
        matrix[0,:3]=right*2*scale/self.width;matrix[0,3]=-cx*2*scale/self.width
        matrix[1,:3]=up*2*scale/self.height;matrix[1,3]=-cy*2*scale/self.height-24/self.height
        matrix[2,:3]=front*.005;matrix[2,3]=-.5
        return self._draw(geometry,matrix,label,outfile,'Actual posed geometry | fixed orthographic camera | same lighting')[1]

    def close(self):
        for buffers in self.buffers.values():
            for value in reversed(buffers):value.release()
        for value in (self.resolve,self.fbo,self.color,self.depth,self.program):value.release()
        self.ctx.release()
