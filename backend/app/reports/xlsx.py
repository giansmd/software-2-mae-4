"""Excel (.xlsx) report builder (openpyxl) — full raw time series."""
from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook

from app.schemas.simulation import SimulationResult


def build_xlsx_report(result: SimulationResult) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Serie_temporal"
    ws.append(["year", "retained_carbon_tc", "effective_area_ha", "vegetation_cover", "variation_pct"])
    for p in result.series:
        ws.append([p.year, p.retained_carbon, p.effective_area_ha, p.vegetation_cover, p.variation_pct])

    summary = wb.create_sheet("Resumen")
    rows = [
        ("Campo", "Valor"),
        ("scenario", result.scenario_name),
        ("scenario_id", result.scenario_id),
        ("restoration_level_pct", result.restoration_level),
        ("sea_level_rise", result.sea_level_rise.value),
        ("horizon_year", result.horizon_year),
        ("baseline_area_ha", result.baseline_area_ha),
        ("baseline_carbon_density", result.baseline_carbon_density),
        ("baseline_carbon_tc", result.baseline_carbon),
        ("horizon_carbon_tc", result.horizon_carbon),
        ("horizon_variation_pct", result.horizon_variation_pct),
        ("meets_hypothesis", result.meets_hypothesis),
    ]
    for r in rows:
        summary.append(list(r))

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
