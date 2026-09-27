#!/usr/bin/env python3
"""Renderiza los diagramas Mermaid de `docs/diagrams/` a PNG y SVG y los sincroniza con el Markdown.

Cada `.mmd` trae la paleta de SmartPot en su directiva `%%{init}%%`: el render no decide
colores, solo mide el ancho natural del diagrama y elige la escala del PNG.

    python docs/tools/render_diagrams.py                              # todos
    python docs/tools/render_diagrams.py SmartPot_02_Reading_Sequence
    python docs/tools/render_diagrams.py --sync-md docs/SmartPot_Technical_Documentation.md
    python docs/tools/render_diagrams.py --super                      # superdiagramas, solo SVG

`--sync-md` reemplaza, en el Markdown, el bloque ```mermaid que sigue a cada
`<!-- diagrama: NOMBRE | titulo=... -->` por el contenido de `diagrams/NOMBRE.mmd`, así el
Markdown (que GitHub dibuja) y las imágenes del DOCX salen de la misma fuente.

`--super` renderiza los superdiagramas de `docs/superdiagrams/`: diagramas independientes de
cualquier tamaño que no van en un documento. Salen solo en SVG y sin el límite de texto ni de
aristas que mermaid aplica por defecto.

Requiere Node.js (usa `npx @mermaid-js/mermaid-cli`) y Google Chrome.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

DOCS = pathlib.Path(__file__).resolve().parent.parent
DIAGRAMS = DOCS / "diagrams"
IMAGES = DOCS / "images" / "diagrams"
SUPER = DOCS / "superdiagrams"
SUPER_IMAGES = DOCS / "images" / "superdiagrams"
# Los superdiagramas superan los límites por defecto de mermaid (50 000 caracteres y 500 aristas).
SUPER_LIMITS = {"maxTextSize": 5_000_000, "maxEdges": 20_000}

# Versión fija: mermaid cambia el motor de diseño entre versiones mayores.
MERMAID_CLI = "@mermaid-js/mermaid-cli@11"
CHROME_CANDIDATES = (
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
)
# Un PNG más ancho infla el DOCX sin ganar lectura.
MAX_WIDTH_PX = 4200

MARKER = re.compile(r"<!--\s*diagrama:\s*([\w.-]+)[^>]*-->\s*\n```mermaid\n[^`]*```")
VIEWBOX = re.compile(r'viewBox="[-\d.]+ [-\d.]+ ([\d.]+) ([\d.]+)"')


def find_chrome(explicit: str | None) -> str:
    for candidate in (explicit, *CHROME_CANDIDATES, shutil.which("chrome"), shutil.which("chromium")):
        if candidate and pathlib.Path(candidate).exists():
            return candidate.replace("\\", "/")
    sys.exit("No se encontró Chrome: indícalo con --chrome")


def mmdc(source: pathlib.Path, target: pathlib.Path, puppeteer: pathlib.Path, extra: str) -> list[str]:
    command = f'npx -y {MERMAID_CLI} -i "{source}" -o "{target}" -p "{puppeteer}" -b white {extra}'
    result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = (result.stdout + result.stderr).splitlines()
    errors = [line for line in lines if "rror" in line or "Parse" in line or "Expecting" in line]
    return errors + ([] if result.returncode == 0 else [f"mmdc terminó con código {result.returncode}"])


def render(source: pathlib.Path, workdir: pathlib.Path, puppeteer: pathlib.Path) -> bool:
    # Primero un SVG de prueba para conocer el ancho natural: con un lienzo más angosto
    # mermaid encoge el diagrama y el texto queda ilegible en papel.
    probe = workdir / f"{source.stem}.svg"
    errors = mmdc(source, probe, puppeteer, "-w 6000")
    width = 1600.0
    if probe.exists():
        match = VIEWBOX.search(probe.read_text(encoding="utf-8"))
        if match:
            width = float(match.group(1))
    scale = max(1.0, min(3.0, MAX_WIDTH_PX / width))
    canvas = int(width) + 80
    errors += mmdc(source, IMAGES / f"{source.stem}.png", puppeteer, f"-w {canvas} -s {scale:.2f}")
    errors += mmdc(source, IMAGES / f"{source.stem}.svg", puppeteer, f"-w {canvas}")
    status = "ERROR" if errors else "OK"
    print(f"{status:5} {source.stem} · ancho {width:.0f} px · escala {scale:.2f}", *errors[:6], sep="\n      ")
    return not errors


def render_super(source: pathlib.Path, workdir: pathlib.Path, puppeteer: pathlib.Path) -> bool:
    config = workdir / "super-config.json"
    config.write_text(json.dumps(SUPER_LIMITS), encoding="utf-8")
    target = SUPER_IMAGES / f"{source.stem}.svg"
    errors = mmdc(source, target, puppeteer, f'-w 4000 -c "{config}"')
    size = ""
    if target.exists():
        match = VIEWBOX.search(target.read_text(encoding="utf-8"))
        if match:
            size = f" · {float(match.group(1)):.0f} × {float(match.group(2)):.0f} px"
    status = "ERROR" if errors else "OK"
    print(f"{status:5} {source.stem}{size}", *errors[:6], sep="\n      ")
    return not errors


def sync_markdown(markdown: pathlib.Path) -> None:
    text = markdown.read_text(encoding="utf-8")

    def replace(match: re.Match) -> str:
        source = DIAGRAMS / f"{match.group(1)}.mmd"
        if not source.exists():
            print(f"      sin fuente para {match.group(1)}: el bloque queda igual")
            return match.group(0)
        header = match.group(0).split("```mermaid", 1)[0]
        return f"{header}```mermaid\n{source.read_text(encoding='utf-8').strip()}\n```"

    updated, count = MARKER.subn(replace, text)
    markdown.write_bytes(updated.encode("utf-8"))
    print(f"Markdown sincronizado: {markdown.name} · {count} diagramas")


def main() -> None:
    parser = argparse.ArgumentParser(description="Renderiza los diagramas de SmartPot.")
    parser.add_argument("names", nargs="*", help="Nombres de .mmd sin extensión; sin nombres, todos")
    parser.add_argument("--sync-md", nargs="*", type=pathlib.Path, default=[],
                        help="Markdown cuyos bloques mermaid se reemplazan por los .mmd")
    parser.add_argument("--no-render", action="store_true", help="Solo sincroniza el Markdown")
    parser.add_argument("--super", action="store_true", help="Renderiza los superdiagramas (solo SVG)")
    parser.add_argument("--chrome", help="Ejecutable de Chrome para puppeteer")
    args = parser.parse_args()

    ok = True
    folder, images = (SUPER, SUPER_IMAGES) if args.super else (DIAGRAMS, IMAGES)
    if not args.no_render:
        sources = [folder / f"{n}.mmd" for n in args.names] if args.names else sorted(folder.glob("*.mmd"))
        missing = [s.name for s in sources if not s.exists()]
        if missing:
            sys.exit("No existen: " + ", ".join(missing))
        images.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            workdir = pathlib.Path(tmp)
            puppeteer = workdir / "puppeteer.json"
            puppeteer.write_text(json.dumps({"executablePath": find_chrome(args.chrome), "args": ["--no-sandbox"]}),
                                 encoding="utf-8")
            for source in sources:
                ok = (render_super if args.super else render)(source, workdir, puppeteer) and ok

    for markdown in args.sync_md:
        sync_markdown(markdown)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
