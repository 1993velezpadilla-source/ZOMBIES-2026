# AK47 HD Android playtest

Integrates the owner's previously converted HD AK47 into the existing pinned
Luanti 5.18.0 + VoxeLibre app. This is a separate test package:
`com.xziel.voxelsandbox.ak47hd` / **AK47 HD Playtest**.

The model is built privately at runtime from the existing source archive.
It has the actual 144,134-triangle rifle, 12,756 hand triangles, external 512px
rifle atlas and a separate hand palette. The adapter retains only 38 weighted
joints, bakes their source world motion and splits the geometry into eight
u16-compatible buffers below 65,535 vertices each. Luanti's actual C++ GLB
loader and software skinner are checked against private golden deformed
vertices; local maximum error was 0.000003 model units.

The first-person camera renders the new combined mesh with a skinning-enabled
shader. It uses the same native camera origin and 75°/50° horizontal FOV as
the inspected previews, adjusted to the actual viewport aspect ratio.
Near clipping is 0.25 model units for this weapon. Old generic item placement,
and the previous placeholder fallback are bypassed. The inventory item is a
lightweight tool, avoiding a second static copy of the full weapon mesh.

The native Android code uses Release/O3 with NDEBUG, checked against the actual
NDK compilation commands. Identical software skin poses are cached on the
shared mesh; pose changes and static-pose resets invalidate that cache. The
developer FPS overlay reports hardware/software skinning counters.

Gun recoil uses the original AK weapon-definition parameters and the IW3
single-angle integration in 5 ms steps. A reference test compares 10,000 steps
against the original function. Shot counters preserve coalesced events and
the first firing sample advances beyond frame zero even at low FPS. The
combined rifle and hands receive the gun rotation together. World-camera
kick remains a separate integration task.

Decoded media accepts up to 32 MiB per file. Protocol 48+ compression and a
final serialized-packet guard retain the existing reliable transport budget.
The native probe verifies exact compression/packet/decoding round trips,
original source poses, skin-cache invalidation and oversize rejection.

Runtime clips: hip idle, ADS enter/hold/fire/exit, hip fire, normal reload and
empty reload. Input remains the existing Luanti joystick/look/jump/sneak.
Labeled **FIRE**, **ADS**, and **R** touch buttons use dig, place and aux1.
ADS toggles. R reloads; sneak+fire also reloads. Ammo is 30/210 initially.
Normal reload is 83/30s, empty reload 106/30s, and ADS exits before reloading.
An AK is added and equipped on world join. Raycast hits use the camera center.

Build: `.github/workflows/ak47-hd-private-android.yml`. It reuses the established
private extraction, verifies the actual native loader, compiles optimized
ARM64 code, inspects nested APK assets and verifies the Android signature.
At the owner's request the installable APK is published as a GitHub prerelease
asset. An encrypted delivery artifact is also retained; its private RSA key
never enters git or CI. Extracted source archives and standalone game exports
are not committed.

Source build recipe and upstream license notices remain in the existing app.
The previous Debug build ran at 6–7 FPS on the test phone, including while idle.
Device FPS improvement and the appearance of recoil in this optimized build
remain to be confirmed; native host tests do not measure phone performance.
