"""Panel CRISP-DM — gemelo digital de carbono azul del manglar de Tumbes.

Ejecutar:
    streamlit run streamlit_app.py

Cubre las seis fases de CRISP-DM con interpretabilidad y explicabilidad,
tanto en pantalla como en reportes exportables.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

# El motor vive en el paquete `app` del backend.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ml import crispdm as C  # noqa: E402
from app.ml.hybrid_dataset import (  # noqa: E402
    build_hybrid_dataset,
    dataset_card,
    load_gmw_series,
    load_reference_data,
    load_species_table,
)

st.set_page_config(
    page_title="MAE-4 · CRISP-DM · Manglar de Tumbes",
    page_icon="🌱",
    layout="wide",
)

CACHE_TTL = 3600


@st.cache_data(ttl=CACHE_TTL, show_spinner="Generando dataset híbrido…")
def get_dataset(n_samples: int, seed: int) -> pd.DataFrame:
    return build_hybrid_dataset(n_samples=n_samples, seed=seed)


@st.cache_resource(show_spinner="Entrenando y validando modelos…")
def get_results(n_samples: int, seed: int, cv_folds: int):
    df = build_hybrid_dataset(n_samples=n_samples, seed=seed)
    results = C.train_and_evaluate(df, cv_folds=cv_folds, seed=seed)
    return results


def png_download(container, data: bytes, filename: str, label: str = "Descargar figura"):
    container.download_button(label, data, file_name=filename, mime="image/png", key=filename)


def show_table(
    frame: pd.DataFrame,
    *,
    filename: str,
    interpretation: str,
    source: str = "Dataset híbrido SNLMT y motor determinista MAE-4",
    include_index: bool = False,
) -> None:
    st.caption(
        f"**Interpretación:** {interpretation} · **Fuente:** {source} · "
        f"**Método:** CRISP-DM · **Semilla:** {seed}"
    )
    st.dataframe(frame, width="stretch")
    st.download_button(
        "Descargar tabla (CSV)",
        table_csv(frame, interpretation, source, include_index),
        file_name=filename,
        mime="text/csv",
        key=f"table-{filename}",
    )


def table_csv(
    frame: pd.DataFrame,
    interpretation: str,
    source: str,
    include_index: bool = False,
) -> bytes:
    note = (
        f"# Interpretación: {interpretation}\n"
        f"# Fuente: {source}\n"
        f"# Método: CRISP-DM · Semilla {seed}\n"
        f"# Fecha de generación: {date.today().isoformat()}\n"
    )
    return (note + frame.to_csv(index=include_index)).encode("utf-8-sig")


# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------

st.sidebar.title("Configuración")
n_samples = st.sidebar.select_slider(
    "Registros del dataset híbrido",
    options=[400, 800, 1200, 2000, 3000],
    value=1200,
)
seed = st.sidebar.number_input("Semilla aleatoria", min_value=1, max_value=9999, value=42)
cv_folds = st.sidebar.slider("Folds de validación cruzada", 3, 10, 5)

st.sidebar.divider()
st.sidebar.caption(
    "Datos reales: SNLMT (Dioses-Puelles et al., 2023; Consorcio Manglares, 2023; "
    "Global Mangrove Watch v3.0, CC BY 4.0). Proyección: motor determinista MAE-4."
)

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------

st.title("🌱 Gemelo digital de carbono azul — Manglar de Tumbes")
st.caption(
    "Metodología CRISP-DM · Santuario Nacional Los Manglares de Tumbes (SNLMT), Perú · "
    "Dataset híbrido (datos reales + proyección calibrable)"
)

card = dataset_card()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Extensión SNLMT", f"{card['extension_total_ha']:,.0f} ha")
c2.metric("Cobertura de manglar", f"{card['manglar_ha']:,.1f} ha")
c3.metric("Carbono azul", f"{card['carbono_azul_MgC_ha']:.0f} MgC/ha")
c4.metric("Clases de cobertura", card["n_clases_cobertura"])

df = get_dataset(int(n_samples), int(seed))

tabs = st.tabs(
    [
        "1 · Comprensión del negocio",
        "2 · Comprensión de datos (EDA)",
        "3 · Preparación",
        "4 · Modelado",
        "5 · Evaluación",
        "6 · Reportes",
    ]
)

# ---------------------------------------------------------------------------
# Fase 1
# ---------------------------------------------------------------------------
with tabs[0]:
    st.header("Fase 1 — Comprensión del negocio")
    bu = C.business_understanding()
    st.markdown(f"**Objetivo de negocio.** {bu['objetivo_negocio']}")
    st.markdown(f"**Objetivo analítico.** {bu['objetivo_analitico']}")
    st.info(f"**Hipótesis.** {bu['hipotesis']}")

    left, right = st.columns(2)
    with left:
        st.subheader("Criterios de éxito")
        for c in bu["criterios_exito"]:
            st.markdown(f"- {c}")
    with right:
        st.subheader("Entregables")
        for d in bu["entregables"]:
            st.markdown(f"- {d}")

    st.subheader("Contexto del sitio de estudio")
    show_table(
        load_reference_data(),
        filename="contexto_sitio_estudio.csv",
        interpretation="Valores de referencia que describen la extensión, cobertura y contexto del sitio.",
        source="Referencias del Santuario Nacional Los Manglares de Tumbes",
    )

# ---------------------------------------------------------------------------
# Fase 2
# ---------------------------------------------------------------------------
with tabs[1]:
    st.header("Fase 2 — Comprensión de los datos (EDA)")

    st.subheader("Calidad del dataset")
    show_table(
        C.eda_quality(df),
        filename="calidad_dataset.csv",
        interpretation="Tipos, valores faltantes y valores únicos permiten detectar problemas de calidad.",
    )

    st.subheader("Estadística descriptiva")
    show_table(
        C.eda_summary(df),
        filename="estadistica_descriptiva.csv",
        interpretation="Media, dispersión y cuantiles resumen la distribución de cada variable.",
        include_index=True,
    )

    st.subheader("Datos reales del SNLMT")
    st.markdown("**Serie multitemporal de extensión de manglar (Global Mangrove Watch v3.0)**")
    show_table(
        load_gmw_series(),
        filename="serie_gmw.csv",
        interpretation="La serie permite comparar cambios observados en extensión de manglar entre años.",
        source="Global Mangrove Watch v3.0",
    )

    st.markdown("**Especies de mangle e índice de valor de importancia (IVI)**")
    show_table(
        load_species_table(),
        filename="especies_ivi.csv",
        interpretation="El IVI permite comparar la importancia ecológica relativa de las especies registradas.",
        source="Estudios de especies del SNLMT",
    )

    st.subheader("Figuras de EDA")
    col1, col2 = st.columns(2)
    fig_dist = C.fig_distributions(df)
    col1.image(fig_dist, caption="Distribución de variables principales")
    png_download(col1, fig_dist, "eda_distribuciones.png")

    fig_corr = C.fig_correlation(df)
    col2.image(fig_corr, caption="Correlación de Pearson")
    png_download(col2, fig_corr, "eda_correlacion.png")

    fig_gmw = C.fig_gmw_trend(load_gmw_series())
    st.image(fig_gmw, caption="Extensión de manglar del SNLMT — dato real GMW v3.0")
    png_download(st, fig_gmw, "eda_gmw_tendencia.png")

    st.caption(
        "**Interpretación.** La extensión de manglar muestra una tendencia positiva "
        "sostenida entre 1996 y 2020, consistente con el SNLMT como área protegida. "
        "La variación de carbono se correlaciona principalmente con el nivel de "
        "restauración y el escenario de nivel del mar."
    )

# ---------------------------------------------------------------------------
# Fase 3
# ---------------------------------------------------------------------------
with tabs[2]:
    st.header("Fase 3 — Preparación de los datos")
    X, y = C.prepare_features(df)

    st.markdown(
        "Se construye la matriz de atributos con codificación ordinal del escenario "
        "de nivel del mar, y se separa el objetivo. El escalado se aplica **dentro** "
        "de cada pipeline para evitar fuga de información entre ajuste y evaluación."
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Registros", f"{len(X):,}")
    c2.metric("Atributos", len(C.FEATURES))
    c3.metric("Objetivo", C.TARGET)

    st.subheader("Matriz de atributos (primeras filas)")
    show_table(
        X.head(10),
        filename="matriz_atributos_muestra.csv",
        interpretation="Muestra de predictores codificados que recibe el modelo; no representa el dataset completo.",
    )

    st.subheader("Variable objetivo")
    show_table(
        y.describe().round(4).rename("horizon_variation_pct").to_frame(),
        filename="resumen_variable_objetivo.csv",
        interpretation="Resumen estadístico de la variación de carbono que el modelo aprende a predecir.",
        include_index=True,
    )

    st.subheader("Trazabilidad del dataset híbrido")
    st.json(card)

# ---------------------------------------------------------------------------
# Fase 4
# ---------------------------------------------------------------------------
results = get_results(int(n_samples), int(seed), int(cv_folds))

with tabs[3]:
    st.header("Fase 4 — Modelado")
    comparison = C.model_comparison_table(results)
    show_table(
        comparison,
        filename="comparacion_modelos.csv",
        interpretation="R² y errores comparan el desempeño de modelos; valores mejores dependen de la métrica.",
    )

    best_name, best = C.select_best_model(results)
    st.success(f"**Mejor modelo seleccionado:** {best_name}")

    col1, col2 = st.columns(2)
    fig_cmp = C.fig_model_comparison(comparison)
    col1.image(fig_cmp, caption="Comparación de modelos")
    png_download(col1, fig_cmp, "modelos_comparacion.png")

    fig_pa = C.fig_predicted_vs_actual(best)
    col2.image(fig_pa, caption="Predicho vs observado (mejor modelo)")
    png_download(col2, fig_pa, "modelo_predicho_vs_observado.png")

    fig_res = C.fig_residuals(best)
    st.image(fig_res, caption="Análisis de residuales del mejor modelo")
    png_download(st, fig_res, "modelo_residuales.png")

    st.subheader("Evidencia sobre la hipótesis del +25 %")
    ev = C.hypothesis_evidence(df)
    show_table(
        ev,
        filename="evidencia_hipotesis.csv",
        interpretation="Compara variación de carbono y cumplimiento del umbral por tramo de restauración.",
    )
    fig_hyp = C.fig_hypothesis(ev)
    st.image(fig_hyp, caption="Variación media por tramo de restauración")
    png_download(st, fig_hyp, "hipotesis_evidencia.png")

# ---------------------------------------------------------------------------
# Fase 5
# ---------------------------------------------------------------------------
with tabs[4]:
    st.header("Fase 5 — Evaluación")

    st.subheader("Validación cruzada")
    st.markdown(
        f"Validación cruzada de **{cv_folds} folds** con `KFold` sobre el conjunto "
        "de entrenamiento. El R² medio entre folds es el criterio de selección, por "
        "ser más robusto que una única partición de prueba."
    )
    show_table(
        comparison,
        filename="evaluacion_modelos.csv",
        interpretation="Resume el desempeño medio en validación cruzada y en el conjunto de prueba.",
    )

    st.subheader("Pruebas estadísticas rigurosas")
    show_table(
        C.statistical_report(results),
        filename="pruebas_estadisticas.csv",
        interpretation="p < 0.05 indica evidencia estadística de diferencia entre modelos en la prueba indicada.",
        source="Puntajes por fold de validación cruzada",
    )
    st.caption(
        "t de Student pareada y Wilcoxon signed-rank sobre los puntajes por fold, "
        "comparando el mejor modelo contra los demás. Un p < 0.05 indica diferencia "
        "estadísticamente significativa."
    )

    st.subheader("Intervalo de confianza del error")
    boot = C.bootstrap_ci(best.y_test, best.y_pred_test)
    c1, c2, c3 = st.columns(3)
    c1.metric("MAE medio (bootstrap)", f"{boot['mae_media']:.3f}")
    c2.metric("IC 95 % inferior", f"{boot['ic95_lo']:.3f}")
    c3.metric("IC 95 % superior", f"{boot['ic95_hi']:.3f}")

    st.subheader("Normalidad de residuales (Shapiro-Wilk)")
    norm = C.residual_normality(best.y_test, best.y_pred_test)
    st.write(
        f"Estadístico = {norm['stat']:.4f}, p = {norm['p']:.3e}. "
        + (
            "Los residuales **no** siguen una distribución normal; conviene "
            "priorizar pruebas no paramétricas (Wilcoxon) en la comparación."
            if norm["p"] < 0.05
            else "No se rechaza la normalidad de los residuales."
        )
    )

    st.subheader("Explicabilidad — importancia por permutación")
    fi = C.permutation_importance_table(best, df)
    show_table(
        fi,
        filename="importancia_variables.csv",
        interpretation="Una caída mayor de R² al permutar una variable indica mayor dependencia predictiva del modelo.",
        source="Conjunto de prueba del dataset híbrido",
    )
    fig_fi = C.fig_feature_importance(fi)
    st.image(fig_fi, caption="Importancia de variables del mejor modelo")
    png_download(st, fig_fi, "evaluacion_importancia.png")

    st.caption(
        "**Interpretación.** La importancia por permutación mide cuánto cae el R² al "
        "desordenar cada variable: valores altos indican dependencia fuerte del modelo. "
        "Al ser model-agnóstica, permite auditar incluso ensambles opacos."
    )

# ---------------------------------------------------------------------------
# Fase 6
# ---------------------------------------------------------------------------
with tabs[5]:
    st.header("Fase 6 — Despliegue y reportes")

    st.markdown(
        "Cada fase exporta sus tablas y figuras. Los reportes consolidados se "
        "generan con `app.reports`, reutilizando el mismo contenido que se ve en "
        "pantalla."
    )

    st.subheader("Exportar tablas")
    c1, c2 = st.columns(2)
    c1.download_button(
        "Descargar comparación de modelos (CSV)",
        table_csv(
            comparison,
            "R² y errores comparan el desempeño de modelos; valores mejores dependen de la métrica.",
            "Dataset híbrido SNLMT y motor determinista MAE-4",
        ),
        file_name="modelos_comparacion.csv",
        mime="text/csv",
    )
    c2.download_button(
        "Descargar pruebas estadísticas (CSV)",
        table_csv(
            C.statistical_report(results),
            "p < 0.05 indica evidencia estadística de diferencia entre modelos en la prueba indicada.",
            "Puntajes por fold de validación cruzada",
        ),
        file_name="pruebas_estadisticas.csv",
        mime="text/csv",
    )

    c3, c4 = st.columns(2)
    c3.download_button(
        "Descargar EDA descriptivo (CSV)",
        table_csv(
            C.eda_summary(df),
            "Media, dispersión y cuantiles resumen la distribución de cada variable.",
            "Dataset híbrido SNLMT y motor determinista MAE-4",
            include_index=True,
        ),
        file_name="eda_descriptivo.csv",
        mime="text/csv",
    )
    c4.download_button(
        "Descargar evidencia de hipótesis (CSV)",
        table_csv(
            C.hypothesis_evidence(df),
            "Compara variación de carbono y cumplimiento del umbral por tramo de restauración.",
            "Dataset híbrido SNLMT y motor determinista MAE-4",
        ),
        file_name="hipotesis_evidencia.csv",
        mime="text/csv",
    )

    st.subheader("Dataset híbrido")
    st.download_button(
        "Descargar dataset completo (CSV)",
        table_csv(
            df,
            "Registros usados para reproducir el análisis; resultados dependen de semilla y configuración.",
            "Dataset híbrido SNLMT y motor determinista MAE-4",
        ),
        file_name="dataset_hibrido_snlmt.csv",
        mime="text/csv",
    )

st.divider()
st.caption(
    "MAE-4 · Ingeniería de Software II · Dataset: manglar del SNLMT (Tumbes, Perú). "
    "Datos reales de literatura abierta; proyección simulada y calibrable."
)
