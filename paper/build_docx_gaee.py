"""Deterministic Word assembler — GaEE (Geomatics and Environmental Engineering) format.

Pipeline
--------
Content lives in per-section Markdown files (``paper/content-en/*.md``). This
script joins them into a single ``.docx`` resolving typed markers:

    [[FIG:name.png|Figure caption]]     -> inserts the image + caption below
    [[TABLA:name.csv|Table caption]]    -> inserts the table + caption above
    [[REF:key]]                         -> numeric citation [n] (Vancouver)

Differences vs. build_docx.py (APA/Manglar version):
    * Citations are numeric, mapped through ref_numbering.json (order of first
      appearance), rendered as [n] before punctuation per GaEE guidelines.
    * The References section file contains a pre-numbered list rendered as-is.
    * Table captions go ABOVE the table, figure captions BELOW the figure.
    * A title page block (title / authors / affiliations placeholder) is
      prepended, per the GaEE template.

The assembly uses NO AI: same input always yields the same output, so the
document is reproducible and auditable.

Usage
-----
    python build_docx_gaee.py --content paper/content-en --out paper/articulo-gaee-en.docx
"""
from __future__ import annotations

import argparse
import csv
import json
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


def _add_runs(paragraph, text: str) -> None:
    """Adds text interpreting simple **bold** and *italic*."""
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
    sections: list[str]
    figures: list[str]
    tables: list[str]
    refs: list[int]
    words: int
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def _load_titlepage(path: Path) -> dict[str, str] | None:
    """Loads title page fields from a `key: value` text file (None if absent)."""
    if not path.exists():
        return None
    fields: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(": ")
        if not value:  # tolerate 'key:value' without space, but never split 'https://'
            key, _, value = line.partition(":")
            if value.startswith("//"):
                key, _, value = line.partition(": ")
        fields[key.strip()] = value.strip()
    return fields


def _render_titlepage(doc: Document, fields: dict[str, str]) -> None:
    """Renders title, authors and footnote-style affiliation blocks."""
    title = doc.add_paragraph()
    trun = title.add_run(fields.get("title", ""))
    trun.bold = True
    trun.font.size = Pt(14)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    authors = []
    for i in (1, 2):
        name = fields.get(f"author{i}")
        if name:
            authors.append(f"{name} {i}")
    ap = doc.add_paragraph(", ".join(authors))
    ap.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for i in (1, 2):
        aff = fields.get(f"affiliation{i}")
        if not aff:
            continue
        p = doc.add_paragraph()
        run = p.add_run(f"{i} {aff}\n{fields.get(f'email{i}', '')}\n{fields.get(f'orcid{i}', '')}")
        run.font.size = Pt(9)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    credit = fields.get("credit")
    if credit:
        cp = doc.add_paragraph()
        crun = cp.add_run(credit)
        crun.font.size = Pt(9)
        cp.alignment = WD_ALIGN_PARAGRAPH.LEFT

    doc.add_paragraph()


def _style_document(doc: Document, font: str, size: int) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = font
    normal.font.size = Pt(size)
    for level, pt in ((1, 14), (2, 12), (3, 11), (4, 11)):
        style = doc.styles[f"Heading {level}"]
        style.font.name = font
        style.font.size = Pt(pt)
        style.font.color.rgb = RGBColor(0x00, 0x00, 0x00)


def _add_table(doc: Document, csv_path: Path, caption: str) -> None:
    with csv_path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return
    if caption:
        p = doc.add_paragraph()
        run = p.add_run(caption)
        run.italic = True
        run.font.size = Pt(9)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
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


def _render_section(doc: Document, text: str, figures_dir: Path, tables_dir: Path,
                    ref_map: dict[str, int], report: BuildReport) -> None:
    for raw in text.split("\n"):
        line = raw.rstrip()

        heading = HEADING_RE.match(line)
        if heading:
            level = min(len(heading.group(1)), 4)
            doc.add_heading(heading.group(2).strip(), level=level)
            continue

        if not line.strip():
            continue

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
                    report.errors.append(f"Figure not found: {target}")
                else:
                    doc.add_picture(str(path), width=Cm(15.5))
                    # GaEE requires alt text: reuse the caption, verbatim.
                    if caption:
                        shape = doc.inline_shapes[-1]
                        shape._inline.docPr.set("descr", caption)
                    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                    report.figures.append(target)
                    if caption:
                        cp = doc.add_paragraph()
                        run = cp.add_run(caption)
                        run.italic = True
                        run.font.size = Pt(9)
                        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER

            elif kind == "TABLA":
                path = tables_dir / target
                if not path.exists():
                    report.errors.append(f"Table not found: {target}")
                else:
                    _add_table(doc, path, caption)
                    report.tables.append(target)

            elif kind == "REF":
                # Legacy marker: the translated corpus carries literal [n],
                # so a REF marker here indicates a stale section file.
                report.errors.append(f"Unexpected REF marker in translated corpus: {target}")

            pos = match.end()

        tail = line[pos:]
        if tail:
            _add_runs(paragraph, tail)
        if not paragraph.runs:
            paragraph._element.getparent().remove(paragraph._element)


def build(content_dir: Path, out_path: Path, figures_dir: Path | None = None,
          tables_dir: Path | None = None, numbering_path: Path | None = None,
          titlepage_path: Path | None = None,
          font: str = "Times New Roman", size: int = 11) -> BuildReport:
    base = content_dir.parent
    figures_dir = figures_dir or base / "figures"
    tables_dir = tables_dir or base / "tables"
    numbering_path = numbering_path or base / "ref_numbering.json"
    titlepage_path = titlepage_path or base / "titlepage.txt"

    files = sorted(content_dir.glob("*.md"))
    if not files:
        raise SystemExit(f"No sections in {content_dir}")

    ref_map = json.loads(numbering_path.read_text(encoding="utf-8"))
    report = BuildReport(sections=[], figures=[], tables=[], refs=[], words=0, errors=[], warnings=[])

    doc = Document()
    _style_document(doc, font, size)

    tp = _load_titlepage(titlepage_path)
    if tp is None:
        report.warnings.append(f"Title page file not found: {titlepage_path}")
    else:
        _render_titlepage(doc, tp)

    for path in files:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            report.errors.append(f"Empty section: {path.name}")
            continue
        report.sections.append(path.name)
        report.words += len(text.split())
        # Collect numeric citations present in the section text (they are
        # already literal [n] in the translated corpus).
        if path.name != "07-references.md":
            for m in re.finditer(r"\[(\d{1,2})\]", text):
                report.refs.append(int(m.group(1)))
        _render_section(doc, text, figures_dir, tables_dir, ref_map, report)

    # Deterministic verification: every mapped ref number must be cited at
    # least once in the body, and no citation may point outside the map.
    cited = set(report.refs)
    valid = set(ref_map.values())
    for num in sorted(valid):
        if num not in cited:
            key = next(k for k, v in ref_map.items() if v == num)
            report.errors.append(f"Reference [{num}] ({key}) never cited in text")
    for num in sorted(cited):
        if num not in valid:
            report.errors.append(f"Citation [{num}] has no entry in the numbering map")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Assemble GaEE-format .docx from Markdown sections.")
    ap.add_argument("--content", default="paper/content-en", type=Path)
    ap.add_argument("--figures", default=None, type=Path)
    ap.add_argument("--tables", default=None, type=Path)
    ap.add_argument("--numbering", default=None, type=Path)
    ap.add_argument("--titlepage", default=None, type=Path)
    ap.add_argument("--out", default="paper/articulo-gaee-en.docx", type=Path)
    ap.add_argument("--font", default="Times New Roman")
    ap.add_argument("--size", default=11, type=int)
    args = ap.parse_args(argv)

    rep = build(args.content, args.out, args.figures, args.tables, args.numbering,
                args.titlepage, args.font, args.size)

    print(f"Sections: {len(rep.sections)} -> {', '.join(rep.sections)}")
    print(f"Figures inserted: {len(rep.figures)}")
    print(f"Tables inserted: {len(rep.tables)}")
    print(f"Citations resolved: {len(rep.refs)} (unique: {len(set(rep.refs))})")
    print(f"Words: {rep.words:,}")
    print(f"Output: {args.out}")

    if rep.errors:
        print("\nERRORS:")
        for e in rep.errors:
            print(f"  - {e}")
        return 1
    if rep.warnings:
        print("\nWARNINGS:")
        for w in rep.warnings:
            print(f"  - {w}")
    print("\nOK: document generated without errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
