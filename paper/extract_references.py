"""Extrae el texto de los 40 PDFs y construye un índice de citas utilizables.

Salida:
    paper/references_txt/<slug>.txt   — texto completo por artículo
    paper/tables/citas_candidatas.json — fragmentos citables con metadatos
    paper/tables/bibliografia.json    — metadatos APA por artículo
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pymupdf

PDF_DIR = Path(__file__).resolve().parent / "references_pdf"
TXT_DIR = Path(__file__).resolve().parent / "references_txt"
TAB_DIR = Path(__file__).resolve().parent / "tables"

# Frases que señalan fragmentos conceptualmente útiles para el artículo:
# definiciones de gemelo digital, arquitectura, validación, incertidumbre,
# seguimiento de datos, restauración de humedales y gobernanza.
KEY_PATTERNS = [
    r"digital twin[s]? (?:is|are|can be defined|refers to|as a)",
    r"we define .{0,40}digital twin",
    r"data[- ]driven",
    r"model[- ]data fusion",
    r"physics[- ]informed",
    r"real[- ]time",
    r"uncertaint(?:y|ies)",
    r"calibrat(?:e|ion|ing)",
    r"validat(?:e|ion|ing)",
    r"restoration",
    r"wetland",
    r"mangrove",
    r"carbon",
    r"interoperab",
    r"governance",
    r"stakeholder",
    r"scenario",
    r"monitoring",
    r"remote sensing",
    r"machine learning",
    r"decision[- ]mak",
    r"ecosystem service",
    r"blue carbon",
    r"sea[- ]level",
]


def slug(name: str) -> str:
    base = name.rsplit(".", 1)[0]
    s = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:80]


def clean(text: str) -> str:
    text = re.sub(r"-\n(?=[a-z])", "", text)          # palabras cortadas
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sentences(text: str) -> list[str]:
    """Divide en oraciones conservando las que tienen contenido sustantivo."""
    text = re.sub(r"\n+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text)
    return [p.strip() for p in parts if 60 <= len(p.strip()) <= 400]


def main() -> int:
    TXT_DIR.mkdir(parents=True, exist_ok=True)
    TAB_DIR.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    print(f"PDFs encontrados: {len(pdfs)}")

    biblio = []
    candidatas = []

    for pdf in pdfs:
        doc = pymupdf.open(pdf)
        pages = [doc[i].get_text() for i in range(len(doc))]
        doc.close()
        raw = "\n".join(pages)
        text = clean(raw)

        s = slug(pdf.name)
        (TXT_DIR / f"{s}.txt").write_text(text, encoding="utf-8")

        # Metadatos: nombre del archivo ya trae "Autor et al. - Año - Título"
        stem = pdf.name.rsplit(".", 1)[0]
        m = re.match(r"^(?P<authors>[^-]+?)\s+-\s+(?P<year>\d{4})\s+-\s+(?P<title>.+)$", stem)
        authors = m.group("authors").strip() if m else stem
        year = m.group("year") if m else ""
        title = m.group("title").strip() if m else ""

        # DOI / revista si aparecen en el texto
        doi_m = re.search(r"(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", text)
        biblio.append({
            "archivo": pdf.name,
            "slug": s,
            "autores": authors,
            "anio": year,
            "titulo": title,
            "doi": doi_m.group(1).rstrip(".,") if doi_m else "",
            "paginas": len(pages),
            "caracteres": len(text),
        })

        # Fragmentos candidatos a cita
        sents = sentences(text)
        for pat in KEY_PATTERNS:
            rx = re.compile(pat, re.IGNORECASE)
            for i, sent in enumerate(sents):
                if rx.search(sent):
                    candidatas.append({
                        "slug": s,
                        "archivo": pdf.name,
                        "patron": pat,
                        "oracion": sent,
                        "idx": i,
                    })

    # Deduplicar por (slug, oración)
    seen = set()
    unicas = []
    for c in candidatas:
        k = (c["slug"], c["oracion"][:120])
        if k in seen:
            continue
        seen.add(k)
        unicas.append(c)

    (TAB_DIR / "bibliografia.json").write_text(
        json.dumps(biblio, ensure_ascii=False, indent=2), encoding="utf-8")
    (TAB_DIR / "citas_candidatas.json").write_text(
        json.dumps(unicas, ensure_ascii=False, indent=2), encoding="utf-8")

    total_chars = sum(b["caracteres"] for b in biblio)
    print(f"Texto extraído: {total_chars:,} caracteres")
    print(f"Fragmentos candidatos: {len(unicas):,}")
    print("\nPor artículo (caracteres):")
    for b in sorted(biblio, key=lambda x: -x["caracteres"])[:12]:
        print(f"  {b['caracteres']:>7,}  {b['archivo'][:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
