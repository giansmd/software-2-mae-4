"""Análisis por escenario de ascenso del nivel del mar y sensibilidad del motor.

Responde a la revisión A1/A3: el umbral del +25 % es alcanzable solo en el
escenario bajo, y ese resultado depende de los parámetros del motor.

Salida (la consume ``regenerate_v2.py``):
    band_by_scenario(df)        media, IC 95 % y % sobre el umbral por tramo × escenario
    parameter_sensitivity(df)   barrido de Bmax y k (±20 %)
    theoretical_bounds()        máximo teórico y restauración mínima por escenario
    fig_hypothesis_scenarios()  figura de barras agrupadas
"""
from __future__ import annotations

import io
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.models.scenario import SeaLevelRise  # noqa: E402
from app.simulations.engine import DEFAULT_PARAMS, calculate_state  # noqa: E402

BANDS = [(-0.01, 25, "0-25 %"), (25, 50, "25-50 %"), (50, 75, "50-75 %"), (75, 100.01, "75-100 %")]
SLR_NAMES = {"low": "bajo", "medium": "medio", "high": "alto"}
SLR_ENUM = {"low": SeaLevelRise.LOW, "medium": SeaLevelRise.MEDIUM, "high": SeaLevelRise.HIGH}
LOSS_KEYS = {
    "low": ("slr_area_loss_low", "slr_density_loss_low"),
    "medium": ("slr_area_loss_medium", "slr_density_loss_medium"),
    "high": ("slr_area_loss_high", "slr_density_loss_high"),
}
THRESHOLD = 25.0


def _band(series: pd.Series) -> pd.Series:
    return pd.cut(series, bins=[b[0] for b in BANDS] + [100.01], labels=[b[2] for b in BANDS])


def _mean_ci(values: np.ndarray, n_boot: int = 2000, seed: int = 42) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), (n_boot, len(values)))
    means = values[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def band_by_scenario(df: pd.DataFrame) -> pd.DataFrame:
    """Media, IC 95 % y proporción de registros sobre el umbral por tramo y escenario."""
    data = df.copy()
    data["tramo"] = _band(data["restoration_level"])
    rows = []
    for (band, slr), group in data.groupby(["tramo", "sea_level_rise"], observed=True):
        values = group["horizon_variation_pct"].to_numpy()
        lo, hi = _mean_ci(values)
        rows.append(
            {
                "tramo": str(band),
                "escenario": SLR_NAMES.get(str(slr), str(slr)),
                "n": int(len(values)),
                "variacion_media_pct": round(float(values.mean()), 2),
                "ic95_lo_pct": round(lo, 2),
                "ic95_hi_pct": round(hi, 2),
                "pct_sobre_umbral": round(100 * float((values >= THRESHOLD).mean()), 2),
            }
        )
    out = pd.DataFrame(rows)
    out["tramo"] = pd.Categorical(out["tramo"], categories=[b[2] for b in BANDS], ordered=True)
    out["escenario"] = pd.Categorical(
        out["escenario"], categories=["bajo", "medio", "alto"], ordered=True
    )
    return out.sort_values(["tramo", "escenario"]).reset_index(drop=True)


def theoretical_bounds(params: dict | None = None) -> pd.DataFrame:
    """Máximo alcanzable y restauración mínima para cruzar +25 %, por escenario."""
    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)
    boost, k = float(p["restoration_boost_max"]), float(p["restoration_k"])
    factor_r1 = boost * (1.0 - math.exp(-k))
    rows = []
    for slr, (area_key, density_key) in LOSS_KEYS.items():
        area_keep = 1.0 - float(p[area_key])
        density_keep = 1.0 - float(p[density_key])
        max_pct = (area_keep * (1.0 + factor_r1) * density_keep - 1.0) * 100
        required = 1.0 + THRESHOLD / 100.0
        factor_needed = required / (area_keep * density_keep) - 1.0
        if factor_needed >= boost:
            r_star = None
        else:
            r_star = round(-math.log(1.0 - factor_needed / boost) / k * 100, 2)
            if r_star > 100.0:
                r_star = None
        rows.append(
            {
                "escenario": SLR_NAMES[slr],
                "maximo_teorico_pct": round(max_pct, 2),
                "restauracion_minima_pct": r_star,
            }
        )
    return pd.DataFrame(rows)


def parameter_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """Barrido de Bmax y k (±20 %): proporción sobre el umbral y umbral de restauración."""
    high = df[df["restoration_level"] >= 75]
    rows = []
    for boost in (0.40, 0.50, 0.60):
        for k in (2.0, 2.5, 3.0):
            params = {"restoration_boost_max": boost, "restoration_k": k}
            values = np.array(
                [
                    calculate_state(
                        restoration_level=float(r),
                        sea_level_rise=SLR_ENUM[str(s)],
                        progress=1.0,
                        baseline_area_ha=1.0,
                        baseline_carbon_density=1.0,
                        params=params,
                    )["variation_pct"]
                    for r, s in zip(high["restoration_level"], high["sea_level_rise"])
                ]
            )
            bounds = theoretical_bounds(params).set_index("escenario")
            rows.append(
                {
                    "bmax": boost,
                    "k": k,
                    "pct_sobre_umbral_tramo_alto": round(100 * float((values >= THRESHOLD).mean()), 2),
                    "maximo_bajo_pct": bounds.loc["bajo", "maximo_teorico_pct"],
                    "maximo_medio_pct": bounds.loc["medio", "maximo_teorico_pct"],
                    "maximo_alto_pct": bounds.loc["alto", "maximo_teorico_pct"],
                    "restauracion_minima_bajo_pct": bounds.loc["bajo", "restauracion_minima_pct"],
                }
            )
    return pd.DataFrame(rows)


SCENARIO_FIG_TEXTS = {
    "es": {
        "label": "ascenso {scenario}",
        "names": {"bajo": "bajo", "medio": "medio", "alto": "alto"},
        "threshold": "umbral +25 %",
        "x": "Tramo de restauración hidrológica",
        "y": "Variación media del carbono retenido (%)",
        "title": "Hipótesis por tramo y escenario de ascenso del nivel del mar",
        "note": "Motor determinista · el umbral solo es alcanzable en el escenario bajo",
    },
    "en": {
        "label": "{scenario} SLR",
        "names": {"bajo": "low", "medio": "medium", "alto": "high"},
        "threshold": "+25 % threshold",
        "x": "Hydrological restoration band",
        "y": "Mean change in retained carbon (%)",
        "title": "Hypothesis by restoration band and sea-level rise scenario",
        "note": "Deterministic engine · the threshold is only reachable in the low scenario",
    },
}


def fig_hypothesis_scenarios(evidence: pd.DataFrame, lang: str = "es") -> bytes:
    """Barras agrupadas por tramo y escenario, con el umbral del +25 %."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t = SCENARIO_FIG_TEXTS.get(lang, SCENARIO_FIG_TEXTS["es"])
    bands = [b[2] for b in BANDS]
    scenarios = ["bajo", "medio", "alto"]
    colors = {"bajo": "#2a6f97", "medio": "#f4a261", "alto": "#e76f51"}
    width = 0.26
    x = np.arange(len(bands))

    fig, ax = plt.subplots(figsize=(9, 5))
    for offset, scenario in zip((-width, 0, width), scenarios):
        subset = evidence[evidence["escenario"] == scenario].set_index("tramo")
        values = [float(subset.loc[b, "variacion_media_pct"]) if b in subset.index else np.nan for b in bands]
        label = t["label"].format(scenario=t["names"][scenario])
        ax.bar(x + offset, values, width, label=label, color=colors[scenario])

    ax.axhline(THRESHOLD, ls="--", color="#6a040f", lw=1.5, label=t["threshold"])
    ax.set_xticks(x)
    ax.set_xticklabels(bands)
    ax.set_xlabel(t["x"])
    ax.set_ylabel(t["y"])
    ax.set_title(t["title"], fontsize=12)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.text(
        0.5,
        0.02,
        t["note"],
        ha="center",
        fontsize=7,
        style="italic",
        color="#666666",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=600, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    buf.seek(0)
    return buf.read()
