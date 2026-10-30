"""Verifica los DOI del artículo contra Crossref y reporta discrepancias.

Uso:
    backend/.venv/Scripts/python.exe paper/verify_dois.py
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REFS = ROOT.parent.parent / "semana 11" / "articulo" / "referencias.json"
REPORT = ROOT.parent.parent / "semana 11" / "articulo" / "verificacion_dois.json"
HEADERS = {"User-Agent": "mae4-article/1.0 (mailto:gsamana@unitru.edu.pe)"}


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", text.lower())


def main() -> int:
    refs = json.loads(REFS.read_text(encoding="utf-8"))
    report = []
    for key, ref in refs.items():
        match = re.search(r"https://doi\.org/(\S+)", ref)
        if not match:
            report.append({"clave": key, "doi": None, "estado": "sin DOI"})
            continue
        doi = match.group(1).rstrip(".")
        entry = {"clave": key, "doi": doi}
        try:
            req = urllib.request.Request(
                f"https://api.crossref.org/works/{doi}", headers=HEADERS
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                message = json.load(resp)["message"]
            title = (message.get("title") or [""])[0]
            local_title = re.sub(r"^.*?\(\d{4}\)\.\s*", "", ref).split("*")[0]
            entry.update(
                {
                    "estado": "ok" if norm(title)[:40] == norm(local_title)[:40] else "titulo distinto",
                    "titulo_crossref": title,
                    "revista_crossref": (message.get("container-title") or [""])[0],
                    "anio_crossref": (message.get("issued", {}).get("date-parts") or [[""]])[0][0],
                }
            )
        except urllib.error.HTTPError as exc:
            entry.update({"estado": f"HTTP {exc.code}"})
        except Exception as exc:  # red, timeout
            entry.update({"estado": f"error: {exc}"})
        report.append(entry)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    bad = [r for r in report if r["estado"] != "ok"]
    print(f"DOI verificados: {len(report) - len(bad)}/{len(report)}")
    for r in bad:
        print(f"  {r['clave']:18s} {r['estado']:16s} {r.get('titulo_crossref', '')[:80]}")
    print(f"Reporte: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
