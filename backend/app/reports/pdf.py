"""PDF report builder (ReportLab)."""
from __future__ import annotations

from io import BytesIO

from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.simulation import SimulationResult


def build_pdf_report(result: SimulationResult) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="Reporte MAE-4")
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("MAE-4 — Reporte de Simulación de Carbono Azul", styles["Title"]))
    story.append(Paragraph(f"Escenario: {result.scenario_name}", styles["Heading2"]))
    story.append(Spacer(1, 8))

    kpi_rows = [
        ["Parámetro", "Valor"],
        ["Nivel de restauración", f"{result.restoration_level:.0f}%"],
        ["Subida del nivel del mar", result.sea_level_rise.value],
        ["Año horizonte", str(result.horizon_year)],
        ["Retención base (tC)", f"{result.baseline_carbon:.1f}"],
        [f"Retención {result.horizon_year} (tC)", f"{result.horizon_carbon:.1f}"],
        ["Variación respecto a base", f"{result.horizon_variation_pct:.1f}%"],
        ["Hipótesis ≥ +25%", "SÍ" if result.meets_hypothesis else "NO"],
    ]
    kpi = Table(kpi_rows, hAlign="LEFT")
    kpi.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(kpi)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Serie temporal (cada 5 años)", styles["Heading3"]))
    series_rows = [["Año", "Retenido (tC)", "Área (ha)", "Cobertura", "Var %"]]
    for p in result.series:
        if (p.year - result.series[0].year) % 5 == 0:
            series_rows.append(
                [p.year, f"{p.retained_carbon:.1f}", f"{p.effective_area_ha:.1f}",
                 f"{p.vegetation_cover:.2f}", f"{p.variation_pct:.1f}"]
            )
    st = Table(series_rows, hAlign="LEFT")
    st.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 8)]))
    story.append(st)
    story.append(Spacer(1, 12))

    # Line chart of retained carbon over time
    drawing = Drawing(460, 220)
    chart = LinePlot()
    chart.x, chart.y, chart.width, chart.height = 45, 35, 380, 160
    chart.data = [[(p.year, p.retained_carbon) for p in result.series]]
    chart.lines[0].strokeColor = colors.HexColor("#0ea5e9")
    chart.lines[0].strokeWidth = 2
    chart.xValueAxis.valueMin = result.series[0].year
    chart.xValueAxis.valueMax = result.series[-1].year
    chart.yValueAxis.valueMin = 0
    chart.yValueAxis.valueMax = max(p.retained_carbon for p in result.series) * 1.1
    drawing.add(chart)
    story.append(Paragraph("Retención de carbono azul (tC) por año", styles["Heading3"]))
    story.append(drawing)

    doc.build(story)
    return buf.getvalue()
