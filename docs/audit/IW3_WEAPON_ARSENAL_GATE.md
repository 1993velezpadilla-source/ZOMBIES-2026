# IW3 → Godot: comprobación del arsenal original de COD4

Estado: **protocolo y pruebas automáticas implementados; extracción real todavía no validada**.

## Lo que sí existe
El Release `gofile-p2DdQHsz` de `ZOMBIES-2026` contiene el ZIP original dividido en cuatro partes (7,021,386,357 bytes). Las auditorías previas identificaron 22 archivos `.iwd`, 73 fastfiles `.ff` y 6,566 texturas `.iwi` dentro de los IWD. **Los modelos XMODEL, animaciones XANIM y WeaponDef suelen estar empaquetados en los fastfiles; no aparecen como archivos sueltos dentro de los IWD.** No contamos todavía con un inventario fiable de armas animadas exportadas.

## Nueva prueba acotada
La rama de auditoría proporciona `tools/iw3_weapon_probe.py` y `.github/workflows/iw3-weapon-arsenal-gauntlet.yml`.

1. Descarga en el runner, temporalmente, las cuatro partes del Release proporcionado por el usuario; comprueba que la longitud total corresponde al archivo original.
2. Lee el ZIP partido **sin unir ni descomprimir los 7 GB completos** gracias al lector `SplitReader`. Extrae **solo** `common_mp.ff`, `mp_crash.ff` y dos IWD (`iw_02.iwd`, `iw_03.iwd`) para un primer pase. Estos IWD no garantizan cubrir todas las texturas.
3. Descarga la **versión v0.34.0 de OpenAssetTools** como herramienta separada. Comprueba su ejecución y llama a `Unlinker --list` y `Unlinker --model-format GLB --image-format DDS --include-assets xmodel,xanim,weapon,image,material` con `--search-path` a las carpetas correctas.
4. Cuenta ficheros exportados, comprueba cabeceras y JSON de glTF binario (`.glb`), distingue las mallas de los esqueletos (`skins`) y animaciones (`animations`) y busca nombres relacionados con **M4, AK-47, MP5 y viewhands**.
5. Publica **solo JSON de metadatos y resultados de pruebas**, nunca modelos, texturas, animaciones, IWD, FF ni instaladores.

Los experimentos se ejecutan en un runner temporal de GitHub Actions. La primera ejecución puede fallar por compatibilidad de OAT o datos específicos: si ocurre, el JSON registra qué comando falló, sin declararlo un éxito.

## Cómo reproducir el pase usando archivos propios
```bash
# Preparar (las 4 partes en _release_assets/c4)
python3 tools/iw3_weapon_probe.py prepare --with-iwds

# Requiere un OpenAssetTools Unlinker v0.34.0 para Linux instalado.
python3 tools/iw3_weapon_probe.py probe --unlinker /ruta/a/Unlinker

python3 -m unittest discover -s tests -p 'test_iw3_weapon_probe.py' -v
```

El informe queda en `_iw3_reports/results.json`. Las salidas privadas se guardan en `_iw3_private/`; **no deben subirse al repositorio público**.

## Criterios de éxito por arma
- **Modelo:** `.glb` válido con geometría/malla.
- **Rig:** esqueleto, bones y pesos asociados al arma/manos y exportación válida.
- **Animations:** animaciones originales de idle, hip fire, ADS, fire y reload, todas con correspondencia de huesos; que Unlinker liste un XANIM_BIN **no** demuestra que esté aplicada al modelo GLB.
- **Godot:** materiales, manos, arma, escalas, orientación, pivotes y reproducción sincronizada comprobados en la escena real.
- **Distribución:** confirmar autorización/licencias antes de usar contenido propietario de COD4 en un juego público o comercial.

**La prueba actual NO convierte las animaciones binarias en AnimationPlayer ni crea escenas Godot.** Ese será un gate distinto después de verificar los recursos reales. **No confundir el motor IW3 con compatibilidad directa de coordenadas Godot.**

Referencias: OpenAssetTools `Unlinker`, opciones `--list`, `--model-format`, `--include-assets`, `--search-path`. Ver https://openassettools.dev/guide/using-the-tools.html y https://github.com/Laupetin/OpenAssetTools/blob/main/docs/SupportedAssetTypes.md .

## Hallazgo de ingeniería inversa (2 noviembre 2026)

El primer pase remoto pasó sobre dos fastfiles y **exportó 1,894 GLB válidos**, con 1,240 GLB con `skins` y 263 nombres base de `viewmodel` (incluidas variaciones/attachments: **no son 263 armas distintas**). Aparecen modelos de M4, AK-47, MP5 y `viewhands` con esqueletos. **0 animaciones incluidas en GLB**. La inspección del código de OAT identificó un bug en nuestro primer comando: el filtro usaba los nombres C++ `xanimparts,weapondef,gfximage`, pero IW3 exige las cadenas de tipo `xanim,weapon,image` según `src/Common/Game/IW3/GameIW3.cpp`. Se corrigió y se repite el pase para comprobar XANIM reales. La corrección no garantiza aún enlazar las animaciones en Godot.
