"""Completa con Crossref las referencias que aún usan «et al.».

Uso:
    backend/.venv/Scripts/python.exe paper/completar_referencias.py
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

REFS = Path(__file__).resolve().parent.parent.parent / "semana 11" / "articulo" / "referencias.json"
HEADERS = {"User-Agent": "mae4-article/1.0 (mailto:gsamana@unitru.edu.pe)"}
TARGETS = {
    "verdouw2021": "10.1016/j.agsy.2020.103046",
    "aguzzi2025": "10.1016/j.ecoinf.2025.103409",
    "guo2017": "10.3390/s17040777",
    "durao2018": "10.1007/978-3-030-01614-2_19",
    "rodriguez2024": "10.3390/s24051568",
}


def apa(message: dict) -> str:
    authors = []
    for a in message.get("author", []):
        family = a.get("family", "")
        given = a.get("given", "")
        initials = " ".join(f"{part[0]}." for part in re.split(r"[\s-]+", given) if part)
        authors.append(f"{family}, {initials}".strip(", "))
    if len(authors) > 20:
        author_text = ", ".join(authors[:19]) + ", ... " + authors[-1]
    elif len(authors) > 1:
        author_text = ", ".join(authors[:-1]) + ", & " + authors[-1]
    else:
        author_text = authors[0] if authors else ""

    year = (message.get("issued", {}).get("date-parts") or [[""]])[0][0]
    title = (message.get("title") or [""])[0].rstrip(".")
    journal = (message.get("container-title") or [""])[0]
    volume = message.get("volume", "")
    issue = message.get("issue", "")
    page = message.get("page", "")
    doi = message.get("DOI", "")

    parts = [f"{author_text} ({year}). {title}."]
    venue = f"*{journal}*"
    if volume:
        venue += f", {volume}"
    if issue:
        venue += f"({issue})"
    if page:
        venue += f", {page}"
    parts.append(venue + ".")
    if doi:
        parts.append(f"https://doi.org/{doi}")
    return " ".join(parts)


def main() -> int:
    refs = json.loads(REFS.read_text(encoding="utf-8"))
    for key, doi in TARGETS.items():
        try:
            req = urllib.request.Request(f"https://api.crossref.org/works/{doi}", headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as resp:
                message = json.load(resp)["message"]
            refs[key] = apa(message)
            print(f"ok  {key}: {refs[key][:100]}")
        except Exception as exc:
            print(f"ERR {key}: {exc}")
    REFS.write_text(json.dumps(refs, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
