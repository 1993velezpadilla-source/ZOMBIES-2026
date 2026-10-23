# ZOMBIES-2026

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
