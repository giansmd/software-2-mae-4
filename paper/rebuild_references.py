"""Regenera references.txt usando el DOI real extraído de cada PDF.

Cruza: metadatos del PDF (autores, año, título del nombre de archivo) + DOI
extraído de la cabecera + datos de Crossref (revista, volumen, páginas).
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
TAB = BASE / "tables"
UA = {"User-Agent": "mae4/1.0 (mailto:gianfranco.samana@gmail.com)"}

# Clave estable por artículo (primer apellido + año).
def make_key(autores: str, anio: str) -> str:
    first = re.split(r"\s|,|and", autores.strip())[0]
    first = re.sub(r"[^A-Za-z]", "", first).lower()
    return f"{first}{anio}"


def crossref(doi: str) -> dict | None:
    try:
        req = urllib.request.Request(f"https://api.crossref.org/works/{doi}", headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.load(r)["message"]
    except Exception:
        return None


def apa_from(autores: str, anio: str, titulo: str, doi: str, msg: dict | None) -> str:
    """Construye la referencia APA. Crossref aporta revista/volumen/páginas."""
    journal = vol = issue = page = ""
    if msg:
        journal = (msg.get("container-title") or [""])[0]
        vol = msg.get("volume", "")
        issue = msg.get("issue", "")
        page = msg.get("page", "")

    # Autores: se conserva el formato del archivo y se añaden iniciales si faltan.
    who = autores.strip()
    who = re.sub(r"\s+and\s+", " & ", who)
    if who.endswith("et al."):
        who = who  # se respeta la forma abreviada del nombre del archivo

    parts = [f"{who} ({anio}). {titulo}."]
    if journal:
        seg = f"*{journal}*"
        if vol:
            seg += f", {vol}"
            if issue:
                seg += f"({issue})"
        if page:
            seg += f", {page}"
        parts.append(seg + ".")
    if doi:
        parts.append(f"https://doi.org/{doi}")
    return " ".join(parts)


def main() -> int:
    biblio = json.loads((TAB / "bibliografia.json").read_text(encoding="utf-8"))
    dois = {d["slug"]: d for d in json.loads((TAB / "dois_extraidos.json").read_text(encoding="utf-8"))}

    lineas, meta = [], []
    for b in biblio:
        d = dois.get(b["slug"], {})
        doi = d.get("doi", "")
        msg = crossref(doi) if doi else None

        # Título real desde el nombre del archivo.
        stem = b["archivo"].rsplit(".", 1)[0]
        m = re.match(r"^[^-]+-\s*\d{4}\s*-\s*(.+)$", stem)
        titulo = (m.group(1) if m else b["titulo"]).strip()
        titulo = re.sub(r"\bPDF\b", "", titulo).strip()

        key = make_key(b["autores"], b["anio"])
        ref = apa_from(b["autores"], b["anio"], titulo, doi, msg)
        lineas.append(f"{key} | {ref}")
        meta.append({"clave": key, "slug": b["slug"], "doi": doi,
                     "crossref_ok": bool(msg),
                     "titulo_crossref": (msg.get("title") or [""])[0] if msg else ""})
        time.sleep(0.12)

    header = (
        "# Bibliografía — 40 artículos provistos por el docente\n"
        "# Formato: clave|referencia APA 7\n"
        "# DOI extraído de la cabecera de cada PDF y validado contra Crossref.\n\n"
    )
    (BASE / "references.txt").write_text(header + "\n\n".join(lineas) + "\n", encoding="utf-8")
    (TAB / "referencias_finales.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Referencias escritas: {len(lineas)}")
    print(f"con DOI validado: {sum(1 for m in meta if m['crossref_ok'])}")
    print(f"sin DOI: {sum(1 for m in meta if not m['doi'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
