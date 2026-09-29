"""Motor CRISP-DM para el gemelo digital MAE-4 (manglar de Tumbes).

Implementa las seis fases de CRISP-DM sobre el dataset híbrido:

  1. Comprensión del negocio  -> objetivos, hipótesis, criterios de éxito
  2. Comprensión de los datos -> EDA (distribuciones, correlaciones, calidad)
  3. Preparación de los datos -> split, escalado, pipelines sin fuga
  4. Modelado                 -> varios algoritmos, búsqueda acotada
  5. Evaluación               -> validación cruzada, pruebas estadísticas
  6. Despliegue               -> reportes, figuras y tablas reproducibles

Todas las figuras y tablas se generan tanto para pantalla como para reporte.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Any

import matplotlib

matplotlib.use("Agg")  # backend sin display: imprescindible en servidor
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
TARGET = "horizon_variation_pct"
HYPOTHESIS_THRESHOLD = 25.0

FEATURES = [
    "restoration_level",
    "sea_level_rise_code",
    "horizon_year",
    "baseline_area_ha",
    "baseline_carbon_density",
    "ndvi",
]

SLR_CODE = {"low": 0, "medium": 1, "high": 2}


# ---------------------------------------------------------------------------
# Fase 1 — Comprensión del negocio
# ---------------------------------------------------------------------------


def business_understanding() -> dict[str, Any]:
    """Objetivos, hipótesis y criterios de éxito del proyecto."""
    return {
        "objetivo_negocio": (
            "Cuantificar y proyectar la retención de carbono azul del manglar del "
            "SNLMT bajo escenarios de restauración hidrológica y aumento del nivel "
            "del mar, para apoyar decisiones de conservación y financiamiento de "
            "carbono."
        ),
        "objetivo_analitico": (
            "Modelar la variación porcentual del carbono retenido a 2050 en función "
            "de covariables hidrológicas y de cobertura, con capacidad predictiva "
            "verificable fuera de muestra."
        ),
        "hipotesis": (
            f"La restauración hidrológica puede incrementar la retención de carbono "
            f"en al menos +{HYPOTHESIS_THRESHOLD:.0f} % a 2050 respecto de la línea base."
        ),
        "criterios_exito": [
            "R² fuera de muestra >= 0.85 en la variación porcentual.",
            "MAE <= 3 puntos porcentuales en la variación.",
            "Diferencia significativa (p < 0.05) entre el mejor modelo y el modelo lineal base.",
            "Coeficiente de determinación estable entre folds (desviación <= 0.05).",
        ],
        "entregables": [
            "Panel interactivo (Streamlit) con EDA, modelado y explicabilidad.",
            "Reportes exportables (PDF/Excel) por cada fase.",
            "Selección del mejor modelo con justificación estadística.",
        ],
    }


# ---------------------------------------------------------------------------
# Fase 2 — Comprensión de los datos (EDA)
# ---------------------------------------------------------------------------


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Construye la matriz de features y el vector objetivo."""
    data = df.copy()
    data["sea_level_rise_code"] = data["sea_level_rise"].map(SLR_CODE).astype(float)
    X = data[FEATURES].astype(float)
    y = data[TARGET].astype(float)
    return X, y


def eda_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Estadística descriptiva por variable numérica."""
    num = df.select_dtypes(include=[np.number])
    out = pd.DataFrame(
        {
            "n": num.count(),
            "media": num.mean(),
            "mediana": num.median(),
            "desv_std": num.std(),
            "min": num.min(),
            "p25": num.quantile(0.25),
            "p75": num.quantile(0.75),
            "max": num.max(),
            "asimetria": num.skew(),
            "nulos": num.isna().sum(),
        }
    )
    return out.round(4)


def eda_quality(df: pd.DataFrame) -> pd.DataFrame:
    """Diagnóstico de calidad: nulos, duplicados y cardinalidad."""
    rows = []
    for col in df.columns:
        rows.append(
            {
                "variable": col,
                "tipo": str(df[col].dtype),
                "nulos": int(df[col].isna().sum()),
                "pct_nulos": round(100 * df[col].isna().mean(), 2),
                "unicos": int(df[col].nunique()),
            }
        )
    return pd.DataFrame(rows)


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Matriz de correlación de Pearson sobre variables numéricas."""
    data = df.copy()
    data["sea_level_rise_code"] = data["sea_level_rise"].map(SLR_CODE).astype(float)
    num = data.select_dtypes(include=[np.number])
    return num.corr(numeric_only=True).round(3)


# ---------------------------------------------------------------------------
# Fase 3-4 — Preparación y modelado
# ---------------------------------------------------------------------------


@dataclass
class ModelResult:
    """Resultado de un modelo evaluado."""

    name: str
    pipeline: Pipeline
    metrics: dict[str, float]
    cv_scores: np.ndarray
    y_pred_test: np.ndarray
    y_test: np.ndarray
    feature_importance: dict[str, float] = field(default_factory=dict)


def _model_zoo() -> dict[str, Pipeline]:
    """Catálogo de modelos: línea base, regularizado y ensambles de árboles."""
    return {
        "Regresión lineal (base)": Pipeline(
            [("scaler", StandardScaler()), ("model", LinearRegression())]
        ),
        "Ridge (regularizado)": Pipeline(
            [("scaler", StandardScaler()), ("model", Ridge(alpha=1.0, random_state=RANDOM_STATE))]
        ),
        "Random Forest": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=200,
                        max_depth=None,
                        random_state=RANDOM_STATE,
                        n_jobs=2,
                    ),
                ),
            ]
        ),
        "Extra Trees": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "model",
                    ExtraTreesRegressor(
                        n_estimators=200,
                        max_depth=None,
                        random_state=RANDOM_STATE,
                        n_jobs=2,
                    ),
                ),
            ]
        ),
        "Gradient Boosting": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "model",
                    GradientBoostingRegressor(
                        n_estimators=200, random_state=RANDOM_STATE
                    ),
                ),
            ]
        ),
    }


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Métricas de regresión con manejo de casos degenerados."""
    if len(y_true) < 2 or np.allclose(y_true, y_true[0]):
        r2 = 0.0
    else:
        r2 = float(r2_score(y_true, y_pred))
    return {
        "r2": r2,
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
    }


def train_and_evaluate(
    df: pd.DataFrame,
    test_size: float = 0.2,
    cv_folds: int = 5,
    seed: int = RANDOM_STATE,
) -> dict[str, ModelResult]:
    """Fase 4 + 5: entrena cada modelo, valida cruzado y evalúa en test."""
    X, y = prepare_features(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, shuffle=True
    )

    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=seed)
    results: dict[str, ModelResult] = {}

    for name, pipe in _model_zoo().items():
        scores = cross_val_score(
            pipe, X_train, y_train, cv=cv, scoring="r2", n_jobs=1
        )
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        metrics = _metrics(y_test.to_numpy(), y_pred)

        fi: dict[str, float] = {}
        model = pipe.named_steps["model"]
        if hasattr(model, "feature_importances_"):
            fi = {
                feat: float(v)
                for feat, v in zip(FEATURES, model.feature_importances_)
            }

        results[name] = ModelResult(
            name=name,
            pipeline=pipe,
            metrics=metrics,
            cv_scores=np.asarray(scores, dtype=float),
            y_pred_test=np.asarray(y_pred, dtype=float),
            y_test=y_test.to_numpy(),
            feature_importance=fi,
        )
    return results


def model_comparison_table(results: dict[str, ModelResult]) -> pd.DataFrame:
    """Tabla comparativa con métricas de test y de validación cruzada."""
    rows = []
    for name, r in results.items():
        rows.append(
            {
                "modelo": name,
                "r2_test": round(r.metrics["r2"], 4),
                "mae_test": round(r.metrics["mae"], 3),
                "rmse_test": round(r.metrics["rmse"], 3),
                "cv_r2_media": round(float(np.mean(r.cv_scores)), 4),
                "cv_r2_desv": round(float(np.std(r.cv_scores)), 4),
            }
        )
    return pd.DataFrame(rows).sort_values("cv_r2_media", ascending=False).reset_index(drop=True)


def select_best_model(results: dict[str, ModelResult]) -> tuple[str, ModelResult]:
    """Selección por R² medio en validación cruzada (más robusto que test)."""
    best = max(results.items(), key=lambda kv: float(np.mean(kv[1].cv_scores)))
    return best


# ---------------------------------------------------------------------------
# Fase 5 — Pruebas estadísticas
# ---------------------------------------------------------------------------


def paired_ttest(results: dict[str, ModelResult], model_a: str, model_b: str) -> dict[str, Any]:
    """t de Student pareada sobre los folds de validación cruzada."""
    a = np.asarray(results[model_a].cv_scores, dtype=float)
    b = np.asarray(results[model_b].cv_scores, dtype=float)
    if np.allclose(a, b):
        return {"t": 0.0, "p": 1.0, "nota": "scores idénticos"}
    t_stat, p_val = stats.ttest_rel(a, b)
    return {
        "t": float(t_stat),
        "p": float(p_val),
        "media_a": float(a.mean()),
        "media_b": float(b.mean()),
        "diferencia": float(a.mean() - b.mean()),
    }


def wilcoxon_test(results: dict[str, ModelResult], model_a: str, model_b: str) -> dict[str, Any]:
    """Wilcoxon signed-rank: alternativa no paramétrica a la t pareada."""
    a = np.asarray(results[model_a].cv_scores, dtype=float)
    b = np.asarray(results[model_b].cv_scores, dtype=float)
    if np.allclose(a, b):
        return {"stat": 0.0, "p": 1.0, "nota": "scores idénticos"}
    try:
        stat, p_val = stats.wilcoxon(a, b)
        return {"stat": float(stat), "p": float(p_val)}
    except ValueError as exc:  # muestras demasiado pequeñas o todas nulas
        return {"stat": float("nan"), "p": float("nan"), "nota": str(exc)}


def bootstrap_ci(
    y_true: np.ndarray, y_pred: np.ndarray, n_boot: int = 500, seed: int = RANDOM_STATE
) -> dict[str, float]:
    """Intervalo de confianza del 95 % para el MAE por remuestreo bootstrap."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    stats_boot = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        stats_boot.append(mean_absolute_error(y_true[idx], y_pred[idx]))
    if not stats_boot:
        return {"mae_media": float("nan"), "ic95_lo": float("nan"), "ic95_hi": float("nan")}
    arr = np.asarray(stats_boot)
    return {
        "mae_media": float(arr.mean()),
        "ic95_lo": float(np.percentile(arr, 2.5)),
        "ic95_hi": float(np.percentile(arr, 97.5)),
        "n_boot": int(len(arr)),
    }


def residual_normality(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Shapiro-Wilk sobre los residuales (normalidad de errores)."""
    resid = np.asarray(y_true) - np.asarray(y_pred)
    if len(resid) < 3:
        return {"stat": float("nan"), "p": float("nan")}
    sample = resid if len(resid) <= 5000 else np.random.default_rng(0).choice(resid, 5000, replace=False)
    stat, p_val = stats.shapiro(sample)
    return {"stat": float(stat), "p": float(p_val)}


def statistical_report(results: dict[str, ModelResult]) -> pd.DataFrame:
    """Tabla de pruebas estadísticas del mejor modelo frente a los demás."""
    best_name, _ = select_best_model(results)
    rows = []
    for name in results:
        if name == best_name:
            continue
        tt = paired_ttest(results, best_name, name)
        wl = wilcoxon_test(results, best_name, name)
        rows.append(
            {
                "comparacion": f"{best_name} vs {name}",
                "t_pareada": round(tt["t"], 4),
                "p_t": round(tt["p"], 4),
                "wilcoxon_stat": round(wl["stat"], 4) if wl["stat"] == wl["stat"] else None,
                "p_wilcoxon": round(wl["p"], 4) if wl["p"] == wl["p"] else None,
                "significativo_0.05": bool(tt["p"] < 0.05),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Explicabilidad
# ---------------------------------------------------------------------------


def permutation_importance_table(
    result: ModelResult, df: pd.DataFrame, n_repeats: int = 10, seed: int = RANDOM_STATE
) -> pd.DataFrame:
    """Importancia por permutación (modelo-agnóstica) sobre el conjunto de test."""
    from sklearn.inspection import permutation_importance

    X, y = prepare_features(df)
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed, shuffle=True
    )
    r = permutation_importance(
        result.pipeline,
        X_test,
        y_test,
        n_repeats=n_repeats,
        random_state=seed,
        scoring="r2",
        n_jobs=1,
    )
    return (
        pd.DataFrame(
            {
                "variable": FEATURES,
                "importancia_media": r.importances_mean,
                "desv_std": r.importances_std,
            }
        )
        .sort_values("importancia_media", ascending=False)
        .reset_index(drop=True)
        .round(5)
    )


def hypothesis_evidence(df: pd.DataFrame) -> pd.DataFrame:
    """Evidencia sobre la hipótesis del +25 % por escenario de restauración."""
    data = df.copy()
    data["tramo_restauracion"] = pd.cut(
        data["restoration_level"],
        bins=[-0.01, 25, 50, 75, 100.01],
        labels=["0-25 %", "25-50 %", "50-75 %", "75-100 %"],
    )
    out = (
        data.groupby("tramo_restauracion", observed=True)
        .agg(
            n=("horizon_variation_pct", "size"),
            variacion_media=("horizon_variation_pct", "mean"),
            variacion_mediana=("horizon_variation_pct", "median"),
            pct_cumple_hipotesis=("meets_hypothesis", lambda s: 100 * s.mean()),
        )
        .round(3)
        .reset_index()
    )
    return out


# ---------------------------------------------------------------------------
# Figuras (bytes PNG, listas para pantalla y para reporte)
# ---------------------------------------------------------------------------


def _fig_to_png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def fig_distributions(df: pd.DataFrame) -> bytes:
    """Histogramas de las variables principales."""
    cols = ["restoration_level", TARGET, "baseline_carbon_density", "ndvi"]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, col in zip(axes.ravel(), cols):
        sns.histplot(df[col], kde=True, ax=ax, color="#2a6f97")
        ax.set_title(f"Distribución — {col}", fontsize=10)
        ax.set_xlabel("")
    fig.suptitle("Distribución de variables principales (SNLMT, Tumbes)", fontsize=12)
    fig.tight_layout()
    return _fig_to_png(fig)


def fig_correlation(df: pd.DataFrame) -> bytes:
    """Mapa de calor de correlaciones."""
    cm = correlation_matrix(df)
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(cm, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax, cbar_kws={"shrink": 0.8})
    ax.set_title("Correlación de Pearson entre variables", fontsize=12)
    fig.tight_layout()
    return _fig_to_png(fig)


def fig_model_comparison(comparison: pd.DataFrame) -> bytes:
    """Barras comparativas de R² de test y CV por modelo."""
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(comparison))
    w = 0.38
    ax.bar(x - w / 2, comparison["r2_test"], w, label="R² test", color="#2a6f97")
    ax.bar(x + w / 2, comparison["cv_r2_media"], w, label="R² CV (media)", color="#e07a5f")
    ax.set_xticks(x)
    ax.set_xticklabels(comparison["modelo"], rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("R²")
    ax.set_title("Comparación de modelos", fontsize=12)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return _fig_to_png(fig)


def fig_predicted_vs_actual(result: ModelResult) -> bytes:
    """Dispersión de valores predichos frente a observados."""
    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.scatter(result.y_test, result.y_pred_test, alpha=0.35, s=14, color="#2a6f97")
    lims = [
        min(result.y_test.min(), result.y_pred_test.min()),
        max(result.y_test.max(), result.y_pred_test.max()),
    ]
    ax.plot(lims, lims, "--", color="#e07a5f", lw=1.5, label="Identidad")
    ax.set_xlabel("Variación observada (%)")
    ax.set_ylabel("Variación predicha (%)")
    ax.set_title(f"Predicho vs observado — {result.name}", fontsize=11)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return _fig_to_png(fig)


def fig_residuals(result: ModelResult) -> bytes:
    """Residuales frente a valores predichos."""
    resid = result.y_test - result.y_pred_test
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(result.y_pred_test, resid, alpha=0.35, s=14, color="#3d5a80")
    ax.axhline(0, ls="--", color="#e07a5f", lw=1.5)
    ax.set_xlabel("Variación predicha (%)")
    ax.set_ylabel("Residual (%)")
    ax.set_title(f"Residuales — {result.name}", fontsize=11)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return _fig_to_png(fig)


def fig_feature_importance(fi: pd.DataFrame) -> bytes:
    """Importancia por permutación."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(
        fi["variable"][::-1],
        fi["importancia_media"][::-1],
        xerr=fi["desv_std"][::-1],
        color="#2a6f97",
    )
    ax.set_xlabel("Importancia por permutación (caída de R²)")
    ax.set_title("Explicabilidad: importancia de variables", fontsize=12)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    return _fig_to_png(fig)


def fig_hypothesis(evidence: pd.DataFrame) -> bytes:
    """Evidencia de la hipótesis del +25 % por tramo de restauración."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(evidence["tramo_restauracion"].astype(str), evidence["variacion_media"], color="#2a6f97")
    ax.axhline(HYPOTHESIS_THRESHOLD, ls="--", color="#e07a5f", lw=1.5, label="Umbral +25 %")
    ax.set_xlabel("Tramo de restauración hidrológica")
    ax.set_ylabel("Variación media de carbono (%)")
    ax.set_title("Evidencia de la hipótesis por nivel de restauración", fontsize=12)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return _fig_to_png(fig)


def fig_gmw_trend(gmw: pd.DataFrame) -> bytes:
    """Serie multitemporal real de extensión de manglar (GMW v3.0)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(gmw["anio"], gmw["extension_ha"], marker="o", color="#2d6a4f", lw=2)
    ax.set_xlabel("Año")
    ax.set_ylabel("Extensión de manglar (ha)")
    ax.set_title("Extensión de manglar del SNLMT — dato real GMW v3.0", fontsize=12)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return _fig_to_png(fig)
