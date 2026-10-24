# ZOMBIES-2026

## Pruebas Android del motor original

- [GPU A/B: shader rojo vs SwANGLE y bloqueo de nivel](docs/audit/GPU_BACKEND_AB.md) — SwANGLE elimina el tintado rojo del menú, pero **no** ha demostrado renderizar correctamente el nivel; aparecen miles de errores OpenGL.\n- [Prueba de controles táctiles y comparación visual real](docs/audit/ANDROID_TOUCH_CONTROLS.md) — los siete gestos se inyectaron correctamente y el proceso siguió activo; **las funciones de disparo, movimiento, ADS y recarga aún no están verificadas**.
- [Importación de datos originales y render 3D](docs/audit/REAL_SOURCE_IMPORT.md) — escena 3D visible; tintado rojo y rendimiento emulado inadecuado.

## Auditoría de todo el repositorio y archivos internos (23 octubre 2026)

**Prueba real Android 15: lanzamiento de COD4.apk GREEN** (campaña y recursos externos aún no probados). [Evidencia y capturas del emulador](docs/audit/ANDROID_EMULATOR_SMOKE.md) · [Compatibilidad estática C4/Android](docs/audit/ANDROID_PC_COMPATIBILITY.md).

- **Resumen y conclusiones:** [docs/audit/EXECUTIVE_AUDIT.md](docs/audit/EXECUTIVE_AUDIT.md)
- **Inventario del ZIP y APK:** [docs/audit/README.md](docs/audit/README.md)
- **Análisis de 22 archivos IWD y bibliotecas Android:** [docs/audit/NESTED_AUDIT.md](docs/audit/NESTED_AUDIT.md)
- **24,104 archivos internos catalogados:** [docs/audit/c4-iwd-file-inventory.json](docs/audit/c4-iwd-file-inventory.json)

Auditoría estática completada sin ejecutar los archivos. **Importante: el repositorio y sus Releases son públicos y pueden contener archivos propietarios de terceros.**

Proyecto IGLESIA / ZOMBIES 2026 (Godot).

## Archivo original importado desde Gofile

Origen: https://gofile.io/d/p2DdQHsz

**Importación verificada: GREEN.** El archivo `C4-Mocs.zip` se descargó y pasó la validación de formato ZIP. Tamaño original: **7,021,386,357 bytes**.

**GitHub Release:** https://github.com/1993velezpadilla-source/ZOMBIES-2026/releases/tag/gofile-p2DdQHsz

GitHub no acepta archivos de este tamaño como un único asset de Release. El ZIP original se conserva dividido en cuatro partes consecutivas y sin modificar su contenido:

- `C4-Mocs.zip.part-000`
- `C4-Mocs.zip.part-001`
- `C4-Mocs.zip.part-002`
- `C4-Mocs.zip.part-003`

Para reconstruir exactamente el ZIP original en Linux/macOS:

```bash
cat C4-Mocs.zip.part-000 C4-Mocs.zip.part-001 C4-Mocs.zip.part-002 C4-Mocs.zip.part-003 > C4-Mocs.zip
sha256sum C4-Mocs.zip
```

SHA-256 original: `6787f2082b39ee76445db7fca92892256bfb97e62bbdebfe63f6ee11de6a8d99`

En Windows PowerShell, para unir archivos binarios use `cmd /c copy /b C4-Mocs.zip.part-000+C4-Mocs.zip.part-001+C4-Mocs.zip.part-002+C4-Mocs.zip.part-003 C4-Mocs.zip` y compruebe el resultado con `Get-FileHash C4-Mocs.zip -Algorithm SHA256`.

El registro verificable también está en [incoming/gofile/manifest.json](incoming/gofile/manifest.json).

El flujo `.github/workflows/import-gofile.yml` efectúa la descarga y guarda los ZIP pequeños en Git o los grandes como assets de Release.

## COD4.apk — MediaFire import (2026-10-23)

Source: https://www.mediafire.com/file/q0vww6sknvvfqqh/COD4.apk/file?dkey=8z4vx6zhdqb&r=369

- Status: **GREEN** — downloaded and saved as GitHub Release asset (not executed).
- Original filename: `COD4.apk`.
- Size: **51,760,726 bytes**.
- APK archive validation: valid ZIP containing `AndroidManifest.xml` (45 ZIP entries).
- SHA-256: `40386503d564b0985423339b5ccd5611dc60ce08ebe1b4ae494d4de22a62473c`.
- Release: https://github.com/1993velezpadilla-source/ZOMBIES-2026/releases/tag/mediafire-COD4-apk
- Verification manifest: [incoming/mediafire/manifest.json](incoming/mediafire/manifest.json).
- Import workflow: [.github/workflows/import-mediafire-cod4.yml](.github/workflows/import-mediafire-cod4.yml).

This basic archive validation does **not** establish that the APK is safe to install, legitimate, or compatible with Android.
