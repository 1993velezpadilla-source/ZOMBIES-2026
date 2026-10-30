# XZIEL ZOMBIES — Godot 3D pixel prototype

Independent experimental Godot 4.6 project. **Does not replace IW3** and does not embed Call of Duty game files.

## What is included (first vertical-slice scaffold)

- A small 3D test room built from primitive meshes, with collision and simple lighting.
- Pixelated rendering via a 640x360 viewport scaled with nearest-neighbor viewport stretching.
- FPS controls: WASD, mouse look, Shift to sprint, Space to jump, mouse left to fire, mouse right to toggle ADS, R to reload.
- Android-oriented onscreen FIRE, ADS, RELOAD, JUMP and RUN buttons, plus touch drag movement/look.
- A **procedural blockout weapon** for framing tests. **This is not the previously-made MP40 mesh or its complete reload animation**; it is explicitly a placeholder.
- Simple chase/attack zombies, raycast shots, health, ammo, reload timing, score, and wave progression.

## Open / run

1. Open this folder (containing `project.godot`) in the Godot 4.6 editor.
2. Press F6/F5 to run. For a phone, export to Android using a locally configured Godot Android export template/signing setup.
3. Landscape only. Android GPU compatibility renderer (GL Compatibility).
4. This is a source-code prototype, **not an APK**. No in-device or Godot runtime validation has been performed yet.

## Art strategy

Real 3D geometry + low internal render resolution; no AI-generated sprite sheets are required. The gameplay and camera are independent of the visual style. We can later replace the procedural weapon with a properly licensed MP40 model and replace box zombies with the existing original assets (subject to asset inspection/license).

## Quality gates before calling it playable

- Import and run Godot headless, fix all parser/runtime errors.
- Validate mobile multi-touch (move + shoot + ADS, including controls while dragging).
- Test hipfire muzzle alignment, then ADS sight alignment in landscape on target phone.
- Android ARM64 export, install, and record actual gameplay evidence.
- Test framerate on real device; reduce lights and resolution if needed.
