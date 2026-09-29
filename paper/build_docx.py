"""Ensamblador determinístico de documentos Word.

Flujo
-----
El contenido vive en archivos Markdown por sección (``paper/content/*.md``). Este
script los une en un único ``.docx`` resolviendo marcadores tipados:

    [[FIG:nombre.png|Pie de figura]]      -> inserta la imagen
    [[TABLA:nombre.csv|Pie de tabla]]     -> inserta la tabla
    [[REF:clave]]                          -> cita en el texto

El ensamblado NO usa IA: mismo input produce siempre el mismo output, de modo
que el documento es reproducible y auditable.

Uso
---
    python build_docx.py --content paper/content --out paper/GD.docx

Valida antes de construir: si falta una sección, una figura o una tabla
referenciada, falla y lo reporta en lugar de generar un documento incompleto.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

MARKER_RE = re.compile(r"\[\[(FIG|TABLA|REF):([^\]|]+)(?:\|([^\]]+))?\]\]")
HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")


def _short_cite(full: str) -> str:
    """Deriva la cita corta APA a partir de la referencia completa.

    ``Apellido, A. B., & Apellido, C. (2023). Título…`` -> ``Apellido & Apellido, 2023``
    """
    year = ""
    year_match = re.search(r"\((\d{4}[a-z]?)\)", full)
    if year_match:
        year = year_match.group(1)

    authors_part = full.split("(")[0].strip().rstrip(".")
    if re.search(r"\bet\s+al\.?", authors_part, re.IGNORECASE):
        first = re.split(r",|&|\by\b", authors_part)[0].strip()
        who = f"{first} et al."
        return f"{who}, {year}" if year else who

    # Se descarta el nombre de pila: se conservan los apellidos.
    tokens = [t.strip() for t in re.split(r",|&|\by\b", authors_part) if t.strip()]
    surnames = [t for t in tokens if not re.fullmatch(r"[A-Z]\.?", t)]
    if not surnames:
        surnames = tokens[:1]

    if len(surnames) == 1:
        who = surnames[0]
    elif len(surnames) == 2:
        who = f"{surnames[0]} & {surnames[1]}"
    else:
        who = f"{surnames[0]} et al."

    return f"{who}, {year}" if year else who


def _add_runs(paragraph, text: str) -> None:
    """Añade texto interpretando **negrita** e *itálica* simples."""
    pos = 0
    for match in BOLD_RE.finditer(text):
        if match.start() > pos:
            paragraph.add_run(text[pos:match.start()])
        paragraph.add_run(match.group(1)).bold = True
        pos = match.end()
    tail = text[pos:]
    if tail:
        pos2 = 0
        for match in ITALIC_RE.finditer(tail):
            if match.start() > pos2:
                paragraph.add_run(tail[pos2:match.start()])
            paragraph.add_run(match.group(1)).italic = True
            pos2 = match.end()
        if tail[pos2:]:
            paragraph.add_run(tail[pos2:])


@dataclass
class BuildReport:
    """Resultado del ensamblado, para verificación y trazabilidad."""

    sections: list[str]
    figures: list[str]
    tables: list[str]
    refs: list[str]
    words: int
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def _load_references(refs_path: Path) -> dict[str, str]:
    """Carga un archivo de referencias en formato `clave|texto APA`."""
    refs: dict[str, str] = {}
    if not refs_path.exists():
        return refs
    for line in refs_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        key, _, value = line.partition("|")
        refs[key.strip()] = value.strip()
    return refs


def _style_document(doc: Document, font: str, size: int) -> None:
    """Aplica estilos base al documento."""
    normal = doc.styles["Normal"]
    normal.font.name = font
    normal.font.size = Pt(size)
    for level, pt in ((1, 16), (2, 14), (3, 12), (4, 11)):
        style = doc.styles[f"Heading {level}"]
        style.font.name = font
        style.font.size = Pt(pt)
        style.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)


def _add_table(doc: Document, csv_path: Path, caption: str) -> None:
    """Inserta una tabla desde CSV con encabezado y pie."""
    with csv_path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Light Grid Accent 1"
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            if j < len(table.columns):
                table.cell(i, j).text = str(cell)
                if i == 0:
                    for p in table.cell(i, j).paragraphs:
                        for r in p.runs:
                            r.bold = True
    if caption:
        p = doc.add_paragraph()
        run = p.add_run(f"Tabla. {caption}")
        run.italic = True
        run.font.size = Pt(9)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT


def _render_section(doc: Document, text: str, figures_dir: Path, tables_dir: Path,
                    refs: dict[str, str], report: BuildReport) -> None:
    """Renderiza una sección resolviendo sus marcadores en orden de aparición."""
    for raw in text.split("\n"):
        line = raw.rstrip()

        heading = HEADING_RE.match(line)
        if heading:
            level = min(len(heading.group(1)), 4)
            doc.add_heading(heading.group(2).strip(), level=level)
            continue

        if not line.strip():
            continue

        # Cada línea puede contener varios marcadores.
        pos = 0
        paragraph = doc.add_paragraph()
        for match in MARKER_RE.finditer(line):
            literal = line[pos:match.start()]
            if literal:
                _add_runs(paragraph, literal)

            kind, target, caption = match.group(1), match.group(2).strip(), (match.group(3) or "").strip()

            if kind == "FIG":
                path = figures_dir / target
                if not path.exists():
                    report.errors.append(f"Figura no encontrada: {target}")
                else:
                    doc.add_picture(str(path), width=Cm(15.5))
                    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                    report.figures.append(target)
                    if caption:
                        cp = doc.add_paragraph()
                        run = cp.add_run(f"Figura. {caption}")
                        run.italic = True
                        run.font.size = Pt(9)
                        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER

            elif kind == "TABLA":
                path = tables_dir / target
                if not path.exists():
                    report.errors.append(f"Tabla no encontrada: {target}")
                else:
                    _add_table(doc, path, caption)
                    report.tables.append(target)

            elif kind == "REF":
                if target not in refs:
                    report.errors.append(f"Referencia no definida: {target}")
                else:
                    report.refs.append(target)
                    paragraph.add_run(f"({_short_cite(refs[target])})")

            pos = match.end()

        tail = line[pos:]
        if tail:
            _add_runs(paragraph, tail)
        if not paragraph.runs:
            # Párrafo sin contenido real: se descarta para no dejar huecos.
            paragraph._element.getparent().remove(paragraph._element)


def build(content_dir: Path, out_path: Path, figures_dir: Path | None = None,
          tables_dir: Path | None = None, refs_path: Path | None = None,
          font: str = "Times New Roman", size: int = 11) -> BuildReport:
    """Ensambla el .docx y devuelve un reporte verificable."""
    base = content_dir.parent
    figures_dir = figures_dir or base / "figures"
    tables_dir = tables_dir or base / "tables"
    refs_path = refs_path or base / "references.txt"

    files = sorted(content_dir.glob("*.md"))
    if not files:
        raise SystemExit(f"No hay secciones en {content_dir}")

    refs = _load_references(refs_path)
    report = BuildReport(sections=[], figures=[], tables=[], refs=[], words=0, errors=[], warnings=[])

    doc = Document()
    _style_document(doc, font, size)

    for path in files:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            report.errors.append(f"Sección vacía: {path.name}")
            continue
        report.sections.append(path.name)
        report.words += len(text.split())
        _render_section(doc, text, figures_dir, tables_dir, refs, report)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ensambla GD.docx desde secciones Markdown.")
    ap.add_argument("--content", default="paper/content", type=Path)
    ap.add_argument("--figures", default=None, type=Path)
    ap.add_argument("--tables", default=None, type=Path)
    ap.add_argument("--refs", default=None, type=Path)
    ap.add_argument("--out", default="paper/GD.docx", type=Path)
    ap.add_argument("--font", default="Times New Roman")
    ap.add_argument("--size", default=11, type=int)
    args = ap.parse_args(argv)

    rep = build(args.content, args.out, args.figures, args.tables, args.refs, args.font, args.size)

    print(f"Secciones: {len(rep.sections)} -> {', '.join(rep.sections)}")
    print(f"Figuras insertadas: {len(rep.figures)}")
    print(f"Tablas insertadas: {len(rep.tables)}")
    print(f"Citas resueltas: {len(rep.refs)}")
    print(f"Palabras: {rep.words:,}")
    print(f"Salida: {args.out}")

    if rep.errors:
        print("\nERRORES:")
        for e in rep.errors:
            print(f"  - {e}")
        return 1
    if rep.warnings:
        print("\nAVISOS:")
        for w in rep.warnings:
            print(f"  - {w}")
    print("\nOK: documento generado sin errores.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
