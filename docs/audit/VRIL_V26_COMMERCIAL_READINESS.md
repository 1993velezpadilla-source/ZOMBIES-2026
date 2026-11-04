# Auditoría inicial: Vril v26 / NZ:P — preparación para lanzamiento comercial

**Fecha:** 2026-11-04  
**Estado:** PRELIMINAR — NO constituye autorización legal para publicar ni certifica las armas individualmente.  
**Objetivo:** conservar el arsenal convencional **sin rehacer modelos ni animaciones** siempre que la procedencia y los derechos de cada archivo lo permitan. Separar motor, código de juego, recursos e identidad de la franquicia.

## Lo comprobado en las fuentes oficiales

| Componente | Fuente oficial | Licencia publicada | ¿Permite monetización en principio? | Condición relevante |
|---|---|---|---|---|
| Motor Vril | https://github.com/nzp-team/vril-engine/blob/main/LICENSE | GPL-2.0 | Sí | Licencia del código; al distribuir binarios, cumplir GPLv2, avisos y código fuente correspondiente. |
| Lógica del juego/armas/perks (QuakeC) | https://github.com/nzp-team/quakec | GPL-2.0 | Sí | La lógica está cubierta por licencia de software; no autoriza diseños o marcas de terceros. |
| Recursos del equipo NZ:P | https://github.com/nzp-team/assets/blob/main/LICENSE.md | CC BY-SA 4.0 | Sí, si el licenciante tiene derechos y se cumplen condiciones | Atribución, vínculo a licencia, aviso de modificaciones y compartir adaptaciones bajo CC BY-SA 4.0. |
| Créditos de modelos | https://github.com/nzp-team/nzportable#credits | Créditos a Blubswillrule, Ju[s]tice y Derped_Crusader | **Indeterminado por archivo** | Créditos generales no prueban titularidad ni permisos sobre *cada* arma, textura o sonido. |
| Contenidos de Call of Duty | No licencia de Activision/Treyarch verificada aquí | **No determinada / presumir no autorizada para activos propietarios** | No habilitados por las licencias de NZ:P | Evitar Ray Gun y cualquier identidad gráfica, audio, mapa o marca reconocible protegida de terceros. |
| KisakCOD importado en este repo | `third_party/KisakCOD/ZOMBIES_2026_IMPORT.md` | GPL-3.0 indicada en README de este repo | No usar como sustituto automático | Revisar compatibilidad de distribución con componentes GPL-2.0-only; **no** incluir archivos propietarios COD4/IWD. |

## Decisión práctica de producción

1. **No fabricar ni convertir 30 armas.** Conservar provisionalmente armas y animaciones de la distribución NZ:P v26, sin alterarlas durante la auditoría.
2. **No aprobar publicación comercial aún.** Revisar procedencia de los archivos de armas concretos (modelo de primera persona, textura, sonido, animación, icono) y distinguir creación original del equipo de material exportado/derivado de Call of Duty u otras fuentes.
3. **Reemplazar identidad especial de franquicia**, comenzando por Ray Gun, nombres/skins/logotipos de Perk-a-Cola y otras apariencias distintivas. Cambiar una textura no limpia por sí mismo un diseño protegido.
4. **Crear mapa y marca original**. No incorporar mapas, música, voces o elementos de la franquicia extraídos directamente.
5. **Mantener mecanismos preexistentes** como recarga, ADS, lógica de daño, rondas y máquinas, respetando las licencias del código; no copiar la expresión protegida.
6. **Plan de licencias para Android:** incluir créditos, licencias y acceso al código fuente correspondiente GPLv2; para adaptaciones de assets BY-SA, conservar los avisos y distribuir la adaptación bajo BY-SA 4.0 sin imponer restricciones incompatibles.

## Matriz de auditoría por arma (por completar con archivos reales v26)

| Categoría | Estado | Siguiente prueba |
|---|---|---|
| Armas históricas convencionales: MP40, Kar98k, etc. | **SIN VERIFICAR POR ARCHIVO** | Listar los modelos/texturas/animaciones/sonidos realmente empaquetados; rastrear autoría, licencia y origen. Ser histórica no prueba licencias de los *archivos digitales*. |
| Armas convencionales restantes | **SIN VERIFICAR POR ARCHIVO** | Mismo inventario y trazabilidad por archivo. |
| Ray Gun / arma fantástica reconocible | **REEMPLAZAR ANTES DE PUBLICAR** | Diseño y denominación propios, evitando una simple recoloración. |
| Máquinas de perks/skins/nombres | **REVISAR Y REDISEÑAR IDENTIDAD** | Nombres, formas distintivas, texturas, audio, logotipos; conservar mecánicas cuando proceda. |
| Mapas, música, enemigos, HUD, powerups | **SIN VERIFICAR / REVISAR IDENTIDAD** | Construir mapa propio y documentar procedencia del resto. |

## Regla de pase a monetización

**PASS** solo si (a) el APK usa código y assets con procedencia autorizada, (b) no incorpora obras protegidas de terceros sin licencia, (c) se entregan avisos de atribución y obligaciones GPL/CC, (d) se revisan exigencias de distribución de la tienda Android y del SDK publicitario frente a GPL/CC y (e) se documentan versiones/hashes de los paquetes auditados.

**HOLD** mientras no tengamos el paquete Vril v26 específico y su inventario. La licencia genérica publicada por NZ:P es un avance importante, **pero no equivale a una autorización de cada objeto concreto**.

## Fuentes

- Motor y licencia: https://github.com/nzp-team/vril-engine
- Código de juego y licencia: https://github.com/nzp-team/quakec
- Assets y licencia: https://github.com/nzp-team/assets/blob/main/LICENSE.md
- Créditos/proyecto: https://github.com/nzp-team/nzportable
- Documentación oficial: https://docs.nzp.gay/

**Nota:** Informe técnico preliminar, no dictamen jurídico. Antes de monetizar, revisión profesional de propiedad intelectual y de obligaciones de las licencias.
