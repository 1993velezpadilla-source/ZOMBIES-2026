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
