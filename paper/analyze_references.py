"""Analiza los 40 artículos: clasifica su aporte y extrae citas de alta calidad.

Produce un dossier por artículo con: tema, definiciones clave, hallazgos
citables y la sección del manuscrito donde encaja.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
TXT = BASE / "references_txt"
TAB = BASE / "tables"

# Ejes temáticos que estructuran el marco teórico y la discusión.
EJES = {
    "definicion_dt": [
        r"digital twin",
        r"physical (?:counterpart|entity|asset)",
        r"virtual (?:representation|replica|counterpart)",
    ],
    "arquitectura": [
        r"architecture", r"framework", r"modular", r"edge comput",
        r"interoperab", r"federat", r"middleware", r"API",
    ],
    "datos_sensores": [
        r"sensor", r"remote sensing", r"satellite", r"in situ",
        r"data (?:stream|pipeline|infrastructure|assimilation)",
        r"real[- ]time data", r"IoT",
    ],
    "modelado_simulacion": [
        r"physics[- ]informed", r"surrogate", r"simulat", r"numerical model",
        r"machine learning", r"neural network", r"emulator", r"calibrat",
    ],
    "incertidumbre_validacion": [
        r"uncertaint", r"validat", r"verificat", r"error", r"bias",
        r"confidence interval", r"propagat",
    ],
    "gobernanza_social": [
        r"governance", r"stakeholder", r"participat", r"policy",
        r"decision[- ]mak", r"citizen", r"ethic",
    ],
    "humedales_restauracion": [
        r"wetland", r"mangrove", r"restoration", r"hydrolog",
        r"coastal", r"blue carbon", r"sea[- ]level",
    ],
    "carbono_ecosistemas": [
        r"carbon", r"sequestrat", r"greenhouse gas", r"emission",
        r"ecosystem service",
    ],
}

# Marcadores de alta calidad argumental.
MARCADORES = [
    r"we (?:define|propose|argue|demonstrate|show)",
    r"this (?:study|paper|work) (?:presents|proposes|shows|demonstrates)",
    r"however,", r"nevertheless,", r"despite",
    r"(?:key|main|major) (?:challenge|limitation|gap|finding|contribution)",
    r"future (?:work|research|directions)",
    r"remains? (?:unclear|challenging|limited)",
]


def sentences(text: str) -> list[str]:
    text = re.sub(r"\n+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text)
    out = []
    for p in parts:
        p = p.strip()
        # Se descartan oraciones con ruido de referencias o tablas.
        if not (80 <= len(p) <= 380):
            continue
        if len(re.findall(r"\b(?:19|20)\d{2}\b", p)) > 3:
            continue
        if re.search(r"(?:et al\.,|doi:|https?://)", p):
            continue
        if p.count("(") > 4:
            continue
        out.append(p)
    return out


def score(sent: str, eje: str) -> float:
    """Prioriza oraciones con contenido argumental y densidad conceptual."""
    s = 0.0
    low = sent.lower()
    for pat in EJES[eje]:
        if re.search(pat, low):
            s += 1.0
    for pat in MARCADORES:
        if re.search(pat, low):
            s += 1.5
    # Penaliza fragmentos que son claramente de referencias.
    if low.count("(") > 2:
        s -= 0.5
    if len(sent) > 300:
        s -= 0.3
    return s


def main() -> int:
    biblio = json.loads((TAB / "bibliografia.json").read_text(encoding="utf-8"))
    dossier = []

    for b in biblio:
        path = TXT / f"{b['slug']}.txt"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        sents = sentences(text)

        por_eje: dict[str, list[dict]] = defaultdict(list)
        for eje in EJES:
            for sent in sents:
                sc = score(sent, eje)
                if sc >= 2.0:
                    por_eje[eje].append({"score": round(sc, 2), "oracion": sent})

        resumen: dict[str, list[str]] = {}
        for eje, lst in por_eje.items():
            lst.sort(key=lambda x: -x["score"])
            resumen[eje] = [x["oracion"] for x in lst[:4]]

        ejes_dominantes = sorted(resumen, key=lambda e: -len(resumen[e]))[:3]

        dossier.append({
            "slug": b["slug"],
            "archivo": b["archivo"],
            "autores": b["autores"],
            "anio": b["anio"],
            "titulo": b["titulo"],
            "doi": b["doi"],
            "ejes_dominantes": ejes_dominantes,
            "citas_por_eje": resumen,
        })

    (TAB / "dossier_referencias.json").write_text(
        json.dumps(dossier, ensure_ascii=False, indent=2), encoding="utf-8")

    # Resumen legible
    print(f"Artículos analizados: {len(dossier)}\n")
    conteo = defaultdict(int)
    for d in dossier:
        for e in d["ejes_dominantes"]:
            conteo[e] += 1
    print("Artículos por eje dominante:")
    for e, n in sorted(conteo.items(), key=lambda x: -x[1]):
        print(f"  {n:>2}  {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
