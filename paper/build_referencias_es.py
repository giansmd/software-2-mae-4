"""Construye ``referencias.json`` para el artículo en español.

Toma la lista existente (``paper/content/08-referencias.md``) y la completa con
los metadatos de Crossref ya descargados (``paper/tables/bibliografia_crossref.json``):
autores completos, títulos sin truncar, volumen, páginas y DOI.

Salida:
    ../semana 11/articulo/referencias.json   clave -> referencia formateada

Uso:
    backend/.venv/Scripts/python.exe paper/build_referencias_es.py
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent.parent / "semana 11" / "articulo" / "referencias.json"

# Año del número impreso, que es el que usa el texto (Crossref registra a veces
# el año de publicación en línea).
YEAR_OVERRIDES = {"brown2019": "2019", "devries2024": "2024", "henriksen2023": "2023"}


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", text.lower())


def main() -> int:
    numbering = json.loads((ROOT / "ref_numbering.json").read_text(encoding="utf-8"))
    lines = [
        line.strip()
        for line in (ROOT / "content" / "08-referencias.md").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    crossref = json.loads(
        (ROOT / "tables" / "bibliografia_crossref.json").read_text(encoding="utf-8")
    )
    by_title = {norm(item["crossref"]["title"])[:60]: item["apa"] for item in crossref}

    out: dict[str, str] = {}
    problems: list[str] = []
    upgraded = 0
    for key in sorted(numbering, key=lambda k: numbering[k]):
        surname = re.sub(r"\d{4}$", "", key)
        year = key[-4:]
        candidates = [ln for ln in lines if norm(surname) in norm(ln)[:40] and year in ln]
        if len(candidates) != 1:
            problems.append(f"{key}: {len(candidates)} candidatos")
            continue
        line = candidates[0]
        title = re.sub(r"^.*?\(\d{4}\)\.\s*", "", line).split("*")[0]
        apa = by_title.get(norm(title)[:60])
        if apa:
            year_fix = YEAR_OVERRIDES.get(key)
            if year_fix:
                apa = re.sub(r"\(\d{4}\)", f"({year_fix})", apa, count=1)
            out[key] = apa
            upgraded += 1
        else:
            out[key] = line

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Referencias: {len(out)}/{len(numbering)} | completadas con Crossref: {upgraded}")
    for key, ref in out.items():
        mark = "CROSSREF" if ref in by_title.values() else "LOCAL"
        print(f"  [{numbering[key]:2d}] {key:18s} {mark:8s} {ref[:90]}")
    if problems:
        print("\nPROBLEMAS:")
        for p in problems:
            print("  -", p)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
