# AK47 512x512 texture atlas

The HD rifle now carries one embedded 512x512 RGB PNG. This is an actual
base-color texture with new UVs, rather than a screenshot size or a renamed
geometry-density setting. It is painted at native resolution with deterministic
wood grain, machined steel, receiver seams and pressed-magazine grooves. No
source-game texture is used. The earlier procedural vertex colors are removed
from the rifle material bindings to avoid multiplying its dark palette twice.

The atlas has four padded material regions. UVs come from the shell's rest-space
positions and dominant face normal; each emitted quad stays inside one region.
Magazine and bolt/trigger joints retain their material assignments while moving.
The embedded PNG and the separately supplied PNG are byte-identical. GLB
materials reference the image through baseColorTexture and TEXCOORD_0 with linear
sampling and clamped edges. Four pixels of edge extrusion isolate the regions.

The 144,134-triangle rifle, 9-joint native skin, inverse binds, 39 animation
definitions and all their binary data remain unchanged. Position, normal,
index, joint and weight accessors retain their identities and data. New UV/image
bytes are appended after the original binary. The separate animated hand-only
model is unchanged.

Depth previews now read the image from the delivered GLB and sample it on the
GPU. They retain the same fixed camera, source XANIM timing, source DObj mount
and lighting used for geometry review. Each full FPS frame reports textured
primitive count and decoded image dimensions. Tests check native atlas detail,
preservation of a moving skin, and actual GPU image sampling including glTF's
top-left UV origin. The legacy painter path remains an untextured reference.

Local actual-source verification: all 14 regression tests pass; the original
binary prefix, animation definitions and protected geometry accessors match
exactly. All 117 rendered FPS frames sample four textured primitives from one
decoded 512x512 image. The normal reload contains 67 frames and plays for 2.77
seconds against its 2.76666665-second source. Minimum sampled core-rifle
visibility remains 98.5687%; the stock and detached magazine are excluded from
that framing measure.

Before/after images are technical renders, not gameplay. This change does not
validate Android frame rate, iron-sight ADS or anatomical contact throughout
every reload. No APK is built by the texture pass. Proprietary model and
animation outputs remain private and excluded from public Actions artifacts.
