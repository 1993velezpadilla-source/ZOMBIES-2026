"""Install *AK-only* Lit GL shader variants into Luanti Android assets.

Luanti 5.18's stock fs_model_shader/opengl_fragment.glsl literally ignores
vNormal (TODO directional lighting). That makes even sharp 2K textures appear
flat. These shaders share the original vertex/skinning shader but add a cheap
ambient + diffuse + specular for the rifle; diffuse skin shading for the hands.
No world/map shader is modified. Files in client/shaders are automatically
included by android/app/build.gradle's asset packaging.
"""
from pathlib import Path
import argparse

RIFLE_FRAGMENT=r"""uniform sampler2D baseTexture;

VARYING_ vec3 vNormal;
CENTROID_ VARYING_ mediump vec2 varTexCoord;

void main(void)
{
    vec4 albedo=texture2D(baseTexture,varTexCoord.st);
    if (albedo.a < 0.01)
        discard;

    // Model normals arrive in world-space from Luanti's skinning vertex
    // shader. The built-in fragment shader previously ignored them.
    vec3 n=normalize(vNormal);
    vec3 light=normalize(vec3(0.28,0.72,0.64));
    float diffuse=max(dot(n,light),0.0);
    float hemisphere=0.57+0.36*diffuse;
    // Restrained, cheap metal sheen; no unsupported PBR/normal-map claims.
    vec3 halfVector=normalize(light+vec3(0.0,0.0,1.0));
    float sheen=pow(max(dot(n,halfVector),0.0),22.0)*0.14;
    vec3 color=clamp(albedo.rgb*hemisphere+vec3(sheen),0.0,1.0);
    gl_FragColor=vec4(color,albedo.a);
}
"""

SKIN_FRAGMENT=r"""uniform sampler2D baseTexture;

VARYING_ vec3 vNormal;
CENTROID_ VARYING_ mediump vec2 varTexCoord;

void main(void)
{
    vec4 albedo=texture2D(baseTexture,varTexCoord.st);
    if (albedo.a < 0.01)
        discard;
    vec3 n=normalize(vNormal);
    vec3 light=normalize(vec3(0.28,0.72,0.64));
    float diffuse=max(dot(n,light),0.0);
    float lightTerm=0.65+0.30*diffuse;
    gl_FragColor=vec4(clamp(albedo.rgb*lightTerm,0.0,1.0),albedo.a);
}
"""

def patch(root:Path):
    shaders=root/'client/shaders'
    upstream=shaders/'fs_model_shader'
    vertex=upstream/'opengl_vertex.glsl'
    fragment=upstream/'opengl_fragment.glsl'
    if not vertex.is_file() or not fragment.is_file():
        raise FileNotFoundError('Luanti 5.18 stock model shader not found')
    old=fragment.read_text()
    if 'TODO use vNormal for directional lighting' not in old:
        raise RuntimeError('Upstream model shader changed; re-audit AK lighting')
    for name,source in [('ak47_lit_model_shader',RIFLE_FRAGMENT),
                        ('ak47_lit_skin_shader',SKIN_FRAGMENT)]:
        folder=shaders/name
        folder.mkdir(parents=True,exist_ok=True)
        (folder/'opengl_vertex.glsl').write_bytes(vertex.read_bytes())
        (folder/'opengl_fragment.glsl').write_text(source,encoding='utf-8')
        if 'normalize(vNormal)' not in source:
            raise AssertionError('lit model shader omitted source normals')
    print('AK47_ONLY_LIT_SHADERS: 2 variants; original world and generic model shaders unchanged')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('luanti_root',type=Path)
    patch(ap.parse_args().luanti_root)
