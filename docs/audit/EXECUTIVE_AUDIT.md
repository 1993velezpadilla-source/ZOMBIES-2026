# ZOMBIES-2026 — Auditoría ejecutiva completa (23 octubre 2026)

**Estado: auditoría estática GREEN en GitHub Actions. No significa que los juegos se ejecuten ni que los recursos sean compatibles con Godot.**

Repositorio auditado: `1993velezpadilla-source/ZOMBIES-2026`, rama `main`. Se revisó el árbol Git, sus scripts y workflows, ambos GitHub Releases, los dos archivos binarios completos mediante sus índices ZIP, los 22 subarchivos IWD del juego de PC y los 6 subarchivos del APK. **No se ejecutaron EXE, APK ni librerías nativas.** Se verificaron SHA-256 de los dos archivos originales, no todas las CRC de cada archivo interno.

## 1. El repositorio Git (código visible fuera de los Releases)

Al comenzar la auditoría, `main` contenía README, dos manifiestos de importación, dos workflows de importación y dos scripts de descarga. La auditoría añadió scripts y workflows de inspección y los reportes en `docs/audit/`. **No hay proyecto Godot compilable ni proyecto Unreal**: ningún `project.godot`, `.tscn`, `.gd`, `.uproject`, `.umap`, modelo `.glb` ni flujo de build de videojuego identificado como proyecto propio.

- Rama: `main`; protección de rama: **no configurada**.
- Repositorio: **público**.
- Workflows de importación: dos ejecuciones fallidas antiguas por cambios en API de Gofile, después importación correcta; MediaFire import correcto.
- Workflows de auditoría: inventario de releases y segunda pasada anidada finalizados correctamente. La primera pasada anidada generó 104 errores por faltar `seekable()` en el lector virtual; ese defecto se corrigió y la repetición terminó con **0 errores**.
- Los scripts de importación y auditoría efectúan descargas y lectura estática. No se observó un compilador, exportador APK/Godot o conversor de ejes en el repositorio.
- Los workflows usan `GITHUB_TOKEN` con permiso `contents: write` para enviar los resultados a `main`; conviene revisar la estrategia de permisos/protección antes de continuar.

## 2. Primer Release: `C4-Mocs.zip` (paquete de PC)

- Tamaño original: **7,021,386,357 bytes**, SHA-256: `6787f2082b39ee76445db7fca92892256bfb97e62bbdebfe63f6ee11de6a8d99` (coincide).
- Almacenado en cuatro assets `.part-000` a `.part-003`, reconstruibles sin cambios.
- ZIP exterior: **234 entradas: 215 archivos + 19 directorios**, sin nombres de archivo duplicados, encriptados o con rutas de extracción fuera del directorio detectados.
- Presenta instalación de **Call of Duty 4: Modern Warfare para Windows**; ejecutables `iw3sp.exe` y `iw3mp.exe`, bibliotecas DLL/ASI, videos Bink (`.bik`), datos `.ff` y `.iwd`.
- **73 archivos `.ff`**, entre ellos `zone/spanish/mp_crash.ff`, `mp_shipment.ff`, `mp_crossfire.ff`, `mp_overgrown.ff`, `ac130.ff`, `ui.ff`, etc. Son *fastfiles* del motor IW; **no** son escenas Godot/Unreal editables.
- **53 videos `.bik`**, 22 paquetes `.iwd`, 5 archivos `.exe` y otros recursos periféricos.
- La carpeta `Mods/ModWarfare` contiene `mod.ff`, `z_modwarfare.iwd`, scripts y configuraciones del sistema ModWarfare. Eso es una muestra de modding, no un proyecto Zombies ya creado.
- La carpeta `players/profiles/` contiene archivos de configuración/perfiles: revisarlos antes de cualquier nueva publicación pública para evitar exponer datos de usuario o configuraciones sensibles.
- Hay `Docs/license.txt` y otros avisos propios del juego; son indicio de términos ajenos que deben respetarse.

### Dentro de los 22 archivos IWD (inspeccionados todos)

**24,104 archivos internos, 0 errores de lectura del índice ZIP anidado:**

| Tipo | Cantidad | Observación |
| --- | ---: | --- |
| `.wav` | **16,992** | Sonidos y abundantes paquetes de voz localizados al español |
| `.iwi` | **6,566** | Texturas del motor IW, requieren conversión de formato |
| `.mp3` | **119** | Audio comprimido |
| `.cfg` | **129** | Configuración |
| `.gsc` | **10** | Scripts de `ModWarfare`, todos en su pequeño IWD |
| `.accu` | **15** | Datos de precisión/AI vs. player |
| `.csv` | **2** | Datos de tabla |
| Sin extensión | **271** | Necesitan identificación individual si resultan relevantes |

**Búsqueda por nombres en los 24,104 archivos internos:** ningún archivo con `zombie`, `nacht`, `mp40`, `perk`, `xmodel` ni `animation` en el nombre. Esto **no prueba** que no exista contenido relacionado dentro de `.ff`, porque no se decodificaron las estructuras de esos binarios compilados. Tampoco permite inferir su comportamiento.

Hay rutas como `images/hud_ak47.iwi`, `images/mtl_weapon_colt1911_col.iwi`, `maps/mp/gametypes/_weapons.gsc` y `accuracy/aivsplayer/pistol.accu`. Indican recursos de HUD/armas y scripts de modificación de partida, pero no son coordenadas o riggings listos para Godot.

## 3. Segundo Release: `COD4.apk` (Android)

- Tamaño: **51,760,726 bytes**, SHA-256: `40386503d564b0985423339b5ccd5611dc60ce08ebe1b4ae494d4de22a62473c` (coincide).
- ZIP Android: **45 archivos**; `AndroidManifest.xml` presente.
- ID: **`com.cod4.firstmission`**. Nombre: **COD4**.
- Versión: **`0.5.9-r6-integrated-alpha`** (código 26).
- Android `minSdk` **24**, `targetSdk` **36**.
- Actividades declaradas: `MainActivity`, `CampaignActivity`, `MultiplayerActivity`, `DriverProbeActivity`.
- Permisos declarados: **INTERNET** y **ACCESS_NETWORK_STATE**.
- Firmas APK: v1 y v2 presentes (sin comprobación externa de la identidad del firmante).
- Plataforma nativa: **ARM64 (`arm64-v8a`)**, con librerías ELF válidas. Entre ellas `libcod4first.so`, `libcod4mp.so`, `libc4vk.so`, `libc4icd_hal.so`.
- Incluye **ANGLE** (`libEGL_angle.so`, `libGLESv2_angle.so`) y **cinco paquetes comprimidos de drivers gráficos**, incluidos Mesa Turnip (Adreno), PanVK y RADV.
- Contiene `assets/cod4x/jcod4x_00.iwd`, inventariado a **55 archivos internos** (29 texturas `.iwi`, 25 audios `.mp3` y un archivo sin extensión).
- Contiene varios `.ff` pequeños de COD4X, un `classes.dex`, licencias de componentes, catálogos y avisos de drivers.
- No se hallaron señales de motores Unity, Unreal, Godot o Cocos según el inventario de nombres. El formato y bibliotecas son **consistentes con un port nativo del motor de COD4**, no un proyecto Godot.
- **NO incluye los 7.02 GB del juego PC dentro del APK**. Por su estructura es plausible que necesite datos de juego externos. Se requiere prueba de arranque y verificación de rutas para confirmar cuál conjunto carga, desde qué directorio y si las campañas realmente funcionan.
- Es un APK **alpha**, no verificado con pruebas reales de seguridad, FPS, movimiento, audio, control táctil, permisos efectivos ni compatibilidad con cada GPU.

## 4. Qué significa para nuestro proyecto IGLESIA/Zombies

**Hallazgo principal:** tenemos un paquete completo de archivos del videojuego de PC y una aplicación Android nativa con motor gráfico/librerías COD4. **No** tenemos por esos dos uploads un juego Zombies de Godot terminado, ni código fuente original de COD4, ni convertidor listo de coordenadas para Project Aether.

- **Ruta A — motor nativo:** investigar si el APK realmente abre y utiliza archivos de un ejemplar de COD4 del que se tenga derecho de uso; sería otro motor y otro pipeline. No asumir compatibilidad ni redistribuibilidad.
- **Ruta B — Godot 4.6:** conservar IGLESIA como proyecto nuevo propio; crear/importar assets originales o licenciados y usar conversión explícita de unidades, pivotes, orientación y rotaciones. Los paquetes `.iwd/.iwi/.ff` no pasan a `.glb` o `.tscn` automáticamente.
- **Para sprites PNG 2.5D:** no hay fotogramas de recarga ya listos en PNG que satisfagan la estética definida. Los `.iwi` son texturas del juego de COD4; no fotogramas de la MP40 + manos de la protagonista.
- **Para gameplay Zombies:** se requieren implementación de rondas, ventanas, ataque/IA, perks, Mystery Box y controles touch/ADS; el inventario no demuestra que existan en estos binarios.

## 5. Riesgos y prioridades

1. **URGENTE — derechos de distribución:** el repositorio es **público** y los Releases incluyen una copia de un juego comercial completo y un APK de procedencia externa. Guardar un archivo descargado no concede derechos para redistribuirlo. Revisar autorización/licencias y, si no existe autorización, retirar los assets públicos. (No se cambiaron visibilidad ni Releases en esta auditoría).
2. **Seguridad del APK:** el manifest carece de permisos sensibles adicionales a red, pero eso **no** equivale a análisis antivirus ni certificación del código nativo; probar con aislamiento antes de instalar en dispositivo personal.
3. **Confusión motor/datos:** APK arm64 Android ≠ ejecutables Windows; APK no contiene los 7 GB. No cambiar Godot a partir de estas observaciones sin prueba funcional.
4. **Privacidad:** revisar `players/profiles/` en el ZIP publicado.
5. **Gobernanza del repositorio:** proteger `main`, restringir escritura de workflows y separar código original de binarios de terceros.

## 6. Referencias exactas de esta auditoría

- [Inventario externo C4, 215 archivos](c4-mocs-file-inventory.json).
- [Inventario completo de 24,104 archivos dentro de 22 IWD](c4-iwd-file-inventory.json).
- [Inventario de 45 archivos APK](cod4-apk-file-inventory.json).
- [Reporte ZIP/APK, manifest Android](README.md).
- [Reporte de inspección de archivos anidados y librerías](NESTED_AUDIT.md).
- [Datos completos del primer pase, en JSON](audit-data.json).
- [Datos completos del segundo pase, en JSON](nested-audit-data.json).

**Límite técnico:** inventarios exhaustivos de rutas y tamaños, verificación SHA de contenedores principales y análisis estático de metadatos, pero sin descompilar todos los fastfiles `.ff`, sin extraer todos los recursos a formatos editables, sin ejecutar APK/EXE y sin comprobar CRC total de cada entrada. Los artefactos de auditoría no son pruebas de funcionamiento.
