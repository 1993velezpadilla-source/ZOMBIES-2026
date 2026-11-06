# AK47 high-detail geometry

The default rifle profile now uses a 384-division surface grid, replacing the
76-division preview. This is a geometry-resolution setting, not a texture size.
Materials remain procedural vertex colors; no claim of a 128x128 texture atlas
is made. The denser conversion follows the same user-provided AK geometry.

| Metric | Previous rifle | High-detail rifle |
| --- | ---: | ---: |
| Surface grid divisions | 76 | 384 |
| Grid pitch, model units | 0.515106 | 0.101948 |
| Occupied/merged cuboids | 891 | 27,908 |
| Rendered triangles | 10,692 | 144,134 |
| Vertices | 21,384 | 288,268 |
| Original matched rifle clips | 39 | 39 |
| Native rifle joints | 9 | 9 |

The new shell has approximately 13.48 times as many triangles and a 5.05 times
finer grid pitch. It removes 95,381 fully internal cuboid faces. Only same-joint
neighbors can hide a face: magazine/receiver and bolt/receiver boundaries remain
closed when their joints move apart. Partially covered long faces remain.

The old 72-step triangle sampling cap could leave holes when requesting a much
finer grid. High detail raises the bounded sampler to 512 steps and 8 million
samples per primitive. Its 40,000-cuboid cap is explicit. High detail rejects a
budget failure instead of silently falling back to a coarse mesh. Metadata
reports requested/effective density, vertex/triangle counts and culled faces.
`--rifle-detail legacy` retains the old geometry for comparisons.

Dense previews use a depth-tested OpenGL/EGL renderer (ModernGL 5.12.0), with
identical lighting, camera and resolution for before/after comparisons. The
legacy painter renderer remains available with `--renderer painter`; average
triangle-depth sorting is insufficient for dense overlapping cuboid surfaces.
The new preview reports submitted faces and actual geometry pixels separately.
These are technical renders, not captured gameplay or Android performance data.

Validation on actual source files: all 39 clip names and durations match; joint
world matrices at start/middle/end of every clip have maximum difference 0.0;
inverse binds are identical; the animated hand-only GLB is byte-identical.
All 11 regression tests pass, including same-joint face culling, large-triangle
coverage, strict detail budgets and draw-order-independent depth occlusion.

The high-detail source pass generated 117 real frames. Its normal reload GIF
still contains 67 poses and plays for 2.77 seconds. Minimum sampled core-rifle
visibility is 98.5687% across all rendered poses using the same fixed review
camera. Stock and detached magazine are excluded from that framing criterion.
Android frame rate, anatomical contact across every reload and iron-sight ADS
remain unapproved. No APK was built for this geometry change.
