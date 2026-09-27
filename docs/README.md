# Documentación de SmartPot

| Documento | Formato |
| --- | --- |
| Documentación técnica de la plataforma | [Markdown](SmartPot_Documentacion_Tecnica.md) · [DOCX](SmartPot_Documentacion_Tecnica.docx) · [PDF](SmartPot_Documentacion_Tecnica.pdf) |

El Markdown es la fuente: GitHub lo muestra con sus diagramas y de él salen el DOCX y el PDF con la identidad de SmartPot. Cubre la arquitectura, el flujo de una lectura, el contrato MQTT, la API REST, el asistente de IA, el modelo de datos, la PWA, el firmware, la seguridad, el despliegue, la calidad y la operación.

## Estructura

```text
docs/
├── SmartPot_Documentacion_Tecnica.md     # Fuente
├── SmartPot_Documentacion_Tecnica.docx   # Generado
├── SmartPot_Documentacion_Tecnica.pdf    # Generado
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
python docs/tools/render_diagrams.py --sync-md docs/SmartPot_Documentacion_Tecnica.md
python docs/tools/md_to_docx.py docs/SmartPot_Documentacion_Tecnica.md --pdf
```

Para cambiar un diagrama se edita su `.mmd` y se vuelve a ejecutar el primer comando: renderiza las imágenes y copia el diagrama al bloque ```` ```mermaid ```` que sigue a su marcador `<!-- diagrama: NOMBRE | titulo=... -->` en el Markdown.

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
