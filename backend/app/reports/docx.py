"""Word (.docx) report builder (python-docx)."""
from __future__ import annotations

from io import BytesIO

from docx import Document

from app.schemas.simulation import SimulationResult
from app.services.prediction import METHOD_LABELS


def build_docx_report(result: SimulationResult) -> bytes:
    doc = Document()
    doc.add_heading("MAE-4 — Reporte de Simulación", level=0)
    doc.add_paragraph(f"Escenario: {result.scenario_name}")
    doc.add_paragraph(
        f"Método de predicción: {METHOD_LABELS.get(result.method, result.method)}"
    )
    doc.add_paragraph(f"Nivel de restauración hidrológica: {result.restoration_level:.0f}%")
    doc.add_paragraph(f"Proyección de subida del nivel del mar: {result.sea_level_rise.value}")
    doc.add_paragraph(f"Año horizonte: {result.horizon_year}")
    doc.add_paragraph(f"Retención de carbono base: {result.baseline_carbon:.1f} tC")
    doc.add_paragraph(
        f"Retención proyectada a {result.horizon_year}: {result.horizon_carbon:.1f} tC "
        f"({result.horizon_variation_pct:+.1f}% vs base)"
    )
    doc.add_paragraph(
        "Hipótesis de restauración ≥ +25%: " + ("CUMPLE" if result.meets_hypothesis else "NO CUMPLE")
    )
    if result.ml_horizon_variation_pct is not None:
        doc.add_paragraph(
            f"Comparación al horizonte — motor: {result.engine_horizon_variation_pct:+.1f}% · "
            f"modelo IA: {result.ml_horizon_variation_pct:+.1f}%"
        )

    doc.add_paragraph("")
    doc.add_heading("Serie temporal (resumen cada 5 años)", level=2)
    table = doc.add_table(rows=1, cols=5)
    table.style = "Light Grid Accent 1"
    header = table.rows[0].cells
    for i, h in enumerate(["Año", "Retenido (tC)", "Área (ha)", "Cobertura", "Var %"]):
        header[i].text = h
    for p in result.series:
        if (p.year - result.series[0].year) % 5 == 0:
            cells = table.add_row().cells
            cells[0].text = str(p.year)
            cells[1].text = f"{p.retained_carbon:.1f}"
            cells[2].text = f"{p.effective_area_ha:.1f}"
            cells[3].text = f"{p.vegetation_cover:.2f}"
            cells[4].text = f"{p.variation_pct:.1f}"

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()
