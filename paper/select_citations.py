"""Selecciona las citas textuales más útiles para el artículo.

Agrupa por función retórica: definición de gemelo digital, brecha de
investigación, arquitectura, validación, incertidumbre, restauración de
humedales y gobernanza. Devuelve la mejor cita por artículo y función.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
TXT = BASE / "references_txt"
TAB = BASE / "tables"

# Funciones retóricas y sus patrones. El orden importa: se asigna la primera.
FUNCIONES = {
 "definicion": [
   r"digital twin[s]? (?:is|are|can be|refers to|as a|describes)",
   r"we (?:define|understand) (?:a )?digital twin",
   r"(?:a|the) digital twin (?:concept|approach|idea)",
   r"virtual (?:representation|replica|counterpart) of",
 ],
 "brecha": [
   r"(?:remain|is|are|still) (?:limited|unclear|scarce|lacking|rare|absent)",
   r"(?:little|few|no) (?:is known|studies|research|attention)",
   r"gap (?:in|between)",
   r"(?:however|nevertheless|despite)[^.]{0,110}(?:lack|limit|challeng|barrier)",
 ],
 "arquitectura": [
   r"(?:modular|interoperab|federat|scalab|microservice)[^.]{0,110}(?:architect|framework|design|platform)",
   r"(?:propose|present|develop)[^.]{0,60}(?:architecture|framework|platform)",
 ],
 "datos": [
   r"(?:real[- ]time|continuous)[^.]{0,70}(?:data|monitor|observ)",
   r"(?:integrat|combin|fus)[^.]{0,70}(?:data|observation|model)",
   r"remote sensing[^.]{0,90}",
 ],
 "modelado": [
   r"(?:physics[- ]informed|surrogate|emulator)[^.]{0,100}",
   r"(?:machine learning|neural network)[^.]{0,90}(?:model|predict|surrogate)",
   r"(?:calibrat|train)[^.]{0,80}(?:model|parameter)",
 ],
 "incertidumbre": [
   r"uncertaint[^.]{0,110}",
   r"(?:validat|verif)[^.]{0,100}(?:model|result|data)",
 ],
 "humedales": [
   r"wetland[^.]{0,120}",
   r"(?:restoration|restore)[^.]{0,110}",
   r"mangrove[^.]{0,110}",
   r"sea[- ]level rise[^.]{0,100}",
 ],
 "carbono": [
   r"carbon (?:sequestrat|accumulat|stock|storage)[^.]{0,100}",
   r"blue carbon[^.]{0,100}",
   r"ecosystem service[^.]{0,100}",
 ],
 "gobernanza": [
   r"(?:stakeholder|policymak|decision[- ]mak|governance)[^.]{0,110}",
   r"(?:participat|engagement|co-?design)[^.]{0,100}",
 ],
}

DESCARTES = [
 r"\bet al\.,", r"https?://", r"doi:", r"^\d+\.", r"figure \d", r"table \d",
 r"see (?:section|figure|table)", r"copyright", r"all rights reserved",
]


def oraciones(text: str) -> list[str]:
    text = re.sub(r"\n+", " ", text)
    partes = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text)
    out = []
    for p in partes:
        p = p.strip()
        if not (90 <= len(p) <= 350):
            continue
        if any(re.search(d, p, re.IGNORECASE) for d in DESCARTES):
            continue
        if p.count("(") > 3 or p.count("[") > 2:
            continue
        # Se descartan fragmentos mayormente numéricos o de tabla.
        if len(re.findall(r"\d", p)) > len(p) * 0.18:
            continue
        out.append(p)
    return out


def puntaje(s: str, func: str) -> float:
    sc = 0.0
    for pat in FUNCIONES[func]:
        if re.search(pat, s, re.IGNORECASE):
            sc += 1.0
    # Preferencia por voz activa y verbos de aporte.
    if re.search(r"\b(?:we|this (?:paper|study|work))\b", s, re.IGNORECASE):
        sc += 0.6
    if re.search(r"\b(?:demonstrat|show|propose|present|argue|highlight)\w*", s, re.IGNORECASE):
        sc += 0.5
    if len(s) < 150:
        sc += 0.25
    return sc


def main() -> int:
    refs = {}
    for line in (BASE / "references.txt").read_text(encoding="utf-8").split("\n"):
        if "|" in line and not line.startswith("#"):
            k, _, v = line.partition("|")
            refs[k.strip()] = v.strip()

    biblio = json.loads((TAB / "bibliografia.json").read_text(encoding="utf-8"))
    por_slug = {b["slug"]: b for b in biblio}

    dossier = []
    for clave, ref in refs.items():
        # Localizar el archivo correspondiente por apellido y año.
        apellido = re.split(r"[ ,]", ref)[0].lower()
        anio = ""
        m = re.search(r"\((\d{4})\)", ref)
        if m:
            anio = m.group(1)
        match = None
        for b in biblio:
            a = b["autores"].lower()
            if apellido[:6] in a and b["anio"] == anio:
                match = b
                break
        if not match:
            continue

        path = TXT / f"{match['slug']}.txt"
        if not path.exists():
            continue
        sents = oraciones(path.read_text(encoding="utf-8"))

        mejores = {}
        for func in FUNCIONES:
            cands = [(puntaje(s, func), s) for s in sents]
            cands = [c for c in cands if c[0] >= 1.4]
            if cands:
                cands.sort(key=lambda x: -x[0])
                mejores[func] = {"score": round(cands[0][0], 2), "texto": cands[0][1]}

        dossier.append({
            "clave": clave,
            "referencia": ref,
            "archivo": match["archivo"],
            "funciones": mejores,
        })

    (TAB / "citas_por_funcion.json").write_text(
        json.dumps(dossier, ensure_ascii=False, indent=2), encoding="utf-8")

    # Resumen de cobertura por función.
    from collections import Counter
    c = Counter()
    for d in dossier:
        for f in d["funciones"]:
            c[f] += 1
    print(f"Artículos con citas clasificadas: {len(dossier)}\n")
    print("Cobertura por función retórica:")
    for f, n in c.most_common():
        print(f"  {n:>2}  {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
