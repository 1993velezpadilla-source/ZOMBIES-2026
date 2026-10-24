# IW3/KisakCOD — primera ejecución Windows dedicada con datos MP originales

## Auditoría ejecutada el 24 de octubre de 2026

Esta fase **NO es un servidor de Zombies funcional**. Objetivo concreto: pasar de compilar C++ a arrancar un proceso KisakCOD-dedi.exe local aislado con datos MP suministrados por el usuario.

**Ejecuciones y evidencia**
- [Primera ejecución (error de librería)](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40114799578): compiló el código, pero el EXE terminó con **0xC0000135 = STATUS_DLL_NOT_FOUND** antes de iniciar el mapa. Al principio también falló el link del EXE porque el CMake no seleccionaba la ruta Release a `d3dx9.lib`; ese problema se corrigió agregando `-DCMAKE_BUILD_TYPE=Release`, con el mismo patrón que la compilación verificada anterior.
- [Segunda ejecución (diagnóstico del nuevo bloqueo)](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40115317692): compila y genera `KisakCOD-dedi.exe`, copia **11 archivos originales** de datos COD4/MP (887,083,379 bytes) a directorio temporal, intenta arrancar el servidor solamente en loopback y publica informe sin binarios.
- [Tercera ejecución tras corregir DLL x86](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40115759578): la librería x86 **D3DX9_43.dll** y su compilador asociado se copiaron desde el paquete oficial Microsoft.DXSDK.D3DX. El EXE arrancó como proceso Windows, pero terminó prematuramente con **-2147483645 = 0x80000003 (STATUS_BREAKPOINT)**. No imprimió salida útil ni cargó el mapa. La causa exacta del breakpoint **no está confirmada**.

El flujo de CI publica `staging-manifest.json` y `server-runtime-report.json` exclusivamente; los archivos originales del juego, EXE compilado y DLLs **se eliminan y no se publican**.

### Lo que está comprobado

| Comprobación | Estado |
| --- | --- |
| Tests de seguridad del extractor usando ZIP artificial | GREEN |
| Se seleccionaron archivos COD4 MP originales (11 / 887 MB) | GREEN |
| Compilación KisakCOD Windows x86 dedicated | GREEN |
| Ejecutable copiado y dependencias D3DX, Miles, Steam, Bink en carpeta aislada | GREEN |
| Creación real de proceso Windows | GREEN |
| Proceso continúa 45 segundos | **RED** |
| Mapa `mp_crash` cargado | **RED / NO VALIDADO** |
| RotU `mod.ff` ejecutándose | **NO CONSTRUIDO** |
| Zombi IA activo, rondas o Mystery Box | **NO VALIDADO** |
| Versión Android con Zombies | **NO IMPLEMENTADA** |

### Siguiente bloqueo preciso

`0x80000003` es un **breakpoint de software**; no significa que el paquete MP esté corrupto ni que los datos originales no funcionen. Hay que capturar una pila de llamadas con símbolos/PDB para ubicar si procede de aserción interna del motor, inicialización de Steam (cuya copia de COD4 requiere autenticación), incompatibilidad del servidor o falta de datos. Solo entonces corregir en la rama local de código GPL, sin modificar el snapshot original importado ni su licencia.

**Limitación del test:** Solo se han preparado 11 archivos del ZIP. El upstream KisakCOD recomienda una instalación completa y Steam con licencia. Incluso si se supera el breakpoint, la carga de `mp_crash` podría requerir más archivos; no inferir compatibilidad hasta obtener logs de mapa.

### Nuevos archivos de la rama

- `tools/iw3_rotu/windows_mp_data_stage.py` — lectura directa del ZIP particionado y CRC de cada archivo, whitelist de extensiones, sin binarios ejecutables originales.
- `tests/test_windows_mp_data_stage.py` — pruebas sintéticas de rutas inseguras y ausentes.
- `tools/iw3_rotu/run_windows_mp_server_probe.ps1` — arranque Windows de Kisak-dedi con red local, corte tras 45 s, clasificación de salida y logs.
- `.github/workflows/iw3-windows-runtime-probe.yml` — CI reproducible en Windows 2022 con compilación + ejecución local.

**No reclamar GREEN de gameplay:** el último `Actions conclusion=success` indica que la auditoría procesó y registró el problema; **el mapa y Zombies NO están funcionando**.


## Diagnóstico exacto del breakpoint (nueva evidencia)

La prueba instrumentada [run 40117413584](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40117413584) consiguió **resolver el símbolo y la línea del breakpoint** gracias al PDB compilado desde KisakCOD:

- `BREAKPOINT code=80000003`
- `SYMBOL DB_Thread +0x26`
- `SOURCE src/database/db_registry.cpp:2390`

El código original tiene explícitamente `__debugbreak()` en el camino `if (setjmp(*Value))` de `DB_Thread`, después de `Profile_Recover(1)` y antes de `Com_ErrorAbort()`. Por tanto el servidor **no se está cerrando por un breakpoint arbitrario del sistema operativo**: está llegando al manejador de errores de carga de base de datos del propio motor. **Esto no identifica todavía el error original.**

La rama de pruebas añade una modificación **solo a una copia temporal** del código para registrar `com_errorMessage` justo antes de ese breakpoint, sin eliminarlo ni modificar el snapshot GPL vendorizado. El siguiente gate es leer el error real y determinar si falta una fastfile, una carpeta de localización o hay otro defecto. Un `Actions success` de diagnóstico no equivale a mapa cargado.

**Precaución:** en la prueba anterior el proceso terminaba a los pocos segundos (código 0x80000003), sin cargar `mp_crash`, sin `mod.ff` ni zombi. Sigue siendo runtime **RED**.


## 🟢 ACTUALIZACIÓN: Servidor MP `mp_crash` vivo y verificable (24 oct 2026)

**GREEN runtime real verificado:** [run 40119304501](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40119304501), commit `6dcbf150`.

- Servidor `KisakCOD-dedi.exe` construido de fuente Windows x86, ejecutado de forma efímera en el runner Windows 2022.
- Datos originales del usuario importados de forma temporal: **13 archivos, 944,952,874 bytes**; incorpora fastfiles multijugador localizados en español para corregir el camino de error anterior.
- **Servidor permaneció activo los 45 segundos observados** (`server_alive_at_45_seconds=true`, `exited_early=false`).
- Un cliente de **consulta UDP localhost `127.0.0.1:28960` obtuvo un `statusResponse` genuino** con `gamename=KisakCoD4`, `g_gametype=war`, `mapname=mp_crash`, `protocol=1`. El puerto UDP estaba enlazado; esta respuesta valida el servidor multijugador para ese mapa por protocolo, no solo que existe un proceso.
- El proceso fue detenido al terminar el test y se eliminaron los archivos del juego. Los artifacts de GitHub contienen **exclusivamente informe y diagnóstico**, sin recursos comerciales, ejecutables o DLL.
- **Todavía NO** se conectó un cliente jugable ni se probó colisión/disparos; `client_connected=false`, `mod_ff_present=false`, `zombies_spawned=false`. La prueba verde equivale a **server + map protocol boot**, no a un juego Zombies completo.

**Próximo gate:** construir un cliente Windows MP legal y conectar a servidor local; luego preparar `fs_game`, scripts/recursos de RotU, iniciar modo Survival y verificar un zombi que se mueve, ataca y puede recibir daño. Antes de distribuir, revisar licencias de datos originales y activos de RotU. La línea antigua anterior con `map_boot_verified=RED` corresponde a una prueba obsoleta y está supersedida por la ejecución 40119304501.
