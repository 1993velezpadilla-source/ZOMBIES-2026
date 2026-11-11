# IW3 Android pass IL — translated GLSL embedded-NUL guard

Date: 2026-11-03. PR #4. Branch: `feature/iw3-native-android-arm64-20261025`.

## Verified baseline
Read the current `third_party/KisakCOD/src/gfx_d3d/r_android_gl_program.cpp` and GLES3 compile gate. The provider compiles translated IW3 D3D9 shader text with explicit GL lengths; it has no EGL lifecycle or original material pipeline integration. The existing CI gate compiles syntax only, not a GPU draw.

## Change
Commit `eaee6d6b104b8e3b673fae987e24f09376608e77` rejects embedded NUL bytes in either translated shader source before calling `glCreateShader`. The existing explicit-length `glShaderSource` path otherwise permits ambiguous binary-like GLSL input. This is fail-closed validation on the authentic IW3 translation boundary, not a substitute renderer.

## Verification and limitations
The GitHub Actions runs for the commit were queued at inspection time (including renderer audit 41603779769). No successful CI for this change, GPU compilation, EGL surface, original material binding, map draw, ARM64-device runtime or gameplay is claimed. The existing `iw3-gles3-program-gate.yml` performs only host GLES3 syntax checks.

Next substantive milestone: connect Android EGL surface/context lifecycle to the original IW3 renderer, then exercise real translated material shaders on device and prove an actual map frame. The JNI APK remains diagnostic. `IW3_PLAYABLE_APK=false`; keep PR #4 open and unmerged.
