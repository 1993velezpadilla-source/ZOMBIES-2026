# FIX62 — Collision Paint (Android / Luanti)

## Qué soluciona

Las escaleras y portones de FIX61 usaban entidades físicas invisibles: podía verse una pared y atravesarla, o pisar peldaños y quedar dentro del modelo. En FIX62, la colisión se construye mediante **nodos reales walkable de Luanti**, invisibles durante el juego y separados del OBJ. No se modifican los modelos ni las texturas.

## Uso sencillo en Android

1. Entra a **Zombies > Editor** con el juego detenido.
2. Apunta a una pieza 3D y pulsa el botón nativo **USE**. No hay que vaciar la mano ni quitar el arma.
3. En el inspector, entra a **PAINT**, que está junto a MOVER, ESCALA, ROTAR y FISICA.
4. Escoge **BROCHA**, **BORRAR** o **CUBETA**. Puedes agrandar o achicar la brocha con BROCHA +/−, de 1 a 3 celdas de diámetro aproximado (radio 0 a 2 nodos).
5. Pulsa **PINTAR EN EL MUNDO**. El panel se cierra; apunta a la estructura y pulsa **USE** para aplicar una pincelada. Los bloques de colisión aparecen azulados mientras editas, pero no en el juego.
6. Para cambiar de herramienta o terminar, abre **Editor > OBJETOS > 3D BUILDER / MODO LIBRE**. Si hay una sesión de pintura activa, vuelve a abrir directamente el inspector de esa pieza. En **PAINT**, pulsa **TERMINAR** o **LISTO**.

**BROCHA** agrega física sólida. **BORRAR** quita física sólida incluso donde la modalidad automática haya colocado colisiones. **CUBETA** rellena una figura de pintura cerrada en el plano de la superficie; si el contorno está abierto no pinta el mundo entero.

## Modo automático y corrección rápida

- **AUTO** infiere el tipo de pieza por su nombre y construye colisiones con nodos reales.
- **ARCO LIBRE** pone volumen en soportes laterales y dintel, dejando la puerta abierta en el centro.
- **ESCALERA** genera peldaños parciales (niveles 1/8) y una cuña sólida debajo para impedir atravesarla.
- **SOLIDO** genera una carcasa física de pared/estructura, no una sola caja de entidad gigante.
- **SIN COLISION** elimina los nodos sólidos del modelo. Puedes pintarlos manualmente después.

Las colisiones creadas están asociadas al modelo y se guardan con él. Cambios de escala, posición o rotación regeneran la forma voxelizada. No sobrescribimos bloques existentes (por ejemplo piedra del terreno) ni nodos de colisión pertenecientes a otra estructura.

## Límites que no vamos a ocultar

- Los nodos físicos tienen resolución aproximada de **1 bloque**, con alturas parciales de 1/8 para los peldaños. Es pintura de colisión volumétrica, **no** mesh collider por triángulo ni dibujo píxel a píxel sobre la textura.
- La brocha se aplica desde el punto donde apunta el cursor (raycast del modelo o intersección de su caja orientada). No lee directamente los triángulos exactos del OBJ; hay que probar en Android la precisión real.
- La cubeta necesita un contorno cerrado (limitado a 800 celdas por operación) para evitar pintar accidentalmente todo el mapa.
- Para rendimiento móvil se limita la generación automática a 2400 celdas por objeto y la vista previa a 60; objetos excesivamente gigantes necesitan ajuste manual.
- En el juego las celdas son transparentes e imposibles de seleccionar con DIG normal. Se pueden borrar exclusivamente con la goma del editor. La geometría 3D permanece siempre visible.
- En lugar de un control 3D arrastrable tipo Unreal, el editor usa la selección por retícula y el botón **USE**, compatible con los controles existentes.
- Los tests de GitHub validan registro de nodos, paso central del arco vacío, escalones, brocha, borrador, cubeta, guardado, transformaciones y no interferir con armas. Solo la prueba táctil sobre **el motor Android real** confirmará que ya puede caminarse perfectamente por cada peldaño.

## Arquitectura
- `fort_collision_paint.lua`: backend de nodos físicos (8 alturas) y manipulación de pincel/borrador/cubeta.
- `fort_editor_v2.lua`: pestaña PAINT y redirección de USE durante pintura.
- `init.lua`: reabrir la sesión desde el menú de Editor.
- `test_fix62_collision_paint.lua` y `test_fix62_paint_touch.lua`: pruebas repetibles.
- Mantiene `fort_collision.lua` como compatibilidad para tests sin API de nodos, pero en el Android real se selecciona el nuevo sistema al detectar `core.set_node` y `core.get_meta`.

Referencia: documentación Luanti sobre nodebox, walkable, física; mod Minecraft Collision Box Editor (inspiración, no código reutilizado).
