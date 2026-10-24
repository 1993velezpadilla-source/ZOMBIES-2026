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


## Compilación real de Windows — gate de compilación (24 octubre 2026)

**GREEN verificado en GitHub Actions:** [run 40074797697](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40074797697).

- Visual Studio 2022 + CMake (Windows Server 2022, arquitectura **Win32/x86**) configuraron correctamente la copia importada de KisakCOD.
- Dependencia DirectX 9 Microsoft.DXSDK.D3DX versión 9.29.952.8 instalada con NuGet.
- Compilación de KisakCOD-dedi **GREEN**, ejecutable generado en runner efímero.
- Compilación de KisakCOD-mp **GREEN**, ejecutable generado en runner efímero.
- **No** se corrieron ejecutables sobre un mapa ni se cargó RotU mod.ff; no hay Zombies jugable ni prueba Android. Binarios/DLLs del runner **no** se publicaron como artifacts ni Release.

**API específica RotU → KisakCOD:** El script scripts/bots/_bots.gsc llama addTestClient(); KisakCOD src/game_mp/g_scr_main_mp.cpp registra addtestclient, y src/server_mp/sv_client_mp.cpp define SV_AddTestClient() que crea clientes NA_BOT, realiza SV_DirectConnect y SV_ClientEnterWorld. Para navegación, scripts/include/waypoints.gsc usa tableLookup(...) y KisakCOD registra tablelookup en el catálogo GSC. Estos contratos están incorporados al source_preflight_pass y tienen tests negativos (registro ausente e implementación vacía). **Esto no demuestra ejecución runtime del mod.**

**Próximo bloqueo real:** construir u obtener con autorización un mod.ff de RotU con assets y GSC válidos; confirmar dependencias del mod para la versión de servidor; usar un mapa MP con waypoints CSV válidos. RotU también referencia modelos, armas y FX que no aparecen automáticamente al compilar el motor. El siguiente gate es **arranque MP + dedicated + RotU con datos autorizados y verificación del primer zombi que se mueve/recibe daño**.

**Fallo resuelto:** el primer intento windows-latest falló por el cambio a VS2026; se fijó windows-2022. El siguiente compiló dedicated y el posterior compiló MP + dedicated.


## Fase 2 — reconstrucción del paquete de scripts RotU (24 octubre 2026)

**Corrección de arquitectura importante:** inspeccionamos el archivo ORIGINAL [compile_mod.bat de RotU](https://github.com/doctorluk/rotu-revolution/blob/b76fca23dbd6e803fcfc66c01411dda37e39e232/compile_mod.bat). Este empaqueta maps/mp, scripts y common_scripts en **z_svr_scripts.iwd** mediante 7z (un IWD es un archivo ZIP). Posteriormente genera **mod.ff** con **linker_pc.exe** y los CoD4 mod tools. Por eso en el mod.csv upstream está comentada la línea include,mod_scripts: NO es un bug ni se debe activar indiscriminadamente; la distribución normal coloca scripts en IWD y assets en mod.ff.

El archivo tools/iw3_rotu/package_gate.py sigue esa construcción: inspecciona el Git tree completo del commit público fijado, compara rutas requeridas por mod_scripts.csv y mod.csv, y puede construir **solo temporalmente**, en el runner de GitHub, un z_svr_scripts.iwd con CRC y SHA-256, sin distribuir ese ZIP. Cuenta también referencias a FX, materiales, modelos y animaciones para no confundir un ZIP con un mod ejecutable completo. tests/test_rotu_package_gate.py cubre el flujo con archivos sintéticos.

El workflow publica **únicamente resultados JSON**, NO los archivos GSC, IWD ni los assets. Si el gate de IWD está GREEN, solo confirma que la parte de scripts fue empaquetada. NO significa que mod.ff esté compilado o que un zombi aparezca. El siguiente bloqueo es la fase de mod.ff, cuya compilación original requiere linker_pc.exe y la estructura de raw/, zone_source/ y assets, que no se obtienen simplemente compilando KisakCOD.

Punto de arranque del modo Survival verificado en el upstream: maps/mp/gametypes/surv.gsc llama desde Callback_StartGameType() a scripts/server/_server::init, scripts/clients/_clients::init, scripts/players/_players::init, scripts/gamemodes/_gamemodes::init y scripts/bots/_bots::init. Esto define un smoke test funcional preciso para cuando existan datos autorizados, mod.ff y un mapa compatible.

**Licencias:** los propios autores de RotU documentan que numerosos modelos y audios están extraídos de títulos comerciales (ver docs/README.txt upstream); estos recursos **no pueden declararse libres** ni publicarse junto con el APK simplemente porque los scripts estén visibles.
