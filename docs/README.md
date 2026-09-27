# Documentación de SmartPot

| Documento | Qué cuenta | Formato |
| --- | --- | --- |
| Documentación técnica de la plataforma | La plataforma tal como funciona hoy: arquitectura, contratos MQTT y REST, asistente de IA y aprendizaje continuo, Telegram, macetas virtuales, datos, PWA, firmware, seguridad, despliegue, calidad y operación | [Markdown](SmartPot_Documentacion_Tecnica.md) · [DOCX](SmartPot_Documentacion_Tecnica.docx) · [PDF](SmartPot_Documentacion_Tecnica.pdf) |
| Recorrido del proyecto | Cómo se llegó hasta aquí: inicio (problema, objetivos, mercado, interesados y acta), análisis (requisitos con su estado, casos de uso y base de conocimiento), diseño (abstracciones, diagramas y patrones actualizados), construcción (gestión, evolución de la arquitectura, IA, Telegram y simulación) y pruebas | [Markdown](SmartPot_Recorrido_del_Proyecto.md) · [DOCX](SmartPot_Recorrido_del_Proyecto.docx) · [PDF](SmartPot_Recorrido_del_Proyecto.pdf) |

Los Markdown son la fuente: GitHub los muestra con sus diagramas y de ellos salen los DOCX y los PDF con la identidad de SmartPot. El recorrido parte de la documentación de la fase de diseño y la contrasta, requisito por requisito y diagrama por diagrama, con lo que quedó construido.

## Diagramas

| Diagrama | Tipo | Documento |
| --- | --- | --- |
| 01 Arquitectura | Flujo | Técnica |
| 02 Secuencia de una lectura | Secuencia | Técnica |
| 03 Asistente de IA | Flujo | Técnica |
| 04 Modelo de datos | Entidad-relación | Técnica |
| 05 Estados de un comando | Estados | Técnica |
| 06 Despliegue | Flujo | Técnica |
| 07 Redes | Flujo | Técnica |
| 08 QA | Flujo | Técnica |
| 09 Causa y efecto | Flujo | Recorrido |
| 10 Casos de uso | Flujo con actores | Recorrido |
| 11 Clases del dominio | Clases | Recorrido |
| 12 Componentes | Flujo | Recorrido |
| 13 Actividad del control automático | Actividad | Recorrido |
| 14 Vinculación de Telegram | Secuencia | Ambos |
| 15 Maceta virtual con clima real | Secuencia | Ambos |
| 16 Aprendizaje continuo | Flujo | Ambos |
| 17 Etapas del proyecto | Flujo | Recorrido |

## Estructura

```text
docs/
├── SmartPot_Documentacion_Tecnica.md     # Fuente
├── SmartPot_Recorrido_del_Proyecto.md    # Fuente
├── *.docx, *.pdf                         # Generados
├── diagramas/                            # Fuentes Mermaid (.mmd) con la paleta en %%{init}%%
├── imagenes/diagramas/                   # PNG para el DOCX y SVG para ampliar
├── assets/                               # Logo, ícono y marca de agua de la portada
└── tools/
    ├── render_diagrams.py                # .mmd → PNG y SVG, y sincronización con el Markdown
    └── md_to_docx.py                     # Markdown → DOCX (y PDF con LibreOffice)
```

## Regenerar

Requisitos: Python 3.11+, Node.js (para `npx @mermaid-js/mermaid-cli`), Google Chrome y LibreOffice.

```bash
python docs/tools/render_diagrams.py --sync-md docs/SmartPot_Documentacion_Tecnica.md docs/SmartPot_Recorrido_del_Proyecto.md
python docs/tools/md_to_docx.py docs/SmartPot_Documentacion_Tecnica.md --pdf
python docs/tools/md_to_docx.py docs/SmartPot_Recorrido_del_Proyecto.md --pdf
```

Para cambiar un diagrama se edita su `.mmd` y se vuelve a ejecutar el primer comando: renderiza las imágenes y copia el diagrama al bloque ```` ```mermaid ```` que sigue a su marcador `<!-- diagrama: NOMBRE | titulo=... -->` en cada Markdown.

## Convenciones del Markdown

| Elemento | Resultado en el DOCX |
| --- | --- |
| `<!-- portada ... -->` | Portada a sangre con título, bajada y franja de metadatos |
| `<!-- parte: PARTE I \| Título -->` | Separador de parte en página nueva |
| `## 1. Título` | Sección con la franja "SECCIÓN 01", título y regla verde; entra al índice |
| `### 1.1 Título` | Subsección; entra al índice si está numerada |
| `> [!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`, `[!CAUTION]` | Recuadros azul, verde, ámbar y rojo; un `**Título.**` inicial se usa como encabezado |
| `<!-- diagrama: NOMBRE \| titulo=... \| lamina=H -->` | Figura numerada; `lamina=H` la pone en una página horizontal |

## Identidad

Los documentos usan la paleta de la PWA: `leaf-900` `#0B3D2B` en portada y cabeceras de tabla, `leaf-700` `#067A52` en títulos, `leaf-500` `#00B074` en reglas y acentos, `water` para notas, `sun` para advertencias y `surface` `#F2F7F4` para las filas alternas. Títulos en Century Gothic (la geométrica más cercana a Outfit que viene con Office), cuerpo en Segoe UI y código en JetBrains Mono.
