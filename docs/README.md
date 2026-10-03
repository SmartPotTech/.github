# Documentación de SmartPot

| Documento                              | Qué cuenta                                                                                                                                                                                                                                             | Formato                                                                                                                                       |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| Documentación técnica de la plataforma | La plataforma tal como funciona hoy: arquitectura, contratos MQTT y REST, asistente de IA y aprendizaje continuo, Telegram, cultivos reales y virtuales, ilustración de cada cultivo, datos, PWA, firmware, seguridad, despliegue, calidad y operación | [Markdown](SmartPot_Technical_Documentation.md) · [DOCX](SmartPot_Technical_Documentation.docx) · [PDF](SmartPot_Technical_Documentation.pdf) |
| Recorrido del proyecto                 | Requisito por requisito y diagrama por diagrama: qué se planeó en la fase de diseño, qué quedó construido y cómo se comprueba                                                                                                                          | [Markdown](SmartPot_Project_Journey.md) · [DOCX](SmartPot_Project_Journey.docx) · [PDF](SmartPot_Project_Journey.pdf)                         |
| Ciclo de vida del software             | La lectura crítica de cada etapa: formulación y evaluación, gestión, análisis, diseño, construcción, pruebas y mejora continua, con todos los diagramas                                                                                                | [Markdown](SmartPot_Software_Lifecycle.md) · [DOCX](SmartPot_Software_Lifecycle.docx) · [PDF](SmartPot_Software_Lifecycle.pdf)                |

Los Markdown son la fuente: GitHub los muestra con sus diagramas y de ellos salen los DOCX y los PDF con la identidad de
SmartPot.

## Documentación de cada componente

Esta carpeta reúne la plataforma completa. Cada repositorio tiene además su propia documentación en `docs/`, con la
misma identidad, un diagrama general del componente y los específicos en `docs/diagrams` (mmd, png y svg):

| Componente                                                                       | Qué cuenta                                                                              | Formato                                                                                                                                                                                                                                                                                                                                                                     |
|----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [SmartPot-API](https://github.com/SmartPotTech/SmartPot-API)                     | REST, cultivos reales y virtuales, de la lectura a la orden, seguridad de cada petición | [Markdown](https://github.com/SmartPotTech/SmartPot-API/blob/main/docs/SmartPot_API_Documentation.md) · [DOCX](https://github.com/SmartPotTech/SmartPot-API/blob/main/docs/SmartPot_API_Documentation.docx) · [PDF](https://github.com/SmartPotTech/SmartPot-API/blob/main/docs/SmartPot_API_Documentation.pdf)                                                             |
| [SmartPot-Web](https://github.com/SmartPotTech/SmartPot-Web)                     | pantallas, creación de cultivos, ilustración de cada cultivo, sesión y caché            | [Markdown](https://github.com/SmartPotTech/SmartPot-Web/blob/main/docs/SmartPot_Web_Documentation.md) · [DOCX](https://github.com/SmartPotTech/SmartPot-Web/blob/main/docs/SmartPot_Web_Documentation.docx) · [PDF](https://github.com/SmartPotTech/SmartPot-Web/blob/main/docs/SmartPot_Web_Documentation.pdf)                                                             |
| [SmartPot-AI](https://github.com/SmartPotTech/SmartPot-AI)                       | evaluación, aprendizaje continuo y análisis de flota                                    | [Markdown](https://github.com/SmartPotTech/SmartPot-AI/blob/main/docs/SmartPot_AI_Documentation.md) · [DOCX](https://github.com/SmartPotTech/SmartPot-AI/blob/main/docs/SmartPot_AI_Documentation.docx) · [PDF](https://github.com/SmartPotTech/SmartPot-AI/blob/main/docs/SmartPot_AI_Documentation.pdf)                                                                   |
| [SmartPot-DataGenerator](https://github.com/SmartPotTech/SmartPot-DataGenerator) | cultivos virtuales, modelo físico y API de control                                      | [Markdown](https://github.com/SmartPotTech/SmartPot-DataGenerator/blob/main/docs/SmartPot_DataGenerator_Documentation.md) · [DOCX](https://github.com/SmartPotTech/SmartPot-DataGenerator/blob/main/docs/SmartPot_DataGenerator_Documentation.docx) · [PDF](https://github.com/SmartPotTech/SmartPot-DataGenerator/blob/main/docs/SmartPot_DataGenerator_Documentation.pdf) |
| [SmartPot-IoT](https://github.com/SmartPotTech/SmartPot-IoT)                     | circuito, ciclo principal y atención de órdenes del firmware                            | [Markdown](https://github.com/SmartPotTech/SmartPot-IoT/blob/main/docs/SmartPot_IoT_Documentation.md) · [DOCX](https://github.com/SmartPotTech/SmartPot-IoT/blob/main/docs/SmartPot_IoT_Documentation.docx) · [PDF](https://github.com/SmartPotTech/SmartPot-IoT/blob/main/docs/SmartPot_IoT_Documentation.pdf)                                                             |
| [SmartPot-Broker](https://github.com/SmartPotTech/SmartPot-Broker)               | listeners, permisos por cultivo y certificados                                          | [Markdown](https://github.com/SmartPotTech/SmartPot-Broker/blob/main/docs/SmartPot_Broker_Documentation.md) · [DOCX](https://github.com/SmartPotTech/SmartPot-Broker/blob/main/docs/SmartPot_Broker_Documentation.docx) · [PDF](https://github.com/SmartPotTech/SmartPot-Broker/blob/main/docs/SmartPot_Broker_Documentation.pdf)                                           |
| [SmartPot-DB](https://github.com/SmartPotTech/SmartPot-DB)                       | colecciones, validadores y migración                                                    | [Markdown](https://github.com/SmartPotTech/SmartPot-DB/blob/main/docs/SmartPot_DB_Documentation.md) · [DOCX](https://github.com/SmartPotTech/SmartPot-DB/blob/main/docs/SmartPot_DB_Documentation.docx) · [PDF](https://github.com/SmartPotTech/SmartPot-DB/blob/main/docs/SmartPot_DB_Documentation.pdf)                                                                   |
| [SmartPot-Cache](https://github.com/SmartPotTech/SmartPot-Cache)                 | llaves y endurecimiento de Redis                                                        | [Markdown](https://github.com/SmartPotTech/SmartPot-Cache/blob/main/docs/SmartPot_Cache_Documentation.md) · [DOCX](https://github.com/SmartPotTech/SmartPot-Cache/blob/main/docs/SmartPot_Cache_Documentation.docx) · [PDF](https://github.com/SmartPotTech/SmartPot-Cache/blob/main/docs/SmartPot_Cache_Documentation.pdf)                                                 |
| [SmartPot-Mail](https://github.com/SmartPotTech/SmartPot-Mail)                   | correos y protección de la bandeja                                                      | [Markdown](https://github.com/SmartPotTech/SmartPot-Mail/blob/main/docs/SmartPot_Mail_Documentation.md) · [DOCX](https://github.com/SmartPotTech/SmartPot-Mail/blob/main/docs/SmartPot_Mail_Documentation.docx) · [PDF](https://github.com/SmartPotTech/SmartPot-Mail/blob/main/docs/SmartPot_Mail_Documentation.pdf)                                                       |

## Diagramas

| Diagrama                                  | Tipo                | Documentos               |
|-------------------------------------------|---------------------|--------------------------|
| 01 Arquitectura                           | Flujo               | Técnica, ciclo de vida   |
| 02 Secuencia de una lectura               | Secuencia           | Técnica, ciclo de vida   |
| 03 Asistente de IA                        | Flujo               | Técnica, ciclo de vida   |
| 04 Modelo de datos                        | Entidad-relación    | Técnica, ciclo de vida   |
| 05 Estados de un comando                  | Estados             | Técnica, ciclo de vida   |
| 06 Despliegue                             | Flujo               | Técnica, ciclo de vida   |
| 07 Redes                                  | Flujo               | Técnica, ciclo de vida   |
| 08 QA                                     | Flujo               | Técnica, ciclo de vida   |
| 09 Causa y efecto                         | Flujo               | Recorrido, ciclo de vida |
| 10 Casos de uso                           | Flujo con actores   | Recorrido, ciclo de vida |
| 11 Clases del dominio                     | Clases              | Recorrido, ciclo de vida |
| 12 Componentes                            | Flujo               | Recorrido, ciclo de vida |
| 13 Actividad del control automático       | Actividad           | Recorrido, ciclo de vida |
| 14 Vinculación de Telegram                | Secuencia           | Los tres                 |
| 15 Cultivo virtual con clima real         | Secuencia           | Los tres                 |
| 16 Aprendizaje continuo                   | Flujo               | Los tres                 |
| 17 Etapas del proyecto                    | Flujo               | Recorrido, ciclo de vida |
| 18 Árbol de problemas                     | Flujo               | Ciclo de vida            |
| 19 Árbol de objetivos                     | Flujo               | Ciclo de vida            |
| 20 Poder e interés de los interesados     | Cuadrantes          | Ciclo de vida            |
| 21 Estructura de desglose del trabajo     | Flujo               | Ciclo de vida            |
| 22 Red de precedencias                    | Flujo               | Ciclo de vida            |
| 23 Ruta crítica                           | Gantt               | Ciclo de vida            |
| 24 Ciclo Scrum                            | Flujo               | Ciclo de vida            |
| 25 Riesgos y su desenlace                 | Flujo               | Ciclo de vida            |
| 26 Contexto del sistema                   | Flujo (C4, nivel 1) | Ciclo de vida            |
| 27 Clases del diseño original             | Clases              | Ciclo de vida            |
| 28 Componentes del diseño original        | Flujo               | Ciclo de vida            |
| 29 Actividad original: enviar un comando  | Actividad           | Ciclo de vida            |
| 30 Secuencia original: datos históricos   | Secuencia           | Ciclo de vida            |
| 31 Modelo de datos original               | Entidad-relación    | Ciclo de vida            |
| 32 Mapa de la PWA                         | Flujo               | Ciclo de vida            |
| 33 Pirámide de pruebas                    | Flujo               | Ciclo de vida            |
| 34 Ciclo PDCA                             | Flujo               | Ciclo de vida            |
| 35 Ciclos de mejora                       | Flujo               | Ciclo de vida            |
| 36 Fases de la investigación              | Flujo               | Ciclo de vida            |
| 37 Avisos de un cultivo                   | Secuencia           | Técnica                  |
| 38 Consejo de lugar                       | Flujo               | Técnica, recorrido       |
| 39 Un actuador como switch                | Flujo de estados    | Técnica                  |
| 40 Paquetes del diseño original           | Paquetes            | Ciclo de vida            |
| 41 Objetos del diseño original            | Objetos             | Ciclo de vida            |
| 42 Artefactos del diseño original         | Despliegue          | Ciclo de vida            |
| 43 Actividad original: datos históricos   | Actividad           | Ciclo de vida            |
| 44 Actividad original: control automático | Actividad           | Ciclo de vida            |
| 45 Cronograma de la investigación         | Gantt               | Ciclo de vida            |

## Diagramas generales

Diagramas independientes, sin límite de tamaño, que muestran la plataforma completa en una sola imagen. No van en ningún
documento: el SVG se abre en el navegador y se amplía tanto como haga falta. Sus nombres empiezan por
`SmartPot_Global_`; los demás son específicos y llevan en el nombre lo que muestran.

| Diagrama general         | Qué muestra                                                                                                                                                                                                                                                                                | Archivos                                                                                                                                                                          |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 01 Arquitectura completa | Personas y dispositivos, borde (UFW y Nginx), los ocho contenedores con sus módulos internos, puertos, redes, volúmenes y servicios externos                                                                                                                                               | [MMD](diagrams/SmartPot_Global_01_Architecture.mmd) · [PNG](diagrams/SmartPot_Global_01_Architecture.png) · [SVG](diagrams/SmartPot_Global_01_Architecture.svg)                   |
| 02 Operación completa    | Secuencia de 16 escenas y más de 150 mensajes numerados: arranque, registro, cultivo real o virtual, conexión, simulación, lectura con automatización, aprendizaje, Telegram, PWA, órdenes, vinculación, desconexión, rotación de la clave, recuperación de la contraseña, borrado y salud | [MMD](diagrams/SmartPot_Global_02_Operation_Sequence.mmd) · [PNG](diagrams/SmartPot_Global_02_Operation_Sequence.png) · [SVG](diagrams/SmartPot_Global_02_Operation_Sequence.svg) |
| 03 Entrega continua      | Del commit al servidor: CI, QA con E2E, imágenes en GHCR y Docker Hub, despliegue central, secretos y entornos (demo, desarrollo, producción y Kubernetes)                                                                                                                                 | [MMD](diagrams/SmartPot_Global_03_Delivery.mmd) · [PNG](diagrams/SmartPot_Global_03_Delivery.png) · [SVG](diagrams/SmartPot_Global_03_Delivery.svg)                               |
| 04 Linaje de los datos   | De dónde sale cada dato, por dónde viaja, dónde se guarda (MongoDB, Redis, SQLite, modelos y navegador) y quién lo usa                                                                                                                                                                     | [MMD](diagrams/SmartPot_Global_04_Data_Lineage.mmd) · [PNG](diagrams/SmartPot_Global_04_Data_Lineage.png) · [SVG](diagrams/SmartPot_Global_04_Data_Lineage.svg)                   |
| 05 Máquinas de estado    | Sesión, dispositivo y su cuenta MQTT, comando, evaluación del cultivo, modo automático, aprendizaje por especie, vínculo de Telegram y simulación de un cultivo virtual                                                                                                                    | [MMD](diagrams/SmartPot_Global_05_State_Machines.mmd) · [PNG](diagrams/SmartPot_Global_05_State_Machines.png) · [SVG](diagrams/SmartPot_Global_05_State_Machines.svg)             |
| 06 Modelo de dominio     | Entidades, enumeraciones e interfaces de la API y el contrato de la IA, con relaciones y cardinalidades                                                                                                                                                                                    | [MMD](diagrams/SmartPot_Global_06_Domain_Model.mmd) · [PNG](diagrams/SmartPot_Global_06_Domain_Model.png) · [SVG](diagrams/SmartPot_Global_06_Domain_Model.svg)                   |
| 07 Recorrido de la PWA   | Cada pantalla, las rutas de la API que llama y el servicio que responde                                                                                                                                                                                                                    | [MMD](diagrams/SmartPot_Global_07_User_Journey.mmd) · [PNG](diagrams/SmartPot_Global_07_User_Journey.png) · [SVG](diagrams/SmartPot_Global_07_User_Journey.svg)                   |
| 08 Decisión de la IA     | De la lectura a la orden: diagnóstico, pronóstico, modelos base y aprendidos, las 21 reglas, índice difuso, agente, consejo de lugar y lo que hace la API                                                                                                                                  | [MMD](diagrams/SmartPot_Global_08_AI_Decision.mmd) · [PNG](diagrams/SmartPot_Global_08_AI_Decision.png) · [SVG](diagrams/SmartPot_Global_08_AI_Decision.svg)                      |

Los diagramas de flujo usan el motor de diseño ELK, que ordena mejor los grafos grandes; como superan los límites por
defecto de Mermaid (50 000 caracteres y 500 aristas), `render_diagrams.py` los reconoce por el nombre y los renderiza
sin esos límites, con el PNG a su tamaño natural.

## Estructura

```text
docs/
├── SmartPot_Technical_Documentation.md   # Fuente
├── SmartPot_Project_Journey.md           # Fuente
├── SmartPot_Software_Lifecycle.md        # Fuente
├── *.docx, *.pdf                         # Generados
├── diagrams/                             # Cada diagrama con su fuente (.mmd), su PNG y su SVG
├── assets/                               # Logo, ícono y marca de agua de la portada
└── tools/
    ├── render_diagrams.py                # .mmd → PNG y SVG y sincronización con el Markdown
    └── md_to_docx.py                     # Markdown → DOCX (y PDF con LibreOffice)
```

## Regenerar

Requisitos: Python 3.11+, Node.js (para `npx @mermaid-js/mermaid-cli`), Google Chrome y LibreOffice.

```bash
python docs/tools/render_diagrams.py --sync-md docs/SmartPot_Technical_Documentation.md docs/SmartPot_Project_Journey.md docs/SmartPot_Software_Lifecycle.md
python docs/tools/md_to_docx.py docs/SmartPot_Technical_Documentation.md --pdf
python docs/tools/md_to_docx.py docs/SmartPot_Project_Journey.md --pdf
python docs/tools/md_to_docx.py docs/SmartPot_Software_Lifecycle.md --pdf
python docs/tools/render_diagrams.py --global   # solo los diagramas generales
```

Para cambiar un diagrama se edita su `.mmd` y se vuelve a ejecutar el primer comando: renderiza las imágenes y copia el
diagrama al bloque ```` ```mermaid ```` que sigue a su marcador `<!-- diagrama: NOMBRE | titulo=... -->` en cada
Markdown. Un diagrama nuevo se agrega con su marcador seguido de un bloque ```` ```mermaid ```` vacío.

## Convenciones del Markdown

| Elemento                                                          | Resultado en el DOCX                                                                 |
|-------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| `<!-- portada ... -->`                                            | Portada a sangre con título, bajada y franja de metadatos                            |
| `<!-- parte: PARTE I \| Título -->`                               | Separador de parte en página nueva                                                   |
| `## 1. Título`                                                    | Sección con la franja "SECCIÓN 01", título y regla verde; entra al índice            |
| `### 1.1 Título`                                                  | Subsección; entra al índice si está numerada                                         |
| `> [!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`, `[!CAUTION]` | Recuadros azul, verde, ámbar y rojo; un `**Título.**` inicial se usa como encabezado |
| `<!-- diagrama: NOMBRE \| titulo=... \| lamina=H -->`             | Figura numerada; `lamina=H` la pone en una página horizontal                         |

## Identidad

Los documentos usan la paleta de la PWA: `leaf-900` `#0B3D2B` en portada y cabeceras de tabla, `leaf-700` `#067A52` en
títulos, `leaf-500` `#00B074` en reglas y acentos, `water` para notas, `sun` para advertencias y `surface` `#F2F7F4`
para las filas alternas. Títulos en Century Gothic (la geométrica más cercana a Outfit que viene con Office), cuerpo en
Segoe UI y código en JetBrains Mono.
