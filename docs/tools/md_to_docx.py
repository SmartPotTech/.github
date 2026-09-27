#!/usr/bin/env python3
"""Convierte un Markdown de `docs/` en un DOCX con la identidad de SmartPot y, opcionalmente, en PDF.

    python docs/tools/md_to_docx.py docs/SmartPot_Technical_Documentation.md --pdf

El DOCX se arma desde cero (estilos, portada, encabezado, pie y piezas de marca de
`docs/assets`), sin plantillas externas. Del Markdown entiende el subconjunto que usa la
documentación de SmartPot:

* `<!-- portada ... -->` con `clave: valor` para la portada.
* `<!-- parte: PARTE I | Título -->` para los separadores de parte, que abren página nueva.
* `## 1. Título` (sección con franja "SECCIÓN 01"), `###` y `####`.
* Párrafos con **negrita**, *itálica*, `código` y [enlaces](url); listas con `-` o `1.`.
* Tablas, bloques de código y recuadros `> [!NOTE|TIP|IMPORTANT|WARNING|CAUTION]`.
* `<!-- diagrama: NOMBRE | titulo=... -->` seguido del bloque mermaid: se inserta
  `images/diagrams/NOMBRE.png` (ver `render_diagrams.py`).

El PDF se genera con LibreOffice.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import zipfile

DOCS = pathlib.Path(__file__).resolve().parent.parent
ASSETS = DOCS / "assets"
DIAGRAMS = DOCS / "images" / "diagrams"
SOFFICE_CANDIDATES = (
    "C:/Program Files/LibreOffice/program/soffice.exe",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/usr/bin/soffice",
    "/usr/bin/libreoffice",
)

# Paleta SmartPot (la misma de la PWA).
LEAF_950, LEAF_900, LEAF_800, LEAF_700, LEAF_600 = "06281C", "0B3D2B", "0A5A3C", "067A52", "009A64"
LEAF_500, LEAF_300, LEAF_100, LEAF_50 = "00B074", "7FDBB0", "DDF5EA", "EEFAF4"
WATER_700, WATER_100 = "1F6FA0", "E3F2FB"
SUN_600, SUN_500, SUN_100 = "C98D12", "F2B632", "FDF4DD"
CLAY_600 = "B85A38"
DANGER_600, DANGER_100 = "B83232", "FBE4E4"
INK, MUTED, LINE, SURFACE, PAGE = "17261F", "5B6B63", "D5E3DC", "F2F7F4", "F7FAF8"

CALLOUTS = {
    "NOTE": (WATER_100, WATER_700, WATER_700, "Nota"),
    "TIP": (LEAF_50, LEAF_500, LEAF_700, "Buena práctica"),
    "IMPORTANT": (SUN_100, SUN_500, CLAY_600, "Importante"),
    "WARNING": (SUN_100, SUN_500, CLAY_600, "Atención"),
    "CAUTION": (DANGER_100, DANGER_600, DANGER_600, "Precaución"),
}

# Carta: 12240 × 15840 twips con márgenes de 1".
PAGE_W, PAGE_H = 12240, 15840
MARGIN_TOP, MARGIN_SIDE, MARGIN_BOTTOM = 1700, 1440, 1440
BODY_W = PAGE_W - 2 * MARGIN_SIDE
MAX_FIGURE_H = 11200
LANDSCAPE_BODY_W = PAGE_H - 2 * MARGIN_SIDE
LANDSCAPE_FIGURE_H = PAGE_W - MARGIN_TOP - MARGIN_BOTTOM - 900
EMU = 635  # EMU por twip

DISPLAY = "Century Gothic"
BODY = "Segoe UI"
MONO = "JetBrains Mono"

NS = (
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"'
)


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def fonts(name: str) -> str:
    return f'<w:rFonts w:ascii="{name}" w:hAnsi="{name}" w:eastAsia="{name}" w:cs="{name}"/>'


def png_size(path: pathlib.Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    return struct.unpack(">II", header[16:24])


class Document:
    """Acumula el cuerpo, las relaciones y los medios del DOCX."""

    def __init__(self) -> None:
        self.body: list[str] = []
        self.media: dict[str, pathlib.Path] = {}
        self.rels: list[tuple[str, str, str, bool]] = []
        self.header_rels: list[tuple[str, str, str, bool]] = []
        self.ids = 100
        self.figures = 0
        self.bookmarks: list[tuple[int, str, str]] = []
        self.body_sections = 0

    def next_id(self) -> int:
        self.ids += 1
        return self.ids

    def image(self, path: pathlib.Path, header: bool = False) -> str:
        name = f"image{len(self.media) + 1}{path.suffix}"
        self.media[name] = path
        rels = self.header_rels if header else self.rels
        rid = f"rIdImg{len(self.media)}"
        rels.append((rid, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                     f"media/{name}", False))
        return rid

    def link(self, url: str) -> str:
        rid = f"rIdLink{len(self.rels) + 1}"
        self.rels.append((rid, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                          url, True))
        return rid


# ---------------------------------------------------------------- texto


def run(text: str, *, size: int = 20, color: str = INK, bold: bool = False, italic: bool = False,
        font: str | None = None, caps: bool = False, spacing: int = 0, underline: bool = False) -> str:
    props = [fonts(font) if font else ""]
    if bold:
        props.append("<w:b/><w:bCs/>")
    if italic:
        props.append("<w:i/><w:iCs/>")
    if caps:
        props.append("<w:caps/>")
    props.append(f'<w:color w:val="{color}"/>')
    if spacing:
        props.append(f'<w:spacing w:val="{spacing}"/>')
    props.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    if underline:
        props.append('<w:u w:val="single"/>')
    return f'<w:r><w:rPr>{"".join(props)}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|(?<![\w*])\*[^*\s][^*]*\*(?![\w*]))")


def inline(doc: Document, text: str, *, size: int = 20, color: str = INK, bold: bool = False) -> str:
    out = []
    for piece in INLINE.split(text):
        if not piece:
            continue
        if piece.startswith("**") and piece.endswith("**") and len(piece) > 4:
            out.append(inline(doc, piece[2:-2], size=size, color=color, bold=True))
        elif piece.startswith("`") and piece.endswith("`"):
            out.append(run(piece[1:-1], size=max(size - 2, 14), color=LEAF_800, font=MONO, bold=bold))
        elif piece.startswith("[") and "](" in piece:
            label, url = piece[1:piece.index("](")], piece[piece.index("](") + 2:-1]
            if url.startswith("http"):
                rid = doc.link(url)
                out.append(f'<w:hyperlink r:id="{rid}">'
                           f'{run(label, size=size, color=WATER_700, bold=bold, underline=True)}</w:hyperlink>')
            else:
                out.append(run(label, size=size, color=WATER_700, bold=bold))
        elif piece.startswith("*") and piece.endswith("*") and len(piece) > 2:
            out.append(run(piece[1:-1], size=size, color=color, italic=True, bold=bold))
        else:
            out.append(run(piece, size=size, color=color, bold=bold))
    return "".join(out)


def plain(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.replace("**", "").replace("`", "")


def paragraph(content: str, *, style: str | None = None, before: int = 0, after: int = 120, line: int = 288,
              align: str | None = None, keep_next: bool = False, extra: str = "") -> str:
    props = []
    if style:
        props.append(f'<w:pStyle w:val="{style}"/>')
    if keep_next:
        props.append("<w:keepNext/>")
    props.append(extra)
    props.append(f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="auto"/>')
    if align:
        props.append(f'<w:jc w:val="{align}"/>')
    return f'<w:p><w:pPr>{"".join(props)}</w:pPr>{content}</w:p>'


def spacer(size: int = 120, keep_next: bool = False) -> str:
    keep = "<w:keepNext/>" if keep_next else ""
    return (f'<w:p><w:pPr>{keep}<w:spacing w:before="{size}" w:after="0" w:line="240" w:lineRule="auto"/>'
            f'<w:rPr><w:sz w:val="8"/></w:rPr></w:pPr></w:p>')


def drawing(rid: str, cx: int, cy: int, pid: int, name: str) -> str:
    return (
        f'<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{pid}" name="{esc(name)}"/>'
        f'<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{pid}" name="{esc(name)}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
        f'</wp:inline></w:drawing>'
    )


def anchored(rid: str, cx: int, cy: int, x: int, y: int, pid: int, name: str) -> str:
    # behindDoc="0": LibreOffice no dibuja las imágenes "detrás del texto" al exportar a PDF.
    return (
        f'<w:drawing><wp:anchor distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="1" '
        f'behindDoc="0" locked="0" layoutInCell="0" allowOverlap="1"><wp:simplePos x="0" y="0"/>'
        f'<wp:positionH relativeFrom="page"><wp:posOffset>{x}</wp:posOffset></wp:positionH>'
        f'<wp:positionV relativeFrom="page"><wp:posOffset>{y}</wp:posOffset></wp:positionV>'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:wrapNone/>'
        f'<wp:docPr id="{pid}" name="{esc(name)}"/><wp:cNvGraphicFramePr>'
        f'<a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{pid}" name="{esc(name)}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
        f'</wp:anchor></w:drawing>'
    )


def no_borders() -> str:
    return ('<w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/>'
            '<w:right w:val="nil"/><w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders>')


def box(width: int, fill: str, content: str, *, left_bar: str | None = None, margins=(140, 220, 140, 220),
        top_rule: str | None = None, height: int | None = None, v_align: str = "top", indent: int = 0) -> str:
    """Tabla de una sola celda: recuadros, banners y franjas."""
    top, right, bottom, left = margins
    borders = ""
    if left_bar or top_rule:
        borders = "<w:tcBorders>"
        if top_rule:
            borders += f'<w:top w:val="single" w:sz="18" w:space="0" w:color="{top_rule}"/>'
        if left_bar:
            borders += f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{left_bar}"/>'
        borders += "</w:tcBorders>"
    row_props = "<w:cantSplit/>" + (f'<w:trHeight w:val="{height}" w:hRule="exact"/>' if height else "")
    return (
        f'<w:tbl><w:tblPr><w:tblW w:w="{width}" w:type="dxa"/><w:tblInd w:w="{indent}" w:type="dxa"/>'
        f'{no_borders()}<w:tblLayout w:type="fixed"/>'
        f'<w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar>'
        f'<w:tblLook w:val="0000" w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" '
        f'w:noHBand="1" w:noVBand="1"/></w:tblPr><w:tblGrid><w:gridCol w:w="{width}"/></w:tblGrid>'
        f'<w:tr><w:trPr>{row_props}</w:trPr><w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{borders}'
        f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
        f'<w:tcMar><w:top w:w="{top}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>'
        f'<w:vAlign w:val="{v_align}"/></w:tcPr>{content}</w:tc></w:tr></w:tbl>'
    )


# ---------------------------------------------------------------- bloques


def cover(doc: Document, meta: dict[str, str]) -> str:
    logo = ASSETS / "logo-horizontal-white.png"
    lw, lh = png_size(logo)
    logo_w = 3000000
    logo_run = f"<w:r>{drawing(doc.image(logo), logo_w, int(logo_w * lh / lw), doc.next_id(), 'Logo')}</w:r>"
    mark = ASSETS / "watermark.png"
    mw, mh = png_size(mark)
    mark_w = 4300000
    mark_run = (f"<w:r>{anchored(doc.image(mark), mark_w, int(mark_w * mh / mw), 4050000, 2350000, doc.next_id(), 'Marca')}"
                "</w:r>")

    title = meta.get("titulo", "SmartPot")
    accent = meta.get("acento", "")
    if accent and title.endswith(accent):
        title_runs = (run(title[: -len(accent)], size=68, color="FFFFFF", bold=True, font=DISPLAY)
                      + run(accent, size=68, color=LEAF_500, bold=True, font=DISPLAY))
    else:
        title_runs = run(title, size=68, color="FFFFFF", bold=True, font=DISPLAY)

    content = (
        paragraph(logo_run + mark_run, after=2600)
        + paragraph(run(meta.get("eyebrow", ""), size=17, color=SUN_500, bold=True, caps=True, spacing=50), after=160)
        + paragraph(title_runs, after=120, line=240)
        + paragraph(run(meta.get("subtitulo", ""), size=32, color=LEAF_100, italic=True, font=DISPLAY), after=360,
                    line=264)
        # Ancho restringido con sangría: una tabla anidada en una fila de alto fijo se rompe al renderizar.
        + paragraph(run(meta.get("bajada", ""), size=21, color=LEAF_300), after=0, line=300,
                    extra='<w:ind w:right="3900"/>')
    )
    hero = box(PAGE_W, LEAF_900, content, margins=(1500, 1180, 0, 1180), height=13300)

    labels = ["DOCUMENTO", "VERSIÓN", "EQUIPO", "PROYECTO"]
    values = [meta.get("documento", ""), meta.get("version", ""), meta.get("equipo", ""), meta.get("proyecto", "")]
    tabs = '<w:tabs><w:tab w:val="left" w:pos="2700"/><w:tab w:val="left" w:pos="5000"/><w:tab w:val="left" w:pos="7300"/></w:tabs>'
    label_runs = "".join((run("\t", size=15) if i else "") + run(l, size=15, color=LEAF_300, bold=True, spacing=30)
                         for i, l in enumerate(labels))
    value_runs = "".join((run("\t", size=19) if i else "") + run(v, size=19, color="FFFFFF", bold=True)
                         for i, v in enumerate(values))
    strip_content = (paragraph(label_runs, after=60, line=240, extra=tabs)
                     + paragraph(value_runs, after=0, line=240, extra=tabs))
    strip = box(PAGE_W, LEAF_950, strip_content, margins=(0, 1180, 0, 1180), top_rule=LEAF_500,
                height=PAGE_H - 13300, v_align="center")

    section = (
        '<w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:rPr><w:sz w:val="2"/></w:rPr>'
        f'<w:sectPr><w:pgSz w:w="{PAGE_W}" w:h="{PAGE_H}"/>'
        '<w:pgMar w:top="0" w:right="0" w:bottom="0" w:left="0" w:header="0" w:footer="0" w:gutter="0"/>'
        '<w:cols w:space="720"/></w:sectPr></w:pPr></w:p>'
    )
    return hero + strip + section


def section_properties(doc: Document, landscape: bool) -> str:
    """Página del cuerpo: carta vertical u horizontal, con encabezado y pie."""
    width, height = (PAGE_H, PAGE_W) if landscape else (PAGE_W, PAGE_H)
    orient = ' w:orient="landscape"' if landscape else ""
    # La numeración arranca en 2 en la primera sección del cuerpo: la portada es la página 1.
    numbering = '<w:pgNumType w:start="2"/>' if doc.body_sections == 0 else ""
    doc.body_sections += 1
    return ('<w:sectPr><w:headerReference w:type="default" r:id="rIdHeader"/>'
            '<w:footerReference w:type="default" r:id="rIdFooter"/>'
            f'<w:pgSz w:w="{width}" w:h="{height}"{orient}/>'
            f'<w:pgMar w:top="{MARGIN_TOP}" w:right="{MARGIN_SIDE}" w:bottom="{MARGIN_BOTTOM}" '
            f'w:left="{MARGIN_SIDE}" w:header="700" w:footer="620" w:gutter="0"/>{numbering}'
            '<w:cols w:space="720"/></w:sectPr>')


def section_break(doc: Document, landscape: bool) -> str:
    return ('<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
            f'<w:rPr><w:sz w:val="2"/></w:rPr>{section_properties(doc, landscape)}</w:pPr></w:p>')


def part_banner(label: str, title: str) -> str:
    content = (paragraph(run(label, size=17, color=SUN_500, bold=True, caps=True, spacing=60), after=80)
               + paragraph(run(title, size=44, color="FFFFFF", bold=True, font=DISPLAY), after=0, line=240))
    return (
        '<w:p><w:pPr><w:pageBreakBefore/><w:spacing w:before="0" w:after="0" w:line="20" w:lineRule="exact"/>'
        '<w:rPr><w:sz w:val="2"/></w:rPr></w:pPr></w:p>'
        + box(BODY_W, LEAF_900, content, margins=(420, 480, 420, 480))
        + spacer(240)
    )


def heading(doc: Document, level: int, text: str) -> str:
    bookmark_id = doc.next_id()
    name = f"sec_{bookmark_id}"
    match = re.match(r"^(\d+)\.\s+(.*)$", text)
    body = ""
    if level == 1:
        doc.bookmarks.append((1, name, text))
        eyebrow = f"SECCIÓN {int(match.group(1)):02d}" if match else "DOCUMENTO"
        body += paragraph(run(eyebrow, size=16, color=LEAF_600, bold=True, spacing=60), before=360, after=40,
                          keep_next=True)
        title = match.group(2) if match else text
        style = "Heading1"
    elif level == 2:
        doc.bookmarks.append((2, name, text))
        title, style = text, "Heading2"
    else:
        title, style = text, "Heading3"
    content = (f'<w:bookmarkStart w:id="{bookmark_id}" w:name="{name}"/>'
               f'{inline(doc, title, size={1: 34, 2: 25, 3: 21}[level], color={1: LEAF_900, 2: LEAF_700, 3: LEAF_700}[level], bold=True)}'
               f'<w:bookmarkEnd w:id="{bookmark_id}"/>')
    return body + f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>{content}</w:p>'


def column_widths(rows: list[list[str]]) -> list[int]:
    """Anchos en twips: ninguna columna parte una palabra y el resto se reparte según el contenido."""
    padding, char, mono_char, header_char = 240, 92, 102, 120
    minimums, naturals = [], []
    for c in range(len(rows[0])):
        header_words = plain(rows[0][c]).split() or [""]
        body = [plain(r[c]) for r in rows[1:]] or [""]
        # El código usa letra monoespaciada, más ancha que la del cuerpo.
        widest = max((len(w) * (mono_char if r[c].strip().startswith('`') else char)
                      for r in rows[1:] for w in plain(r[c]).split()), default=char)
        minimum = max(max(len(w) for w in header_words) * header_char, widest) + padding
        minimums.append(min(minimum, int(BODY_W * 0.4)))
        naturals.append(max(minimums[-1], min(max(len(t) for t in body) * char + padding, BODY_W)))
    if sum(naturals) <= BODY_W:
        base, extra = naturals, [n for n in naturals]
    else:
        base, extra = minimums, [n - m for n, m in zip(naturals, minimums)]
    free = BODY_W - sum(base)
    if free < 0:
        widths = [int(m * BODY_W / sum(base)) for m in base]
    else:
        weight = sum(extra) or 1
        widths = [int(b + free * e / weight) for b, e in zip(base, extra)]
    widths[-1] += BODY_W - sum(widths)
    return widths


def table(doc: Document, rows: list[list[str]]) -> str:
    columns = max(len(r) for r in rows)
    rows = [r + [""] * (columns - len(r)) for r in rows]
    widths = column_widths(rows)

    border = (f'<w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="{LINE}"/>'
              f'<w:left w:val="single" w:sz="4" w:space="0" w:color="{LINE}"/>'
              f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="{LINE}"/>'
              f'<w:right w:val="single" w:sz="4" w:space="0" w:color="{LINE}"/>'
              f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{LINE}"/>'
              f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="{LINE}"/></w:tblBorders>')
    xml = [f'<w:tbl><w:tblPr><w:tblW w:w="{BODY_W}" w:type="dxa"/>{border}<w:tblLayout w:type="fixed"/>'
           '<w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar>'
           '<w:tblLook w:val="04A0" w:firstRow="1" w:firstColumn="1" w:noVBand="1"/></w:tblPr><w:tblGrid>'
           + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>"]
    for index, row in enumerate(rows):
        header = index == 0
        fill = LEAF_900 if header else (SURFACE if index % 2 == 0 else "FFFFFF")
        xml.append("<w:tr><w:trPr><w:cantSplit/>" + ("<w:tblHeader/>" if header else "") + "</w:trPr>")
        for c, cell in enumerate(row):
            if header:
                content = run(plain(cell).upper(), size=16, color="FFFFFF", bold=True, spacing=10)
            else:
                content = inline(doc, cell, size=17, color=LEAF_800 if c == 0 else INK, bold=c == 0 and columns > 1)
            xml.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[c]}" w:type="dxa"/>'
                       f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
                       '<w:tcMar><w:top w:w="70" w:type="dxa"/><w:left w:w="110" w:type="dxa"/>'
                       '<w:bottom w:w="70" w:type="dxa"/><w:right w:w="110" w:type="dxa"/></w:tcMar>'
                       '<w:vAlign w:val="center"/></w:tcPr>'
                       f'{paragraph(content, after=0, line=252)}</w:tc>')
        xml.append("</w:tr>")
    xml.append("</w:tbl>")
    # El espacio previo se mantiene con la tabla para que un título no quede solo al pie de la página.
    return spacer(60, keep_next=True) + "".join(xml) + spacer(160)


def callout(doc: Document, kind: str, lines: list[str]) -> str:
    fill, bar, title_color, default_title = CALLOUTS.get(kind, CALLOUTS["NOTE"])
    # Una línea vacía separa párrafos y las líneas con guion son viñetas dentro del recuadro.
    parts, current = [], []
    for line in (line.strip() for line in lines):
        item = re.match(r"^[-*]\s+(.*)$", line)
        if not line or item:
            if current:
                parts.append(("p", " ".join(current)))
                current = []
            if item:
                parts.append(("li", item.group(1)))
            continue
        current.append(line)
    if current:
        parts.append(("p", " ".join(current)))
    title = default_title
    if parts and parts[0][0] == "p" and (match := re.match(r"^\*\*(.+?)\.\*\*\s*(.*)$", parts[0][1])):
        title, parts[0] = match.group(1), ("p", match.group(2))
    parts = [part for part in parts if part[1]]
    content = paragraph(run(title.upper(), size=15, color=title_color, bold=True, spacing=40), after=60, line=240)
    for index, (part, text) in enumerate(parts):
        after = 0 if index == len(parts) - 1 else (40 if part == "li" else 100)
        if part == "li":
            content += paragraph(run("•", size=18, color=bar, bold=True) + "<w:r><w:tab/></w:r>" + inline(doc, text, size=18),
                                 after=after, line=276, extra='<w:ind w:left="300" w:hanging="220"/>')
        else:
            content += paragraph(inline(doc, text, size=18), after=after, line=276)
    return spacer(80) + box(BODY_W, fill, content, left_bar=bar) + spacer(160)


def code_block(language: str, lines: list[str]) -> str:
    label = (language or "texto").upper()
    bar = box(BODY_W, LEAF_900, paragraph(run(label, size=14, color=LEAF_300, bold=True, spacing=40), after=0,
                                          line=240), margins=(60, 200, 60, 200))
    body_lines = "".join(paragraph(run(line or " ", size=16, color=INK, font=MONO), after=0, line=252)
                         for line in lines)
    body = box(BODY_W, PAGE, body_lines, margins=(120, 200, 120, 200))
    return spacer(80) + bar + body + spacer(160)


def figure(doc: Document, name: str, title: str, landscape: bool = False, lead: str = "",
           continued: bool = False) -> str:
    path = DIAGRAMS / f"{name}.png"
    if not path.exists():
        print(f"  Falta la imagen {path.name}: ejecuta render_diagrams.py")
        return ""
    doc.figures += 1
    width, height = png_size(path)
    max_w, max_h = (LANDSCAPE_BODY_W, LANDSCAPE_FIGURE_H) if landscape else (BODY_W, MAX_FIGURE_H)
    if lead:
        max_h -= 1400
    cx = max_w * EMU
    cy = int(cx * height / width)
    if cy > max_h * EMU:
        cy = max_h * EMU
        cx = int(cy * width / height)
    image = f"<w:r>{drawing(doc.image(path), cx, cy, doc.next_id(), name)}</w:r>"
    caption = (run(f"Figura {doc.figures}", size=16, color=LEAF_700, bold=True)
               + run(f"  ·  {title}", size=16, color=MUTED, italic=True))
    if not landscape:
        return (paragraph(image, before=120, after=60, align="center", keep_next=True)
                + paragraph(caption, after=240, align="center"))
    # La lámina es una sección propia en carta horizontal: se cierra la sección vertical anterior
    # (salvo que la anterior también sea una lámina) y la lámina termina con su propia definición de página.
    return (("" if continued else section_break(doc, landscape=False)) + lead
            + paragraph(image, before=0, after=60, align="center", keep_next=True)
            + paragraph(caption, after=0, align="center")
            + section_break(doc, landscape=True))


def bullet(doc: Document, text: str, numbered: bool) -> str:
    num = 2 if numbered else 1
    return paragraph(inline(doc, text), after=60, line=276,
                     extra=f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num}"/></w:numPr>'
                           '<w:ind w:left="360" w:hanging="260"/>')


def toc(doc: Document) -> str:
    items = [paragraph(run("CONTENIDO", size=16, color=LEAF_600, bold=True, spacing=60), before=360, after=40),
             f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>{run("Contenido", size=34, color=LEAF_900, bold=True)}</w:p>']
    for level, name, text in doc.bookmarks:
        if not re.match(r"^\d+(\.\d+)*\.?\s", text):
            continue
        size, color, indent = (21, LEAF_900, 0) if level == 1 else (18, INK, 420)
        link = (f'<w:hyperlink w:anchor="{name}" w:history="1">'
                f'{run(plain(text), size=size, color=color, bold=level == 1)}</w:hyperlink>')
        items.append(paragraph(link, before=100 if level == 1 else 0, after=30, line=252,
                               extra=f'<w:ind w:left="{indent}"/>'))
    return "".join(items)


# ---------------------------------------------------------------- lectura del Markdown

TABLE_SEPARATOR = re.compile(r"^\|?\s*:?-{3,}")
DIAGRAM = re.compile(r"<!--\s*diagrama:\s*([\w.-]+)(.*?)-->")
PART = re.compile(r"<!--\s*parte:\s*([^|]+)\|\s*(.*?)\s*-->")


def parse_cover(text: str) -> tuple[dict[str, str], str]:
    match = re.search(r"<!--\s*portada\s*\n(.*?)-->", text, re.S)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta, text[: match.start()] + text[match.end():]


def split_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [cell.strip() for cell in cells]


def convert(doc: Document, text: str) -> tuple[list[str], str]:
    blocks: list[str] = []
    lines = text.splitlines()
    title = "SmartPot"
    toc_index = None
    # Índices del último título y de la última lámina para encadenar láminas horizontales.
    last_heading = last_landscape = -1
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if part := PART.match(stripped):
            if toc_index is None:
                toc_index = len(blocks)
            blocks.append(part_banner(part.group(1).strip(), part.group(2).strip()))
            i += 1
            continue
        if diagram := DIAGRAM.match(stripped):
            options = dict(part.split("=", 1) for part in (p.strip() for p in diagram.group(2).split("|")) if "=" in part)
            landscape = options.get("lamina", "").upper() == "H"
            # El título justo anterior viaja con la lámina y dos láminas seguidas no dejan una página vacía.
            lead = blocks.pop() if landscape and blocks and last_heading == len(blocks) - 1 else ""
            continued = landscape and blocks and last_landscape == len(blocks) - 1
            blocks.append(figure(doc, diagram.group(1), options.get("titulo", diagram.group(1)).strip(),
                                 landscape=landscape, lead=lead, continued=bool(continued)))
            last_heading = -1
            if landscape:
                last_landscape = len(blocks) - 1
            i += 1
            if i < len(lines) and lines[i].startswith("```"):
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    i += 1
                i += 1
            continue
        if stripped.startswith("<!--"):
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        if stripped.startswith("```"):
            language = stripped[3:].strip()
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i].rstrip())
                i += 1
            i += 1
            blocks.append(code_block(language, code))
            continue
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            i += 1
            continue
        if heading_match := re.match(r"^(#{2,4})\s+(.*)$", stripped):
            blocks.append(heading(doc, len(heading_match.group(1)) - 1, heading_match.group(2).strip()))
            last_heading = len(blocks) - 1
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and TABLE_SEPARATOR.match(lines[i + 1].strip()):
            rows = [split_row(stripped)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            blocks.append(table(doc, rows))
            continue
        if stripped.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            kind = "NOTE"
            if quote and (alert := re.match(r"^\[!(\w+)\]$", quote[0])):
                kind = alert.group(1).upper()
                quote = quote[1:]
            blocks.append(callout(doc, kind, quote))
            continue
        if re.match(r"^[-*]\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
            numbered = bool(re.match(r"^\d+\.\s+", stripped))
            while i < len(lines) and (re.match(r"^\s*[-*]\s+", lines[i]) or re.match(r"^\s*\d+\.\s+", lines[i])):
                item = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", lines[i])
                blocks.append(bullet(doc, item, numbered))
                i += 1
            blocks.append(spacer(40))
            continue
        text_lines = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||>|```|<!--|[-*]\s|\d+\.\s)",
                                                                     lines[i].strip()):
            text_lines.append(lines[i].strip())
            i += 1
        blocks.append(paragraph(inline(doc, " ".join(text_lines)), after=140, line=288))
    if toc_index is not None:
        blocks.insert(toc_index, toc(doc))
    return blocks, title


# ---------------------------------------------------------------- partes del paquete


def styles_xml() -> str:
    def heading_style(style_id: str, name: str, level: int, size: int, color: str, font: str, before: int,
                      after: int, rule: bool) -> str:
        border = (f'<w:pBdr><w:bottom w:val="single" w:sz="12" w:space="6" w:color="{LEAF_500}"/></w:pBdr>'
                  if rule else "")
        return (f'<w:style w:type="paragraph" w:styleId="{style_id}"><w:name w:val="{name}"/>'
                f'<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
                f'<w:pPr><w:keepNext/><w:keepLines/>{border}'
                f'<w:spacing w:before="{before}" w:after="{after}" w:line="240" w:lineRule="auto"/>'
                f'<w:outlineLvl w:val="{level}"/></w:pPr>'
                f'<w:rPr>{fonts(font)}<w:b/><w:bCs/><w:color w:val="{color}"/>'
                f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr></w:style>')

    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {NS}>'
        f'<w:docDefaults><w:rPrDefault><w:rPr>{fonts(BODY)}<w:color w:val="{INK}"/>'
        '<w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="es-CO" w:eastAsia="es-CO" w:bidi="ar-SA"/></w:rPr>'
        '</w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="288" w:lineRule="auto"/></w:pPr>'
        '</w:pPrDefault></w:docDefaults>'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
        + heading_style("Heading1", "heading 1", 0, 34, LEAF_900, DISPLAY, 0, 200, True)
        + heading_style("Heading2", "heading 2", 1, 25, LEAF_700, DISPLAY, 280, 100, False)
        + heading_style("Heading3", "heading 3", 2, 21, LEAF_700, BODY, 200, 80, False)
        + '<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/>'
        '<w:tblPr><w:tblInd w:w="0" w:type="dxa"/><w:tblCellMar><w:top w:w="0" w:type="dxa"/>'
        '<w:left w:w="108" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/>'
        '</w:tblCellMar></w:tblPr></w:style>'
        '<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/>'
        f'<w:rPr><w:color w:val="{WATER_700}"/><w:u w:val="single"/></w:rPr></w:style>'
        '</w:styles>'
    )


def numbering_xml() -> str:
    def abstract(aid: int, fmt: str, text: str) -> str:
        return (f'<w:abstractNum w:abstractNumId="{aid}"><w:multiLevelType w:val="singleLevel"/>'
                f'<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/><w:lvlText w:val="{text}"/>'
                '<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="360" w:hanging="260"/></w:pPr>'
                f'<w:rPr><w:color w:val="{LEAF_500}"/><w:b/></w:rPr></w:lvl></w:abstractNum>')

    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering {NS}>'
            + abstract(1, "bullet", "•") + abstract(2, "decimal", "%1.")
            + '<w:num w:numId="1"><w:abstractNumId w:val="1"/></w:num>'
            '<w:num w:numId="2"><w:abstractNumId w:val="2"/></w:num></w:numbering>')


def header_xml(doc: Document, descriptor: str) -> str:
    icon = ASSETS / "icon.png"
    rid = doc.image(icon, header=True)
    size = 180000
    left = (f"<w:r>{drawing(rid, size, size, doc.next_id(), 'Icono')}</w:r>"
            + run("  SMARTPOT", size=15, color=LEAF_900, bold=True, spacing=40)
            + run("  ·  PLATAFORMA", size=15, color=LEAF_600, bold=True, spacing=40))
    right = run(descriptor.upper(), size=14, color=MUTED, bold=True, spacing=30)
    cells = "".join(
        f'<w:tc><w:tcPr><w:tcW w:w="{BODY_W // 2}" w:type="dxa"/>'
        f'<w:tcBorders><w:bottom w:val="single" w:sz="4" w:space="0" w:color="{LINE}"/></w:tcBorders>'
        f'<w:tcMar><w:bottom w:w="80" w:type="dxa"/></w:tcMar><w:vAlign w:val="center"/></w:tcPr>'
        f'{paragraph(content, after=0, line=240, align=align)}</w:tc>'
        for content, align in ((left, "left"), (right, "right")))
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr {NS}>'
            f'<w:tbl><w:tblPr><w:tblW w:w="{BODY_W}" w:type="dxa"/>{no_borders()}<w:tblLayout w:type="fixed"/>'
            '<w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar>'
            f'</w:tblPr><w:tblGrid><w:gridCol w:w="{BODY_W // 2}"/><w:gridCol w:w="{BODY_W // 2}"/></w:tblGrid>'
            f'<w:tr>{cells}</w:tr></w:tbl>{paragraph("", after=0, line=240)}</w:hdr>')


def footer_xml() -> str:
    tabs = f'<w:tabs><w:tab w:val="right" w:pos="{BODY_W}"/></w:tabs>'
    content = (run("SmartPotTech · smartpot.app", size=15, color=MUTED)
               + run("\tPágina ", size=15, color=MUTED)
               + '<w:fldSimple w:instr=" PAGE "><w:r><w:rPr><w:b/><w:color w:val="'
               + LEAF_700 + '"/><w:sz w:val="15"/></w:rPr><w:t>1</w:t></w:r></w:fldSimple>')
    border = f'<w:pBdr><w:top w:val="single" w:sz="4" w:space="6" w:color="{LINE}"/></w:pBdr>'
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {NS}>'
            f'{paragraph(content, after=0, line=240, extra=border + tabs)}</w:ftr>')


def font_table() -> str:
    def font(name: str, alt: str, family: str, pitch: str = "variable") -> str:
        return (f'<w:font w:name="{name}"><w:altName w:val="{alt}"/><w:charset w:val="00"/>'
                f'<w:family w:val="{family}"/><w:pitch w:val="{pitch}"/></w:font>')

    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:fonts {NS}>'
            + font(DISPLAY, "Arial", "swiss") + font(BODY, "Arial", "swiss")
            + font(MONO, "Consolas", "modern", "fixed") + "</w:fonts>")


def rels_xml(rels: list[tuple[str, str, str, bool]]) -> str:
    items = "".join(
        f'<Relationship Id="{rid}" Type="{kind}" Target="{esc(target)}"'
        + (' TargetMode="External"' if external else "") + "/>"
        for rid, kind, target, external in rels)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{items}</Relationships>')


def build(markdown: pathlib.Path, output: pathlib.Path) -> None:
    text = markdown.read_text(encoding="utf-8")
    meta, text = parse_cover(text)
    doc = Document()
    cover_xml = cover(doc, meta)
    blocks, title = convert(doc, text)
    descriptor = f"{meta.get('documento', title)} · v{meta.get('version', '1.0').split(' ')[0]}"
    header = header_xml(doc, descriptor)

    doc.rels += [
        ("rIdStyles", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles", "styles.xml", False),
        ("rIdNumbering", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering",
         "numbering.xml", False),
        ("rIdSettings", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings",
         "settings.xml", False),
        ("rIdFonts", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable",
         "fontTable.xml", False),
        ("rIdHeader", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header", "header1.xml",
         False),
        ("rIdFooter", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer", "footer1.xml",
         False),
    ]
    body_section = section_properties(doc, landscape=False)
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>'
                f'{cover_xml}{"".join(blocks)}{body_section}</w:body></w:document>')

    settings = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings {NS}>'
                '<w:defaultTabStop w:val="720"/><w:characterSpacingControl w:val="doNotCompress"/>'
                '<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word"'
                ' w:val="15"/></w:compat></w:settings>')
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{esc(title)}</dc:title><dc:subject>{esc(meta.get("subtitulo", ""))}</dc:subject>'
            '<dc:creator>SmartPotTech</dc:creator><dc:language>es-CO</dc:language>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>')
    app = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
           '<Application>SmartPot docs</Application><Company>SmartPotTech</Company></Properties>')
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
        '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
        '<Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/>'
        '<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
        '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        '</Types>')
    package_rels = rels_xml([
        ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
         "word/document.xml", False),
        ("rId2", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
         "docProps/core.xml", False),
        ("rId3", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties",
         "docProps/app.xml", False),
    ])

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", content_types)
        package.writestr("_rels/.rels", package_rels)
        package.writestr("docProps/core.xml", core)
        package.writestr("docProps/app.xml", app)
        package.writestr("word/document.xml", document)
        package.writestr("word/styles.xml", styles_xml())
        package.writestr("word/numbering.xml", numbering_xml())
        package.writestr("word/settings.xml", settings)
        package.writestr("word/fontTable.xml", font_table())
        package.writestr("word/header1.xml", header)
        package.writestr("word/footer1.xml", footer_xml())
        package.writestr("word/_rels/document.xml.rels", rels_xml(doc.rels))
        package.writestr("word/_rels/header1.xml.rels", rels_xml(doc.header_rels))
        for name, path in doc.media.items():
            package.write(path, f"word/media/{name}")
    print(f"DOCX: {output} · {doc.figures} figuras · {len(doc.bookmarks)} títulos en el índice")


def to_pdf(docx: pathlib.Path, soffice: str | None) -> None:
    executable = next((c for c in (soffice, *SOFFICE_CANDIDATES, shutil.which("soffice")) if c and
                       pathlib.Path(c).exists()), None)
    if not executable:
        sys.exit("No se encontró LibreOffice: indícalo con --soffice")
    subprocess.run([executable, "--headless", "--convert-to", "pdf", "--outdir", str(docx.parent), str(docx)],
                   check=True, capture_output=True)
    print(f"PDF:  {docx.with_suffix('.pdf')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convierte la documentación de SmartPot a DOCX y PDF.")
    parser.add_argument("markdown", type=pathlib.Path)
    parser.add_argument("-o", "--output", type=pathlib.Path, help="DOCX de salida (por defecto, junto al .md)")
    parser.add_argument("--pdf", action="store_true", help="Genera también el PDF con LibreOffice")
    parser.add_argument("--soffice", help="Ejecutable de LibreOffice")
    args = parser.parse_args()

    output = args.output or args.markdown.with_suffix(".docx")
    build(args.markdown, output)
    if args.pdf:
        to_pdf(output, args.soffice)


if __name__ == "__main__":
    main()
