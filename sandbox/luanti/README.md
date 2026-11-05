# Voxel Sandbox Dev — Android ARM64 prototype

**Scope of this first build:** a complete Minecraft-like voxel sandbox for Android, without any Zombies features yet. It bundles **Luanti 5.18.0** plus the complete **VoxeLibre** game. No Minecraft proprietary content is included.

## What the player gets

- **Survival:** hunger, exploration, crafting, enemies, mining, agriculture, and building with the blocks VoxeLibre supplies.
- **Creative:** unrestricted access to the VoxeLibre Creative inventory, flight/creative gameplay.
- All available VoxeLibre block types, textures, and existing game mechanics.
- Offline worlds and normal Luanti Android controls.
- Standalone app ID: `com.xziel.voxelsandbox`, installed separately from Luanti.
- First APK is **ARM64 test build, debug-signed**, not a Play Store release.
- No ADS, guns, zombie spawns, map exporter, custom texture pack, or ads in this baseline.

Create a **new world** in the app; select the Creative option for building or leave it off for Survival.

## Build

GitHub Actions workflow: `.github/workflows/luanti-voxelibre-android.yml`

Source code is downloaded at build time from the official upstream projects, pinned to:
- Luanti: `5.18.0` from https://github.com/luanti-org/luanti
- VoxeLibre: `4492ce6ff8d856daa4567abe2ea689f4e7a39842` from https://github.com/VoxeLibre/VoxeLibre

The Python patch script adds the unmodified game to the engine's bundled assets, gives the APK a distinct package and name, and narrows the build to ARM64. The verification script inspects the APK for actual VoxeLibre data. CI publishes an installable debug APK as an Actions artifact and attempts a GitHub prerelease with a direct APK file.

## Legal and source

Luanti is LGPL-2.1-or-later. VoxeLibre is GPL-3.0-or-later with third-party media licenses documented upstream. Distribution of a modified combined APK requires applicable source and attribution/notice obligations; the pinned public source repositories and this exact patch recipe serve as build provenance, but review the full license set before publishing commercially. Do not call the result Minecraft or include proprietary Minecraft content.

## Technical caveats

This workflow is intended to produce a prototype but is not proof of functional play on a physical Android device. It still requires a launch, Create World, Survival/Creative, block inventory, save/reload, and touchscreen smoke test on the user's Pixel Fold.
