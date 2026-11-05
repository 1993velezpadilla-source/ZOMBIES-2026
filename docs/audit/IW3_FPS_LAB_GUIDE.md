# IW3 → Godot: primera sala FPS interactiva (prueba PRIVADA)

Estado: **escena FPS interactiva y control táctil implementados**, con pruebas de Linux/Godot. **No existe un APK Android de esta ruta** y no se han certificado las poses anatómicas.

## Archivos del código fuente (no incluyen material de COD4)

- `tools/iw3_fps_playground.gd`: sala 3D de pruebas generada con primitivas de Godot, jugador `CharacterBody3D`, cámara FPS, disparo por raycast contra tres dianas, munición, recarga e inventario.
- `tools/iw3_fps_playground.tscn`: escena de inicio.
- `tools/iw3_fps_weapon_mount.gd`: montaje de manos + arma sobre el `tag_weapon` original.
- `tools/iw3_fps_weapon_controller.gd`: animación y máquina de estados; ADS toggle y hold, fire y reload interrumpible.
- `tools/iw3_make_private_godot_lab.py`: **ensambla localmente** un proyecto completo de Godot, con modelos y texturas que el propietario ya convirtió por su cuenta. No descarga COD4 ni publica sus recursos.

## Controles para probarla

En Android o pantallas táctiles: **pulgar izquierdo** mueve; **pulgar derecho** gira la cámara; botones FIRE, ADS (toggle), RELOAD, JUMP, SWAP, SPRINT y CROUCH. Soporta movimiento y cámara a la vez mediante IDs independientes de multitouch. El diseño del laboratorio es landscape; esto todavía no es la GUI final ni tiene giroscopio.

En computadora: WASD = movimiento, G = capturar mouse, mouse capturado = mirar, botón derecho = ADS; F = disparar, R = recarga, Tab = cambiar arma, Shift = correr, Space = saltar y C = agacharse. Esc = soltar mouse. El mouse requiere presionar G para capturarlo; la prioridad inicial son los controles táctiles.

## Cómo instalar la sala privada en tu computadora

Requisitos: Godot 4.6.3; haber ejecutado **localmente** el proceso privado `iw3_weapon_probe.py prepare/probe`, `iw3_build_animated_previews.py`, `iw3_stage_weapon_textures.py` e `iw3_png_materials.py`, con acceso al archivo COD4 que tú poseas.

Después de que existan las seis escenas GLB animadas y todas sus texturas PNG en `_iw3_private/`:

```bash
python3 tools/iw3_make_private_godot_lab.py --private-root _iw3_private --output _iw3_private/fps_lab

# Abre esta carpeta con Godot 4.6.3 (Import/Scan Project):
#   _iw3_private/fps_lab
# Ejecuta playground.tscn o "Play".
```

El ensamblador **se niega a escribir si falta alguna escena animada o textura**, y se niega a sobrescribir un proyecto existente. Seis GLB: 3 modelos de arma y 3 de manos. Los materiales PNG deben haber sido previamente resueltos.

Este directorio contiene material propietario: **no lo subas a GitHub, lo distribuyas ni publiques una APK con esos archivos** sin autorización del titular.

## Evidencia de GitHub Actions

GitHub Actions reconstruye todo en un runner efímero usando el archivo propietario de su dueño. Se comprueban los seis GLB + los cuatro AnimationPlayer, 16 texturas, cámara, ADS, recarga y control de tres armas. El nuevo laboratorio tiene pruebas adversariales de:

- 2 dedos simultáneos (move + look), dirección del joystick y movimiento horizontal de cuerpo con colisiones.
- Cámara FPS y cámara de mira, disparo de raycast contra diana (impacto real), disminución de munición.
- ADS toggle y estado a 60 fps; cancelar recarga al disparar y recargar completamente.
- Cambiar M4 → AK-47 → MP5 → M4 y conservar la munición por arma.
- Arranque de un **proyecto Godot real con main_scene**, no solo carga de scripts en modo headless.

Se publican **solo JSON con métricas**; no GLB, XANIM, IWI, DDS, PNG, ni capturas de COD4.

## Limitaciones expresas

La prueba numérica de `tag_iron_sight` / `tag_reflex_sight` centrada no equivale a certificar ADS de miras de hierro frente/trasera. El look/recarga de la animación original puede seguir deformado. La sala utiliza dianas geométricas; no hay zombies, rondas ni AI. No se ha realizado test en un teléfono Android real, ni se ha creado un APK distribuible. El uso público/comercial de material original de Call of Duty requiere permisos aparte. El siguiente esfuerzo debe priorizar validación visual del arma/manos y Android, no inflar artificialmente los contadores de modelos.

## Feedback real del Pixel Fold: viewmodels rotados 90 grados (2 de noviembre de 2026)

Capturas **del APK Android con las armas reales** confirman que el programa abre, los 3 modelos y texturas están presentes, existen controles táctiles y el contador ADS cambia. Pero NO deben confundirse esos resultados con un comportamiento visual correcto: **todas las armas tienen su cara superior apuntando a las 9 en vez de las 12** (roll de -/+90° pendiente de validación directa con nuevas capturas). En MP5 y AK-47, el ADS también sitúa armas/manos demasiado cerca o cubriendo la cámara.

En `tools/iw3_fps_playground.gd` se introdujo una corrección de orientación en el **nodo común que contiene manos y arma**, no sobre la malla del arma. El sistema mantiene el eje original +X de IW3 como forward y aplica una rotación de -90° alrededor de ese eje antes de proyectarse en la cámara FPS. Matemáticamente, `Basis(Vector3.RIGHT,-PI/2) * Vector3.BACK` da `Vector3.UP`: la parte superior queda a las **12 en punto**, sin mover ni romper el `tag_weapon` entre arma/manos. Se utiliza el mismo cálculo para los tres modelos; no se adivinan tres offsets diferentes.

`tools/godot_iw3_roll_orientation_probe.gd` comprueba con GLB auténticos que +X source sigue al frente de la cámara y que source +Z queda alineado con screen-up tanto en idle como ADS, fire y reload, con error cero en el attachment. **El pase matemático no sustituye el test de orientación visual y tamaño real en el Pixel Fold.** La rotación puede revelar problemas adicionales en el rest-pose / retargeting XANIM y calibración del ADS; esos deben corregirse independientemente.


## V7: HIP/ADS en directo sobre el arma auténtica (4 noviembre de 2026)

La V6 dejó de ocultar la óptica detrás de la manga, pero aún **no está validada la imagen en Pixel Fold**. Por eso la V7 permite corregir el encuadre sobre el dispositivo sin recompilar una APK por cada offset. No utiliza armas de mentira ni sustituye las animaciones importadas.

La segunda fila de botones en la esquina superior derecha contiene **HIP X / HIP Y / HIP DEPTH / ADS DEPTH**, un selector que avanza de parámetro al tocar el nombre, controles **−**/**+**, y **SAVE**/**RESET**. Los valores de fábrica siguen siendo HIP (X=0.12 m, Y=−0.12 m, profundidad 0.55 m) y ADS con mira a 0.60 m. Hay límites finitos de seguridad para no colocar el marcador dentro de la cámara. Cada M4, AK-47 y MP5 conserva su propio perfil; SAVE escribe solo valores numéricos locales en \`user://iw3_private_viewmodel_v7.cfg\`; RESET restaura los valores originales del arma actual sin guardarlos.

Cambiar HIP durante ADS conserva el estado y la transición de apuntado; los ajustes mueven conjuntamente manos y arma, preservando el anclaje \`tag_weapon\`. El HUD identifica **IW3 V7 ORIGINAL GUNS**, y el instalador privado usa un ID Android distinto (\`org.xziellabs.zombiesiw3v7\`) para distinguir versiones y evitar atribuir capturas de V3/V6 a V7.

El gate de CI ejercita con las **tres escenas GLB auténticas** la pulsación lógica de + y − para HIP X y exige el retorno a la posición previa. **Una validación numérica o APK compilada NO demuestran que las miras, guantes, recargas o rendimiento sean correctos en el Pixel Fold.** Se necesitan capturas de V7 con versión visible y evaluación en dispositivo. No publicar el paquete propietario.
