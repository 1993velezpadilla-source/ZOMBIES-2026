# ZOMBIES FPS LAB — APK Android segura y experimental

**No es el port original IW3 ni lleva armas/modelos/manos de COD4.** Es una prueba jugable independiente que usa la misma sala de tiro, física/cámara y eventos táctiles de nuestro laboratorio Godot, con armas de **primitivas geométricas creadas dentro de Godot**.

## Fuente del proyecto

La rama `feature/iw3-arsenal-extraction-audit-20261102` contiene:

- `tools/iw3_fps_playground.gd` — movimiento, cámara, raycast, blancos, colisiones, HUD de dos pulgares.
- `tools/iw3_fps_android_safe.gd` — capa de arma geométrica provisional (para distribuir sin archivos ajenos).
- `tools/iw3_fps_android_safe.tscn` — escena de la APK.
- `tools/iw3_make_android_safe_project.py` — ensambla proyecto limpio sin modelos de Activision.
- `tools/godot_iw3_android_safe_probe.gd` — prueba determinista del juego original de dianas.
- `.github/workflows/iw3-android-safe-apk.yml` — exporta `ZOMBIES_FPS_LAB_SAFE_ARM64.apk` firmado con **clave temporal de desarrollo**.

Se comprueba el proyecto Godot en Linux antes de descargar el Android SDK. Después se exporta con Godot 4.6.3, Android SDK 35, JDK 17, ABI arm64 y se audita el contenido APK. Solo en caso GREEN aparece un artifact llamado `ZOMBIES_FPS_LAB_SAFE_ANDROID_ARM64_DEBUG_APK` en GitHub Actions, bajo *Artifacts* del run. Hay que entrar con una cuenta GitHub para descargar Actions artifacts. La disponibilidad del archivo dura 14 días.

## Controles

Usa orientación horizontal. Pulgar izquierdo = caminar. Pulgar derecho = girar cámara. Controles en pantalla: FIRE, ADS, RELOAD, JUMP, SWAP, SPRINT y CROUCH. Tres modelos geométricos de prueba permiten cambiar entre armas, apuntar y disparar a las dianas del cuarto.

**El APK solo prueba si Godot + UI + cámara + FPS + movimientos funcionan en Android.** Ningún resultado en Linux confirma automáticamente que el APK corra en el Pixel Fold del usuario. Tras instalar, se verificará rotación, multitouch, HUD, latencia y compatibilidad del procesador ARM64.

## Seguridad y derechos

El proceso **no copia, extrae ni sube assets COD4**. El archivo no pretende reproducir el aspecto de M4, AK-47 o MP5; son placeholders de ingeniería. Es un APK **debug**, no una release de Play Store, ni un juego terminado. Cada build usa una clave debug temporal distinta: para instalar otra compilación con igual package name puede ser necesario **desinstalar la anterior** (y perder datos locales), hasta establecer firma estable.

El conjunto IW3 original con GLB animados queda en pruebas privadas aparte. La exportación pública con dichos recursos no se autoriza sin una licencia del titular.
