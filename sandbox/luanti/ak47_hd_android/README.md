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
procedural recoil and the previous placeholder fallback are bypassed.

Runtime clips: hip idle, ADS enter/hold/fire/exit, hip fire, normal reload and
empty reload. Input remains the existing Luanti joystick/look/jump/sneak.
Labeled **FIRE**, **ADS**, and **R** touch buttons use dig, place and aux1.
ADS toggles. R reloads; sneak+fire also reloads. Ammo is 30/210 initially.
Normal reload is 83/30s, empty reload 106/30s, and ADS exits before reloading.
An AK is added and equipped on world join. Raycast hits use the camera center.

Build: `.github/workflows/ak47-hd-private-android.yml`. It reuses the established
private extraction, verifies the native loader, compiles ARM64, verifies actual
nested APK assets and the Android signature, and encrypts the APK with a
delivery public key. Only encrypted APK bytes and non-reversible metadata are
public Actions artifacts. The private decryption key is never in git or CI.
The decrypted APK is delivered privately to the owner. No plaintext APK, game
models, keyframes or original textures are committed or publicly released.

Source build recipe and upstream license notices remain in the existing app.
This prototype still requires a real Android launch/play test and FPS
measurement; source/loader tests and a signed build do not establish those.
