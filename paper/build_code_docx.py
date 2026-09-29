"""Genera GD.docx: todo el código fuente del repositorio en un Word legible.

Este documento es el INSUMO que se adjunta al modelo para que redacte el
artículo científico. No es el artículo: es el código completo del proyecto,
formateado con índice, rutas y bloques de código monoespaciados.

Uso:
    python build_code_docx.py --repo .. --out GD.docx
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.shared import Cm, Pt, RGBColor

# Extensiones que se incluyen como código fuente.
CODE_EXT = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".css",
    ".sql", ".sh", ".toml", ".json", ".yml", ".yaml",
    ".txt", ".example", ".npmrc", ".gitignore", ".gitattributes",
    ".dockerignore",
}
# Nombres sin extensión que igual son relevantes.
CODE_NAMES = {"Dockerfile", "docker-entrypoint.sh"}

# Documentos que aportan contexto (van primero, como documentación).
DOCS = ["README.md", "docker-compose.yml", "docker-compose.override.yml",
        "backend/requirements.txt", "backend/pyproject.toml"]

# Rutas excluidas: artefactos generados, binarios y el propio paper.
EXCLUDE_PREFIX = ("paper/", "frontend/.next/", "frontend/node_modules/",
                  "backend/.venv/", "backend/.pytest_cache/")
EXCLUDE_SUFFIX = (".png", ".jpg", ".jpeg", ".ico", ".db", ".lock", ".tsbuildinfo")


def list_files(repo: Path) -> list[str]:
    """Archivos versionados por git, en orden determinista."""
    out = subprocess.run(
        ["git", "ls-files"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    files = []
    for rel in out.splitlines():
        rel = rel.strip()
        if not rel or rel.startswith(EXCLUDE_PREFIX):
            continue
        if rel.endswith(EXCLUDE_SUFFIX):
            continue
        name = Path(rel).name
        if Path(rel).suffix.lower() in CODE_EXT or name in CODE_NAMES:
            files.append(rel)
    # Documentación primero, luego backend, luego frontend, luego el resto.
    def sort_key(p: str) -> tuple:
        tier = 0 if p in DOCS else (1 if p.startswith("backend/") else (2 if p.startswith("frontend/") else 3))
        return (tier, p)
    return sorted(files, key=sort_key)


def _block(doc: Document, text: str, size: int = 8) -> None:
    """Inserta un bloque de código monoespaciado con salto de página previo."""
    for line in text.split("\n"):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.line_spacing = 1.0
        run = p.add_run(line if line.strip() else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(size)
        run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)


def build(repo: Path, out: Path) -> dict:
    files = list_files(repo)
    doc = Document()

    # --- Portada -----------------------------------------------------------
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("MAE-4 — Código fuente completo")
    r.bold = True
    r.font.size = Pt(22)

    s = doc.add_paragraph()
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = s.add_run("Gemelo digital hidrogeomorfológico de humedales costeros y carbono azul")
    r.italic = True
    r.font.size = Pt(13)

    s2 = doc.add_paragraph()
    s2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = s2.add_run("Santuario Nacional Los Manglares de Tumbes, Perú")
    r.font.size = Pt(11)

    doc.add_paragraph()
    doc.add_paragraph(
        "Este documento contiene el código fuente íntegro del repositorio, "
        "organizado por capa y en orden de dependencia. Se acompaña de la "
        "documentación técnica del proyecto. Su finalidad es servir de insumo "
        "para el análisis exhaustivo del sistema y la elaboración del artículo "
        "de investigación derivado."
    )

    doc.add_paragraph()
    meta = doc.add_paragraph()
    meta.add_run("Total de archivos: ").bold = True
    meta.add_run(f"{len(files)}")
    meta2 = doc.add_paragraph()
    meta2.add_run("Repositorio: ").bold = True
    meta2.add_run("https://github.com/giansmd/software-2-mae-4")

    # --- Índice ------------------------------------------------------------
    doc.add_page_break()
    doc.add_heading("Índice de archivos", level=1)
    for i, rel in enumerate(files, 1):
        p = doc.add_paragraph(f"{i}. {rel}")
        p.paragraph_format.space_after = Pt(2)
        for run in p.runs:
            run.font.size = Pt(9)

    # --- Contenido ---------------------------------------------------------
    stats = {"files": len(files), "lines": 0, "chars": 0}
    for rel in files:
        path = repo / rel
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        stats["lines"] += text.count("\n") + 1
        stats["chars"] += len(text)

        doc.add_page_break()
        h = doc.add_heading(rel, level=1)
        p = doc.add_paragraph()
        run = p.add_run(f"Líneas: {text.count(chr(10)) + 1} · Caracteres: {len(text)}")
        run.italic = True
        run.font.size = Pt(8)

        _block(doc, text)

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    stats["out_kb"] = out.stat().st_size // 1024
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Genera GD.docx con el código del repo.")
    ap.add_argument("--repo", default="..", type=Path)
    ap.add_argument("--out", default="GD.docx", type=Path)
    args = ap.parse_args(argv)

    repo = args.repo.resolve()
    stats = build(repo, args.out)
    print(f"Archivos incluidos: {stats['files']}")
    print(f"Líneas totales: {stats['lines']:,}")
    print(f"Caracteres: {stats['chars']:,}")
    print(f"Salida: {args.out} ({stats['out_kb']:,} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
