# ZOMBIES-2026 — IW3 + RotU / fase 1

**Objetivo:** montar una ruta reproducible para probar Zombies sobre KisakCOD/IW3. No se elimina la campaña ni se modifica el APK durante este gate de fuente.

## Hallazgos

| Componente | Estado |
| --- | --- |
| KisakCOD | Fuente Windows importada en third_party/KisakCOD/. Su CMake activa plataforma win32, con targets MP y dedicated. No se compila aquí. |
| RotU-Revolution | Fuente pública en doctorluk/rotu-revolution, rama por defecto experimental (upstream avisa: inestable). |
| RotU IA | scripts/bots/_bots.gsc y _types.gsc, con waypoints, tipos de zombis. |
| RotU rondas | scripts/gamemodes/_survival.gsc y _waves.gsc. |
| RotU Mystery Box | scripts/gamemodes/_mysterybox.gsc (referencias a armas MP del engine). |
| Integración de fuente | Herramienta de preflight y tests en GitHub. **Aún no** es integración runtime ni mod compilado. |
| Zombi jugable / APK propio | **No verificados**. |

**Restricción decisiva:** RotU es un **mod de servidor multijugador** COD4, no una app Android. La guía oficial exige COD4 dedicated 1.7 y señala que el proyecto está pensado para servidores, no un cliente local individual. Una futura sesión offline podría usar servidor local + cliente, pero primero hay que comprobar esa combinación con KisakCOD.

## Lo que ejecuta el primer gate

El workflow “IW3 RotU source preflight” (manual, PR y cambios pertinentes) corre unit tests con datos sintéticos y descarga **solamente código fuente** del commit upstream fijado b76fca23dbd6e803fcfc66c01411dda37e39e232 con sparse checkout. Comprueba: snapshot KisakCOD CMake/MP/dedicated; scripts principales de IA y rondas de RotU; entradas rawfile de mod_scripts.csv y rutas relativas seguras. Publica solo informe JSON (no archivos de COD4).

Uso equivalente con ambos árboles disponibles localmente:

    python tools/iw3_rotu/preflight.py --kisak third_party/KisakCOD --rotu /ruta/rotu-revolution --output rotu-preflight.json

Se puede añadir --game-data /ruta/de/instalacion/propia/cod4 para verificar existencia de main/iw_00.iwd y de fastfiles zone/*/mp_*.ff sin copiarlos ni publicarlos. **source_preflight_pass: true solo significa que coinciden las rutas básicas; no demuestra que RotU compile, cargue, ni que un zombi funcione.**

## Siguiente gate para gameplay real

1. Compilar **Windows MP + dedicated** KisakCOD con Visual Studio y dependencias legítimas y revisar logs.
2. Investigar VM/GSC, mod.ff, fs_game, requisitos CodX/1.7a, configs, rutas y waypoints de RotU. mod_scripts.csv no es un binario: la carpeta GSC, por sí sola, no ejecuta Zombies.
3. Construir el mod de pruebas **local**, con licencias apropiadas; arrancar servidor local con mapa MP autorizado (p. ej. mp_crash) y cliente, y verificar IA, disparos, muerte y avance de ronda.
4. Solo entonces simplificar empaquetado a **Zombies + armas + un mapa**. Quitar campaña del **paquete futuro** tras analizar dependencias; no borrar archivos del repo original ahora.
5. En fase Android: portar código propio a ARM64 + sistema gráfico, archivos, audio, input táctil. El COD4.apk importado es **tercero y no está demostrado que venga de KisakCOD**.

## Licencias importantes

KisakCOD declara GPL-3.0, que **no** concede derechos sobre mapas, armas, sonidos o binarios comerciales de Call of Duty. El RotU upstream tiene avisos y créditos propios, y la página oficial de descargas prohíbe redistribuir sus ZIP. No incluirlos en una distribución pública sin los derechos necesarios; cambiar solo el skin no soluciona derechos sobre modelos o datos subyacentes.

Fuentes: [KisakCOD](https://github.com/SwagSoftware/KisakCOD), [RotU fuente](https://github.com/doctorluk/rotu-revolution), [RotU instalación](https://rotu-revolution.com/install.php), [RotU licencias de descarga](https://rotu-revolution.com/download.php).
