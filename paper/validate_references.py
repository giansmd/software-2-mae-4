"""Validación final: todo DOI de references.txt debe resolver al título citado."""
import json
import re
import time
import urllib.request
from pathlib import Path

REFS = Path(__file__).resolve().parent / "references.txt"
UA = {"User-Agent": "mae4/1.0 (mailto:gianfranco.samana@gmail.com)"}


def norm(s: str) -> set[str]:
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return {w for w in s.split() if len(w) > 3}


entradas = []
for line in REFS.read_text(encoding="utf-8").split("\n"):
    line = line.strip()
    if "|" in line and not line.startswith("#"):
        k, _, v = line.partition("|")
        entradas.append((k.strip(), v.strip()))

print(f"Entradas: {len(entradas)}")
print("=" * 96)

ok = fallo = sin_doi = 0
for key, ref in entradas:
    m = re.search(r"https://doi\.org/(\S+)", ref)
    if not m:
        sin_doi += 1
        print(f"{key:16} SIN DOI (se cita sin enlace)")
        continue
    doi = m.group(1)
    try:
        req = urllib.request.Request(f"https://api.crossref.org/works/{doi}", headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            msg = json.load(r)["message"]
        real = (msg.get("title") or [""])[0]
        # Título citado: tras ") . " y antes del punto final del título.
        after = ref.split(")", 1)[1]
        after = after.split("*", 1)[0]
        citado = after.replace(".", " ").strip()
        overlap = len(norm(citado) & norm(real)) / max(1, len(norm(citado)))
        if overlap >= 0.6:
            ok += 1
            print(f"{key:16} OK   [{overlap:.2f}] {real[:60]}")
        else:
            fallo += 1
            print(f"{key:16} MISMATCH [{overlap:.2f}]")
            print(f"      citado: {citado[:70]}")
            print(f"      real  : {real[:70]}")
    except Exception as e:
        fallo += 1
        print(f"{key:16} ERROR {str(e)[:50]}")
    time.sleep(0.15)

print("=" * 96)
print(f"OK={ok}  MISMATCH/ERROR={fallo}  SIN_DOI={sin_doi}")
