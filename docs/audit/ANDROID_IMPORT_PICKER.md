# COD4 Android — In-app folder import gate (2026-10-23)

**Verified through Android 15 emulator (API 35), GitHub Actions run [40034361248](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40034361248).**

## Verified GREEN

- The unmodified COD4.apk installs and its MainActivity launches on the emulator using an x86_64 → ARM64 native bridge.
- The Android full-screen onboarding overlay is dismissed.
- The native launcher opens the **Android Storage Access Framework** directory picker when pressing **导入游戏资源文件夹 / Import game resource folder**.
- Automation browses `Download/COD4-FIXTURE/`, which contains *only three synthetic text files*: `localization.txt`, `main/README.txt`, `zone/spanish/README.txt`.
- Android system permission dialog **“Allow COD4 to access files in COD4-FIXTURE?”** is shown, and **ALLOW** is accepted.
- The picker closes and the app returns to its launcher after processing the directory.
- The launcher displays **“导入完成，共 3 个文件。” = “Import complete, 3 files.”**
- The launcher also displays **“尚未导入完整 main 文件夹。” = “The complete main folder has not yet been imported.”** This correctly signals incomplete content and does not mean campaign data are usable.
- Diagnostic screenshots `05-fixture-folder.png`, `07-folder-confirm.png`, `08-permission.png`, and `09-final.png` are in the downloadable artifact for the run.

## Limits and next gate

- **No proprietary game files were copied into this test.** It does NOT test C4-Mocs.zip contents and cannot prove Spanish asset compatibility or any game loading.
- No frame-rate or in-game input test, no Zombies implementation, and no Godot project exist as a result of this test.
- The next distinct gate is to check campaign and level-selection behavior against synthetic incomplete import (expected graceful rejection). Only a rights-cleared controlled test could establish full original PC-data compatibility.
- GitHub Actions marked the workflow successful; that means the **automated UI import workflow** completed, not that a commercial mission runs.
- Before further redistribution: public release assets contain files from a third-party commercial game, and permissions must be reviewed.

**Evidence:** [real run 40034361248](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40034361248) — GitHub Actions artifact `cod4-import-picker-synthetic-ui`.


## Follow-up verified — importer vs. campaign gate (run 40035357316)

**This is a newer test than run 40034361248.** The first follow-up accidentally pushed the synthetic files into the Download root, which Android's SAF blocks as a directly selectable folder. The script was fixed to create `Download/COD4-FIXTURE/` explicitly and to avoid repeated Download breadcrumbs.

[Successful latest emulator test](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40035357316), artifact `cod4-import-picker-synthetic-ui`:

- Import button opened Android's native directory picker: **PASS**.
- `COD4-FIXTURE` selected: **PASS**.
- Android storage access granted: **PASS**.
- COD4 launcher reports `导入完成，共 3 个文件。` (3 files imported): **PASS**.
- Launcher explicitly reports `尚未导入完整 main 文件夹。` (complete `main` not imported): **PASS**, expected with synthetic data.
- Pressing the campaign button displays an alert `尚未导入完整 main 文件夹。`: **PASS**, expected graceful rejection.
- Actual COD4 campaign level launch or Spanish PC ZIP import: **NOT TESTED**.
- No PC game files were copied into this test. GitHub reports/fixtures are not proof of any commercial content's compatibility.

Screenshots in artifact: `09-final.png` (import status), `10-campaign-with-incomplete-fixture.png` (expected campaign refusal).
