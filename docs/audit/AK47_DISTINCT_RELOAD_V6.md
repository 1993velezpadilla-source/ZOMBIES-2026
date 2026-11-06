# AK47 V6 — distinct reload sound audit (verified on built APK)

## Bug reported by Android tester

V5 played the **SAME** GunLib `ak47_reload.ogg` magazine sound in **both**
`ak47dev_reload_normal.ogg` and `ak47dev_reload_empty.ogg`; the empty
version merely included an additional late bolt click. The two file names,
different durations, and Lua sound selection did **not** prove two separate
recordings. User repeatedly reported hearing the empty reload on both.

## V6 independent source recordings

| Playback condition | Actual main recording | SHA-256 | License |
| --- | --- | --- | --- |
| Ammo 1–29 before reload (83 frames / 30 FPS, 2.76667s) | SpringySpringo `assaultriflereload1_0.wav` (independent airsoft assault-rifle reload) | `efb2d724d634eabe6ba8d3065686abca848bb7497d4d43a5e4aed5e5ea23016f` | CC0 1.0 |
| Ammo 0 before reload (106 frames / 30 FPS, 3.53333s) | GunLib `ak47_reload.ogg` (AK-47 magazine handling) + short CC0 bolt click | `78c5d7871301a4fef1dcb01d124657fee211dee48f289b8d08bfe2233499d3ba` (main recording) | CC0 |

Original normal sound page: https://opengameart.org/content/gun-reload-sounds

Original normal WAV: https://opengameart.org/sites/default/files/assaultriflereload1_0.wav

Original empty main WAV/OGG: https://raw.githubusercontent.com/Deases/GunLib/main/sounds/ak47_reload.ogg

## Actual signed APK evidence

GitHub Actions run: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/42228757717

Android package: `com.xziel.voxelsandbox.ak47reloadv6` (separate install from V5).

Signed APK SHA-256:
`43aaec1c4450cad4887761d11d973ff9daa8da2a9275a235d42429e76dea8115`

Extracted from the **built APK**, not from source or unit tests:

* `ak47dev_reload_normal.ogg`: 21,807 bytes, **2.76667s**, 2 channels;
  SHA-256 `ce54297cdfcaefb9cc5641edb497f80cb64523b2cd9d6846b114440258a7cc8f`.
* `ak47dev_reload_empty.ogg`: 32,003 bytes, **3.53333s**, 1 channel;
  SHA-256 `fa05c5f91fbd0a3e07a27fcaca2ef45e396b08c095d1513a331bb105d74da599`.
* Maximum offset-adjusted decoded PCM normalized cross-correlation:
  **0.42398** (quality gate < 0.75). Different recordings, not same source
  shifted, padded, or slowed.
* Normal original recording length: **1.55574s**. Its unchanged audio samples
  begin at **0.55s** of the 2.76667s animation; rest is silence, **NOT slow
  motion or pitch shifting**. Empty event is distinct and includes late bolt.
* In-game Lua: `start_reload` sets `s.empty_reload = s.ammo == 0`
  BEFORE ammo refill; plays `ak47dev_reload_normal` if ammo >0,
  `ak47dev_reload_empty` if ammo==0. Native camera chooses the corresponding
  `viewmodel_ak47_reload` or `viewmodel_ak47_reload_empty` animation
  from the same metadata bit.
* Android signature, ARM64 architecture, full APK, and bundled OGG files
  were verified by GitHub CI; audio PCM independently re-inspected after
  extracting the real artifact.

**Limits:** This is a newly sourced CC0 tactical reload, **not a claim that
both sounds were extracted from COD4**. Real phone listening and frame-precise
magazine handling synchronization still need tester confirmation.
