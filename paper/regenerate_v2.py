"""Regenera la evidencia numérica del artículo (revisión G11).

Cierra los hallazgos FON-01 (holdout independiente), FON-05 (Wilcoxon), FON-07
(áreas, porcentajes e IVI) y FON-08 (horizonte 2050) del informe de revisión.

Salida (por defecto ``../../semana 11/articulo``):
    tablas/*.csv          tablas del manuscrito, con unidades y denominadores
    figuras/*.png         figuras a 600 dpi
    resultados_v2.json    fuente única de verdad para todas las cifras del texto

Uso:
    backend/.venv/Scripts/python.exe paper/regenerate_v2.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.ml import crispdm as C  # noqa: E402
from app.ml.hybrid_dataset import (  # noqa: E402
    MANGROVE_HA,
    SNLMT_TOTAL_HA,
    build_hybrid_dataset,
    load_gmw_series,
    load_reference_data,
    load_species_table,
)
from scenario_analysis import (  # noqa: E402
    band_by_scenario,
    fig_hypothesis_scenarios,
    parameter_sensitivity,
    theoretical_bounds,
)

N_SAMPLES = 2000
SEED = 42
HOLDOUT_SEED = 43
CV_FOLDS = 10
N_BOOT = 2000


def _paired_diffs(results, a: str, b: str) -> np.ndarray:
    return np.asarray(results[a].cv_scores) - np.asarray(results[b].cv_scores)


def _wilcoxon_folds(results, a: str, b: str) -> dict:
    from scipy import stats

    d = _paired_diffs(results, a, b)
    nz = d[~np.isclose(d, 0.0)]
    if nz.size == 0:
        return {"stat": None, "p": None, "n_no_nulas": 0, "nota": "diferencias nulas"}
    stat, p = stats.wilcoxon(nz)
    return {
        "stat": round(float(stat), 4),
        "p": round(float(p), 6),
        "n_no_nulas": int(nz.size),
    }


def _cohen_d(results, a: str, b: str) -> float:
    d = _paired_diffs(results, a, b)
    sd = d.std(ddof=1)
    return float(d.mean() / sd) if sd else float("inf")


def _bootstrap_mean_ci(values: np.ndarray, n_boot: int = N_BOOT, seed: int = SEED) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), (n_boot, len(values)))
    means = values[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _eda_table(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "restoration_level",
        "sea_level_rise_code",
        "horizon_year",
        "baseline_area_ha",
        "baseline_carbon_density",
        "ndvi",
        "horizon_variation_pct",
        "horizon_carbon_tC",
    ]
    data = df.copy()
    data["sea_level_rise_code"] = data["sea_level_rise"].map(C.SLR_CODE).astype(float)
    out = (
        pd.DataFrame(
            {
                "n": data[cols].count(),
                "media": data[cols].mean(),
                "mediana": data[cols].median(),
                "desv_std": data[cols].std(),
                "min": data[cols].min(),
                "max": data[cols].max(),
            }
        )
        .round(3)
        .reset_index()
        .rename(columns={"index": "variable"})
    )
    return out


def _largest_remainder(values: list[float], total: float = 100.0) -> list[float]:
    """Reparte ``total`` en porcentajes de dos decimales que suman exacto.

    Método del mayor residuo: trunca a dos decimales y entrega las centésimas
    sobrantes a las clases con mayor fracción descartada.
    """
    exact = [total * v / sum(values) for v in values]
    cents = [int(v * 100) for v in exact]
    missing = int(round(total * 100)) - sum(cents)
    order = sorted(range(len(values)), key=lambda i: exact[i] * 100 - cents[i], reverse=True)
    for i in order[:missing]:
        cents[i] += 1
    return [c / 100 for c in cents]


def _reference_table() -> pd.DataFrame:
    ref = load_reference_data()
    pct = _largest_remainder([float(v) for v in ref["area_ha"]])
    ref = ref.assign(pct_area=pct)
    total = pd.DataFrame(
        [
            {
                "clase_cobertura": "total",
                "ndvi_min": np.nan,
                "ndvi_max": np.nan,
                "ndvi_medio": np.nan,
                "area_ha": round(float(ref["area_ha"].sum()), 2),
                "es_manglar": np.nan,
                "pct_area": 100.0,
            }
        ]
    )
    return pd.concat([ref, total], ignore_index=True)


def _species_table() -> pd.DataFrame:
    return load_species_table()


# --- Traducción de tablas para la versión en inglés -------------------------

EN_COLUMNS = {
    "tab01_cobertura_snlmt.csv": {
        "clase_cobertura": "Cover class",
        "ndvi_min": "NDVI min",
        "ndvi_max": "NDVI max",
        "ndvi_medio": "NDVI mean",
        "area_ha": "Area (ha)",
        "es_manglar": "Mangrove",
        "pct_area": "Share (%)",
    },
    "tab02_gmw_serie.csv": {
        "anio": "Year",
        "extension_ha": "Extent (ha)",
        "data_source": "Data source",
        "fuente": "Source",
    },
    "tab03_especies_ivi.csv": {
        "franja": "Band",
        "especie_dominante": "Dominant species",
        "ivi_pct": "IVI (%)",
        "especies_acompanantes": "Companion species",
        "fuente": "Source",
    },
    "tab04_eda_descriptivo.csv": {
        "variable": "Variable",
        "media": "Mean",
        "mediana": "Median",
        "desv_std": "SD",
        "min": "Min",
        "max": "Max",
    },
    "tab05_comparacion_modelos.csv": {
        "modelo": "Model",
        "r2_prueba": "Test R²",
        "mae_prueba_pp": "Test MAE (pp)",
        "rmse_prueba_pp": "Test RMSE (pp)",
        "r2_cv_media": "CV R² (mean)",
        "r2_holdout": "Holdout R²",
        "mae_holdout_pp": "Holdout MAE (pp)",
    },
    "tab06_pruebas_estadisticas.csv": {
        "comparacion": "Comparison",
        "t_pareada": "Paired t",
        "p_t": "p (t)",
        "cohen_d": "Cohen's d",
        "wilcoxon_folds": "Wilcoxon W",
        "p_wilcoxon_folds": "p (Wilcoxon)",
        "n_dif_no_nulas": "Non-zero differences",
        "dif_mae_pp": "ΔMAE (pp)",
    },
    "tab07_importancia_variables.csv": {
        "variable": "Variable",
        "importancia_media_r2": "Mean importance (R² drop)",
        "desv_std_r2": "SD",
    },
    "tab08_evidencia_hipotesis.csv": {
        "tramo_restauracion": "Restoration band",
        "variacion_media_pct": "Mean change (%)",
        "variacion_mediana_pct": "Median change (%)",
        "pct_cumple_hipotesis_pct": "Share above +25 % (%)",
        "ic95_lo": "95 % CI low",
        "ic95_hi": "95 % CI high",
    },
    "tab09_intervalos_confianza.csv": {
        "modelo": "Model",
        "mae_media_pp": "Mean MAE (pp)",
        "ic95_lo_pp": "95 % CI low (pp)",
        "ic95_hi_pp": "95 % CI high (pp)",
    },
    "tab10_hipotesis_por_escenario.csv": {
        "tramo": "Band (%)",
        "escenario": "SLR scenario",
        "variacion_media_pct": "Mean change (%)",
        "ic95_lo_pct": "95 % CI low",
        "ic95_hi_pct": "95 % CI high",
        "pct_sobre_umbral": "% above +25",
    },
    "tab11_sensibilidad.csv": {
        "pct_sobre_umbral_tramo_alto": "Share above threshold, high band (%)",
        "maximo_bajo_pct": "Max, low SLR (%)",
        "maximo_medio_pct": "Max, medium SLR (%)",
        "maximo_alto_pct": "Max, high SLR (%)",
        "restauracion_minima_bajo_pct": "Min. restoration, low SLR (%)",
    },
    "tab12_limites_teoricos.csv": {
        "escenario": "SLR scenario",
        "maximo_teorico_pct": "Theoretical maximum (%)",
        "restauracion_minima_pct": "Minimum restoration (%)",
    },
}

EN_MODELS = {
    "Regresión lineal (base)": "Linear regression (baseline)",
    "Ridge (regularizado)": "Ridge (regularized)",
}

EN_CLASSES = {
    "cuerpos_agua": "Water bodies",
    "salitrosas_banco_arena": "Salt flats and sand banks",
    "bosque_seco_semidenso": "Semi-dense dry forest",
    "bosque_seco_denso": "Dense dry forest",
    "manglar_franja_baja": "Low mangrove band",
    "manglar_franja_media": "Medium mangrove band",
    "manglar_franja_alta": "High mangrove band",
    "total": "Total",
}

EN_VARIABLES = {
    "restoration_level": "Restoration level (%)",
    "sea_level_rise_code": "SLR scenario code (0–2)",
    "horizon_year": "Horizon year",
    "baseline_area_ha": "Baseline area (ha)",
    "baseline_carbon_density": "Carbon density (tC/ha)",
    "ndvi": "NDVI",
    "horizon_variation_pct": "Change in retained carbon (%)",
    "horizon_carbon_tC": "Retained carbon at horizon (tC)",
    "sea_level_rise": "SLR scenario",
}

EN_SLR = {"bajo": "low", "medio": "medium", "alto": "high", "todos": "all"}
EN_BANDS = {"franja baja": "low band", "franja media": "medium band", "franja alta": "high band"}


def translate_table(name: str, frame: pd.DataFrame) -> pd.DataFrame:
    """Renombra columnas y valores al inglés para el manuscrito."""
    out = frame.copy()
    out = out.rename(columns=EN_COLUMNS.get(name, {}))
    if name == "tab01_cobertura_snlmt.csv" and "Cover class" in out:
        out["Cover class"] = out["Cover class"].replace(EN_CLASSES)
        if "Mangrove" in out:
            out["Mangrove"] = out["Mangrove"].map(
                lambda v: "—" if pd.isna(v) else ("Yes" if bool(v) else "No")
            )
    if name.endswith("comparacion_modelos.csv") and "Model" in out:
        out["Model"] = out["Model"].replace(EN_MODELS)
    if name.endswith("pruebas_estadisticas.csv") and "Comparison" in out:
        for es, en in EN_MODELS.items():
            out["Comparison"] = out["Comparison"].str.replace(es, en, regex=False)
    if name == "tab04_eda_descriptivo.csv" and "Variable" in out:
        out["Variable"] = out["Variable"].replace(EN_VARIABLES)
    if name == "tab07_importancia_variables.csv" and "Variable" in out:
        out["Variable"] = out["Variable"].replace(EN_VARIABLES)
    if name == "tab09_intervalos_confianza.csv" and "Model" in out:
        out["Model"] = out["Model"].replace(EN_MODELS)
    if name == "tab03_especies_ivi.csv" and "Band" in out:
        out["Band"] = out["Band"].replace(EN_BANDS)
        out["Companion species"] = out["Companion species"].astype(str).str.replace(
            r"(\d),(\d)", r"\1.\2", regex=True
        )
    if name == "tab02_gmw_serie.csv" and "Data source" in out:
        out["Data source"] = out["Data source"].replace({"real": "observed"})
    if "SLR scenario" in out:
        out["SLR scenario"] = out["SLR scenario"].replace(EN_SLR)
    # Dos decimales fijos en las columnas de porcentaje y área.
    for column in ("Share (%)", "Area (ha)", "Mean change (%)", "95 % CI low", "95 % CI high",
                   "% above +25"):
        if column in out:
            out[column] = out[column].map(
                lambda v: "—" if pd.isna(v) else f"{float(v):.2f}"
            )
    return out.fillna("—")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT.parent.parent / "semana 11" / "articulo",
    )
    ap.add_argument(
        "--lang",
        choices=("es", "en"),
        default="es",
        help="Idioma de tablas, figuras y nombres de modelo.",
    )
    args = ap.parse_args(argv)
    fig_dir = args.out / "figuras"
    tab_dir = args.out / "tablas"
    fig_dir.mkdir(parents=True, exist_ok=True)
    tab_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/6] Dataset de modelado (n={N_SAMPLES}, seed={SEED}, horizonte=2050)")
    df = build_hybrid_dataset(n_samples=N_SAMPLES, seed=SEED, horizon_year=2050)

    print(f"[2/6] Entrenamiento y validación cruzada ({CV_FOLDS} particiones)")
    results = C.train_and_evaluate(df, cv_folds=CV_FOLDS, seed=SEED)
    best_name, best = C.select_best_model(results)
    comparison = C.model_comparison_table(results)

    print(f"[3/6] Holdout independiente del motor (seed={HOLDOUT_SEED})")
    hold = build_hybrid_dataset(n_samples=N_SAMPLES, seed=HOLDOUT_SEED, horizon_year=2050)
    Xh, yh = C.prepare_features(hold)
    hold_rows = []
    for name, res in results.items():
        pred = res.pipeline.predict(Xh)
        m = C._metrics(yh.to_numpy(), np.asarray(pred, dtype=float))
        hold_rows.append(
            {
                "modelo": name,
                "r2_holdout": round(m["r2"], 4),
                "mae_holdout_pp": round(m["mae"], 3),
                "rmse_holdout_pp": round(m["rmse"], 3),
            }
        )
    hold_tbl = pd.DataFrame(hold_rows)
    comparison = comparison.merge(hold_tbl, on="modelo", how="left")
    comparison = comparison.rename(
        columns={
            "r2_test": "r2_prueba",
            "mae_test": "mae_prueba_pp",
            "rmse_test": "rmse_prueba_pp",
            "cv_r2_media": "r2_cv_media",
            "cv_r2_desv": "r2_cv_desv",
        }
    )

    print("[4/6] Pruebas estadísticas e intervalos de confianza")
    rows = []
    for name in results:
        if name == best_name:
            continue
        tt = C.paired_ttest(results, best_name, name)
        wf = _wilcoxon_folds(results, best_name, name)
        rows.append(
            {
                "comparacion": f"{best_name} vs {name}",
                "t_pareada": round(tt["t"], 3),
                "p_t": f"{tt['p']:.2e}",
                "cohen_d": round(_cohen_d(results, best_name, name), 2),
                "wilcoxon_folds": wf["stat"],
                "p_wilcoxon_folds": wf["p"],
                "n_dif_no_nulas": wf["n_no_nulas"],
                "dif_mae_pp": round(
                    float(results[name].metrics["mae"] - results[best_name].metrics["mae"]), 3
                ),
            }
        )
    stats_tbl = pd.DataFrame(rows)

    boot_rows = []
    for name, res in results.items():
        b = C.bootstrap_ci(res.y_test, res.y_pred_test, n_boot=500, seed=SEED)
        boot_rows.append(
            {
                "modelo": name,
                "mae_media_pp": round(b["mae_media"], 4),
                "ic95_lo_pp": round(b["ic95_lo"], 4),
                "ic95_hi_pp": round(b["ic95_hi"], 4),
            }
        )
    boot_tbl = pd.DataFrame(boot_rows)

    importance = C.permutation_importance_table(best, df, n_repeats=10, seed=SEED)
    importance = importance.rename(
        columns={"importancia_media": "importancia_media_r2", "desv_std": "desv_std_r2"}
    )

    evidence = C.hypothesis_evidence(df)
    band_slr = band_by_scenario(df)
    band_slr = band_slr.astype({"tramo": str, "escenario": str})
    glob_lo, glob_hi = _bootstrap_mean_ci(df["horizon_variation_pct"].to_numpy())
    band_slr = pd.concat(
        [
            band_slr,
            pd.DataFrame(
                [
                    {
                        "tramo": "Total",
                        "escenario": "todos" if args.lang == "es" else "all",
                        "n": int(len(df)),
                        "variacion_media_pct": round(float(df["horizon_variation_pct"].mean()), 2),
                        "ic95_lo_pct": round(glob_lo, 2),
                        "ic95_hi_pct": round(glob_hi, 2),
                        "pct_sobre_umbral": round(100 * float(df["meets_hypothesis"].mean()), 2),
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    bounds = theoretical_bounds()
    sensitivity = parameter_sensitivity(df)
    noise_rng = np.random.default_rng(SEED)
    noisy = df.copy()
    noisy[C.TARGET] = noisy[C.TARGET] + noise_rng.normal(0.0, 2.0, len(noisy))
    noisy_metrics = C.train_and_evaluate(noisy, cv_folds=CV_FOLDS, seed=SEED)[best_name].metrics
    ci_rows = []
    for band, group in df.groupby(
        pd.cut(
            df["restoration_level"],
            bins=[-0.01, 25, 50, 75, 100.01],
            labels=["0-25 %", "25-50 %", "50-75 %", "75-100 %"],
        ),
        observed=True,
    ):
        lo, hi = _bootstrap_mean_ci(group["horizon_variation_pct"].to_numpy())
        ci_rows.append({"tramo_restauracion": str(band), "ic95_lo": round(lo, 2), "ic95_hi": round(hi, 2)})
    evidence = evidence.merge(pd.DataFrame(ci_rows), on="tramo_restauracion", how="left")
    evidence = evidence.rename(
        columns={
            "variacion_media": "variacion_media_pct",
            "variacion_mediana": "variacion_mediana_pct",
            "pct_cumple_hipotesis": "pct_cumple_hipotesis_pct",
        }
    )

    print("[5/6] Figuras (600 dpi)")
    comp_for_fig = comparison.copy()
    if args.lang == "en":
        comp_for_fig["modelo"] = comp_for_fig["modelo"].replace(EN_MODELS)
    figures = {
        "fig01_tendencia_gmw.png": C.fig_gmw_trend(load_gmw_series(), lang=args.lang),
        "fig02_distribuciones.png": C.fig_distributions(df, lang=args.lang),
        "fig04_comparacion_modelos.png": C.fig_model_comparison(
            comp_for_fig.rename(columns={"r2_prueba": "r2_test", "r2_cv_media": "cv_r2_media"}),
            lang=args.lang,
        ),
        "fig05_predicho_observado.png": C.fig_predicted_vs_actual(best, lang=args.lang),
        "fig06_residuales.png": C.fig_residuals(best, lang=args.lang),
        "fig07_importancia.png": C.fig_feature_importance(
            importance.assign(n_folds=CV_FOLDS).rename(
                columns={"importancia_media_r2": "importancia_media", "desv_std_r2": "desv_std"}
            ),
            lang=args.lang,
        ),
        "fig08_hipotesis.png": fig_hypothesis_scenarios(band_slr, lang=args.lang),
    }
    for name, data in figures.items():
        (fig_dir / name).write_bytes(data)

    print("[6/6] Tablas y resumen")
    comp_cols = [
        "modelo",
        "r2_prueba",
        "mae_prueba_pp",
        "rmse_prueba_pp",
        "r2_cv_media",
        "r2_holdout",
        "mae_holdout_pp",
    ]
    tables = {
        "tab01_cobertura_snlmt.csv": _reference_table(),
        "tab02_gmw_serie.csv": load_gmw_series(),
        "tab03_especies_ivi.csv": _species_table(),
        "tab04_eda_descriptivo.csv": _eda_table(df),
        "tab05_comparacion_modelos.csv": comparison[comp_cols],
        "tab06_pruebas_estadisticas.csv": stats_tbl,
        "tab07_importancia_variables.csv": importance,
        "tab08_evidencia_hipotesis.csv": evidence,
        "tab09_intervalos_confianza.csv": boot_tbl,
        "tab10_hipotesis_por_escenario.csv": band_slr,
        "tab11_sensibilidad.csv": sensitivity,
        "tab12_limites_teoricos.csv": bounds,
    }
    for name, frame in tables.items():
        if args.lang == "en":
            frame = translate_table(name, frame)
        frame.to_csv(tab_dir / name, index=False)

    norm = C.residual_normality(best.y_test, best.y_pred_test)
    boot_best = C.bootstrap_ci(best.y_test, best.y_pred_test, n_boot=500, seed=SEED)
    resumen = {
        "dataset": {
            "n_registros": int(len(df)),
            "semilla": SEED,
            "semilla_holdout": HOLDOUT_SEED,
            "horizonte": 2050,
            "atributos": C.FEATURES,
            "objetivo": C.TARGET,
        },
        "areas": {
            "total_ha": SNLMT_TOTAL_HA,
            "manglar_ha": MANGROVE_HA,
            "manglar_pct": round(100 * MANGROVE_HA / SNLMT_TOTAL_HA, 2),
            "suma_clases_ha": round(float(load_reference_data()["area_ha"].sum()), 2),
        },
        "mejor_modelo": best_name,
        "metricas_prueba": {k: round(v, 4) for k, v in best.metrics.items()},
        "cv_r2_media": round(float(best.cv_scores.mean()), 4),
        "cv_r2_desv": round(float(best.cv_scores.std()), 4),
        "bootstrap_mae": {k: round(v, 4) for k, v in boot_best.items()},
        "normalidad_residuales": {k: round(v, 6) for k, v in norm.items()},
        "comparacion": comparison.to_dict(orient="records"),
        "pruebas_estadisticas": stats_tbl.to_dict(orient="records"),
        "intervalos_confianza": boot_tbl.to_dict(orient="records"),
        "importancia": importance.to_dict(orient="records"),
        "evidencia_hipotesis": evidence.to_dict(orient="records"),
        "hipotesis": {
            "umbral_pct": C.HYPOTHESIS_THRESHOLD,
            "pct_global_cumple": round(100 * float(df["meets_hypothesis"].mean()), 2),
            "variacion_media_global_pct": round(float(df["horizon_variation_pct"].mean()), 2),
        },
        "escenarios": band_slr.to_dict(orient="records"),
        "limites_teoricos": bounds.to_dict(orient="records"),
        "sensibilidad": sensitivity.to_dict(orient="records"),
        "ruido_objetivo": {
            "sigma_pp": 2.0,
            "r2": round(noisy_metrics["r2"], 4),
            "mae_pp": round(noisy_metrics["mae"], 4),
            "rmse_pp": round(noisy_metrics["rmse"], 4),
        },
    }
    (tab_dir / "resultados_v2.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nMejor modelo: {best_name}")
    print(
        f"R2 prueba: {best.metrics['r2']:.4f} | MAE: {best.metrics['mae']:.3f} pp | "
        f"CV R2: {best.cv_scores.mean():.4f}"
    )
    print(f"Salida: {tab_dir} y {fig_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
