"""Genera las figuras y tablas del artículo desde el motor CRISP-DM.

Salida:
    paper/figures/*.png   — figuras numeradas del artículo
    paper/tables/*.csv    — tablas numeradas del artículo
    paper/tables/resumen.json — métricas del run, para la narrativa

Todo se deriva del dataset híbrido real: ninguna cifra se escribe a mano.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.ml import crispdm as C  # noqa: E402
from app.ml.hybrid_dataset import (  # noqa: E402
    build_hybrid_dataset,
    dataset_card,
    load_gmw_series,
    load_reference_data,
    load_species_table,
)

FIG_DIR = ROOT / "figures"
TAB_DIR = ROOT / "tables"
N_SAMPLES = 2000
SEED = 42
CV_FOLDS = 5


def main() -> int:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TAB_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[1/5] Generando dataset híbrido (n={N_SAMPLES}, seed={SEED})…")
    df = build_hybrid_dataset(n_samples=N_SAMPLES, seed=SEED)
    gmw = load_gmw_series()
    ref = load_reference_data()
    species = load_species_table()

    print(f"[2/5] Entrenando y validando ({CV_FOLDS} folds)…")
    results = C.train_and_evaluate(df, cv_folds=CV_FOLDS, seed=SEED)
    best_name, best = C.select_best_model(results)
    comparison = C.model_comparison_table(results)
    stats_tbl = C.statistical_report(results)
    importance = C.permutation_importance_table(best, df)
    evidence = C.hypothesis_evidence(df)
    boot = C.bootstrap_ci(best.y_test, best.y_pred_test)
    norm = C.residual_normality(best.y_test, best.y_pred_test)

    print(f"[3/5] Escribiendo figuras…")
    figures = {
        "fig01_tendencia_gmw.png": C.fig_gmw_trend(gmw),
        "fig02_distribuciones.png": C.fig_distributions(df),
        "fig03_correlacion.png": C.fig_correlation(df),
        "fig04_comparacion_modelos.png": C.fig_model_comparison(comparison),
        "fig05_predicho_observado.png": C.fig_predicted_vs_actual(best),
        "fig06_residuales.png": C.fig_residuals(best),
        "fig07_importancia.png": C.fig_feature_importance(importance),
        "fig08_hipotesis.png": C.fig_hypothesis(evidence),
    }
    for name, data in figures.items():
        (FIG_DIR / name).write_bytes(data)
        print(f"    figura: {name} ({len(data)//1024} KB)")

    print(f"[4/5] Escribiendo tablas…")
    tables = {
        "tab01_referencia_snlmt.csv": ref,
        "tab02_gmw_serie.csv": gmw,
        "tab03_especies_ivi.csv": species,
        "tab04_eda_descriptivo.csv": C.eda_summary(df).reset_index().rename(columns={"index": "variable"}),
        "tab05_comparacion_modelos.csv": comparison,
        "tab06_pruebas_estadisticas.csv": stats_tbl,
        "tab07_importancia_variables.csv": importance,
        "tab08_evidencia_hipotesis.csv": evidence,
    }
    for name, frame in tables.items():
        frame.to_csv(TAB_DIR / name, index=False)
        print(f"    tabla: {name} ({len(frame)} filas)")

    print(f"[5/5] Escribiendo resumen…")
    resumen = {
        "dataset": {
            "n_registros": int(len(df)),
            "n_atributos": len(C.FEATURES),
            "objetivo": C.TARGET,
            "card": dataset_card(),
        },
        "mejor_modelo": best_name,
        "metricas_mejor_modelo": {k: round(v, 4) for k, v in best.metrics.items()},
        "cv_r2_media": round(float(best.cv_scores.mean()), 4),
        "cv_r2_desv": round(float(best.cv_scores.std()), 4),
        "comparacion": comparison.to_dict(orient="records"),
        "pruebas_estadisticas": stats_tbl.to_dict(orient="records"),
        "bootstrap_mae": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in boot.items()},
        "normalidad_residuales": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in norm.items()},
        "importancia": importance.to_dict(orient="records"),
        "evidencia_hipotesis": evidence.to_dict(orient="records"),
        "hipotesis_cumplida": bool(
            (evidence["variacion_media"] >= C.HYPOTHESIS_THRESHOLD).any()
        ),
    }
    (TAB_DIR / "resumen.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nMejor modelo: {best_name}")
    print(f"R² test: {best.metrics['r2']:.4f} | MAE: {best.metrics['mae']:.3f} | CV R²: {best.cv_scores.mean():.4f}")
    print(f"Figuras: {len(figures)} | Tablas: {len(tables)}")
    print(f"Salida: {FIG_DIR} y {TAB_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
