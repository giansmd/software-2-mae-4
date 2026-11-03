"""Exporta el dataset híbrido y su diccionario de variables.

Genera un paquete reproducible para revisores y para el depósito de datos:

    artifacts/dataset/dataset_modelado.csv    semilla 42 (entrenamiento)
    artifacts/dataset/dataset_holdout.csv     semilla 43 (holdout independiente)
    artifacts/dataset/referencia_snlmt.csv    clases de cobertura reales
    artifacts/dataset/especies_ivi.csv        IVI por franja (especie dominante)
    artifacts/dataset/gmw_serie.csv           serie de extensión GMW v3.0
    artifacts/dataset/series_anuales_muestra.csv  trayectorias del motor (2020-2050)
    artifacts/dataset/diccionario_variables.csv
    artifacts/dataset/LEEME.md

Uso:
    backend/.venv/Scripts/python.exe paper/export_dataset.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.ml import crispdm as C  # noqa: E402
from app.ml.hybrid_dataset import (  # noqa: E402
    build_hybrid_dataset,
    load_gmw_series,
    load_reference_data,
    load_species_table,
)
from app.models.scenario import SeaLevelRise  # noqa: E402
from app.simulations.engine import calculate_state  # noqa: E402

OUT = ROOT.parent / "artifacts" / "dataset"
N_SAMPLES = 2000

DICCIONARIO = [
    ("restoration_level", "Nivel de restauración hidrológica", "%", "uniforme 0-100, con 50 % en los extremos"),
    ("sea_level_rise", "Escenario IPCC de ascenso del nivel del mar", "categoría", "low | medium | high"),
    ("horizon_year", "Año horizonte de la proyección", "año", "fijo en 2050"),
    ("baseline_area_ha", "Área efectiva de línea base", "ha", "uniforme 50-300"),
    ("baseline_carbon_density", "Densidad de carbono suelo + biomasa", "tC/ha", "uniforme 50-120"),
    ("ndvi", "NDVI del manglar de franja media", "índice", "uniforme 0,728-0,808"),
    ("month", "Mes de la observación", "mes", "1-12; no se usa como atributo"),
    ("horizon_variation_pct", "Variación porcentual del carbono retenido (objetivo)", "%", "salida del motor"),
    ("horizon_carbon_tC", "Carbono retenido en el horizonte", "tC", "salida del motor"),
    ("meets_hypothesis", "Indicador de variación ≥ +25 %", "0/1", "derivado del objetivo"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    train = build_hybrid_dataset(n_samples=N_SAMPLES, seed=42, horizon_year=2050)
    hold = build_hybrid_dataset(n_samples=N_SAMPLES, seed=43, horizon_year=2050)
    train.to_csv(OUT / "dataset_modelado.csv", index=False)
    hold.to_csv(OUT / "dataset_holdout.csv", index=False)
    load_reference_data().to_csv(OUT / "referencia_snlmt.csv", index=False)
    load_species_table().to_csv(OUT / "especies_ivi.csv", index=False)
    load_gmw_series().to_csv(OUT / "gmw_serie.csv", index=False)

    # Muestra de trayectorias del motor: 4 niveles de restauración x 3 escenarios
    # cada 5 años entre 2020 y 2050, sobre una línea base de 100 ha y 80 tC/ha.
    series = []
    for level in (25.0, 50.0, 75.0, 100.0):
        for scenario in (SeaLevelRise.LOW, SeaLevelRise.MEDIUM, SeaLevelRise.HIGH):
            for year in range(2020, 2051, 5):
                state = calculate_state(
                    restoration_level=level,
                    sea_level_rise=scenario,
                    progress=(year - 2020) / 30.0,
                    baseline_area_ha=100.0,
                    baseline_carbon_density=80.0,
                )
                series.append(
                    {
                        "year": year,
                        "restoration_level_pct": level,
                        "sea_level_rise": scenario.value,
                        "baseline_area_ha": 100.0,
                        "baseline_carbon_density_tC_ha": 80.0,
                        "retained_carbon_tC": state["retained_carbon"],
                        "variation_pct": state["variation_pct"],
                    }
                )

    import pandas as pd

    pd.DataFrame(series).to_csv(OUT / "series_anuales_muestra.csv", index=False)

    pd.DataFrame(DICCIONARIO, columns=["variable", "descripcion", "unidad", "valores"]).to_csv(
        OUT / "diccionario_variables.csv", index=False
    )

    (OUT / "LEEME.md").write_text(
        "# Dataset híbrido MAE-4\n\n"
        "Covariables reales publicadas del SNLMT y variable objetivo generada por el motor\n"
        "determinista. Semillas 42 (modelado) y 43 (holdout independiente), horizonte 2050.\n\n"
        f"Atributos del modelo: {', '.join(C.FEATURES)}.\n"
        "Objetivo: " + C.TARGET + ".\n\n"
        "Incluye una muestra de trayectorias anuales del motor (2020-2050) sobre una\n"
        "línea base de 100 ha y 80 tC/ha.\n\n"
        "Regenerar con `paper/regenerate_v2.py` (figuras y tablas) o `paper/export_dataset.py`\n"
        "(este paquete). Licencia del software: MIT. GMW v3.0: CC BY 4.0.\n",
        encoding="utf-8",
    )

    print(f"Exportado en {OUT}")
    for path in sorted(OUT.glob("*")):
        print(f"  {path.name} ({path.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
