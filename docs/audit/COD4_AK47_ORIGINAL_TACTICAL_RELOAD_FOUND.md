# FOUND: original COD4 AK47 nonempty/tactical reload sounds (from user's own archive)

Verified on 2026-11-06 in ZOMBIES-2026 release gofile-p2DdQHsz, C4-Mocs.zip split 7GB.

Source audits: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/42239932564 and https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/42240866044

## Original weapon definition

Path inside game: main/iw_11.iwd -> weapons/mp/ak47_mp

| Field | Original COD4 value |
|---|---|
| reloadAnim | viewmodel_ak47_reload |
| reloadEmptyAnim | viewmodel_ak47_reload_empty |
| reloadTime | 2.5 |
| reloadEmptyTime | 3.25 |
| reloadSound | weap_ak47_reload_npc |
| reloadEmptySound | weap_ak47_reload_npc |
| reloadSoundPlayer / reloadEmptySoundPlayer | blank |

Both direct reloadSound fields are the NPC alias, not first-person Foley. The first-person weapon file has notetrackSoundMap entries: weap_ak47_lift_plr, weap_ak47_clipout_plr, weap_ak47_clipin_plr and weap_ak47_chamber_plr.

## Actual original first-person WAVs, VERIFIED inside zone/spanish/common.ff

| Player sound alias | Original sound path inside FastFile | Duration | Original WAV SHA-256 |
|---|---|---|---|
| weap_ak47_lift_plr | sound/foley/wpfoly_ak47_reload_lift_v4.wav | 0.32952s | 0d29856c9f9063fba5b56d6e468d18f6e52025caf51d35bb40cd732c5901f7a3 |
| weap_ak47_clipout_plr | sound/foley/wpfoly_ak47_reload_clipout_v5.wav | 1.07973s | 5b7fe9e5e588bbed9efb78da9c8a04e6c4c3050e464cd5bbcbe667a034e17e7c |
| weap_ak47_clipin_plr | sound/foley/wpfoly_ak47_reload_clipin_v4.wav | 0.69599s | 6bc27dea15268628cb6404e2ee4ded951792c792faf8184f980171567c26d44d |
| weap_ak47_chamber_plr | sound/foley/wpfoly_ak47_reload_chamber_v4.wav | 0.72567s | b19d3d85fd3820f73aa88bd92619dd8b4ee6c6462721a0a10989877c175301ac |

## Correct approach

The tactical/nonempty reload uses original source audio events from its XAnim (magazine lift, clipout and clipin); empty reload additionally has a chamber/charging event. Only trigger a cue if that specific animation's XAnim notetrack includes it. Need extract actual XAnim notify timings before implementing exact scheduling. Do NOT take the same complete GunLib OGG and change its offset/duration; do NOT substitute a third-party airsoft tactical reload.

The previous APK V5 duplicated the GunLib source recording, and V6 used a separate but non-COD4 recording for normal; neither used these four genuine COD4 sounds. Both were wrong.

Source data remains only inside user's COD4 archive and ephemeral CI runner. Only metadata (filenames, durations, SHA hashes) is committed; no proprietary sound bytes are published.
