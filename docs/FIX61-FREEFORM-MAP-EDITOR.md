# FIX61 – Freeform Android 3D Map Editor

Based on FIX60. The signed original FIX56 ARM64 engine, 28 guns, ADS, V26 gameplay, and existing map data remain preserved.

## Android controls

In STOP/map-building mode, select one of the 22 Modular Fort items and tap to place it. New architecture is now an entity with its **original Poly Haven glTF dimensions**, rather than a normalized 1×1 Luanti node. The preview appears cyan; its origin is aligned so the lowest visible mesh surface sits at the contacted surface height.

The editor contains four short, non-scrolling touch pages:
- MOVER: decimal X/Y/Z shifts with 0.05, 0.25 and 1 unit increments
- ESCALA: 0.10×–256×, ±0.25× and ±1×, reset to natural source dimensions
- ROTAR: 15°/90° Y rotation and 15° X; the PRECISION XYZ subpage offers ±1° for all axes
- FISICA: AUTO, SOLIDO, ARCO LIBRE, ESCALERA, ESCALERA INV and SIN COLISION

The selection hologram updates with the selected object. Transformations and collision presets are persisted by the entity staticdata and Luanti position persistence. Scaling tries to preserve the bottom face's old world Y so the model does not sink into the floor.

Go to the existing Zombies editor -> OBJETOS -> **3D BUILDER / MODO LIBRE**, or use /zedit. With builder enabled, the original independent USE button selects architecture and ordinary decorative cubic blocks **even when a gun or a block is equipped**. The Editor Tool is no longer inserted into the hotbar on every join. Decorative blocks can also be placed as editable wielditem entities while this mode is enabled. Interactive chests, perks, doors and other scripted nodes are excluded from generic conversion.

## Technical notes

- Existing FIX58/FIX60 nodes are not automatically transformed on load. They convert individually only when selected and actually edited.
- Entities reuse the same original OBJ and texture atlas; resizing does not generate duplicate assets.
- Original glTF dimensions per model are recorded in the generated manifest.
- Arch/gate objects use separate invisible physical volumes for both side supports and a lintel, leaving the opening clear. Staircases use height-adaptive stepped physical proxies, not a large solid cube. Geometry/colllision alignment is approximate and has manual mode switches.
- Luanti's documented raycast reliability bound is 5 nodes per direction for an entity selectionbox. Selection boxes are limited and large objects are additionally picked by an on-demand ray-volume test.
- The fixed-page inspector needs no scrollbar. It does not implement a native swipe scrollbar or a draggable C++ 3D gizmo.

## Remaining validation / known limitations

This is not yet fully validated on an Android screen. Check gate clearance, walking up both stair directions, large-entity FPS, basic-block rendering, arm/ADS controls and the visual cyan overlay.

Texture stretching at scales substantially above the artist's original source size remains a UV/material limitation: FIX61 does **not** yet implement world-space UV remapping or custom shaders. Very large objects can look stretched or blurred. 256× is a practical safety bound, not unlimited geometry. Mobile frame rate may degrade when many collision proxies are present.

Because the CI pipeline generates an ephemeral signing key, a new build may not upgrade over the prior APK without uninstalling. Back up existing worlds before installing.

Poly Haven Modular Fort 01 license: CC0. https://polyhaven.com/a/modular_fort_01
