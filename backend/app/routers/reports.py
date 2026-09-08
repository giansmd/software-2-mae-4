"""Report export endpoints: PDF / Word / Excel for a scenario."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.scenario import Scenario
from app.models.user import Role, User
from app.reports import build_docx_report, build_pdf_report, build_xlsx_report
from app.schemas.simulation import SimulationResult
from app.services.params import load_model_params
from app.simulations.engine import InvalidSimulationParamsError, run_simulation

router = APIRouter(prefix="/reports", tags=["reports"])

_XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _simulate(scenario_id: int, db: Session, user: User) -> SimulationResult:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(404, "Escenario no encontrado")
    if not scenario.is_public and user.role != Role.ADMIN and scenario.owner_id != user.id:
        raise HTTPException(403, "No tiene permiso para reportar este escenario")
    params = load_model_params(db)
    try:
        result = run_simulation(
            restoration_level=scenario.restoration_level,
            sea_level_rise=scenario.sea_level_rise,
            horizon_year=scenario.horizon_year,
            baseline_area_ha=scenario.baseline_area_ha,
            baseline_carbon_density=scenario.baseline_carbon_density,
            params=params,
            scenario_id=scenario.id,
            scenario_name=scenario.name,
        )
    except InvalidSimulationParamsError as exc:
        raise HTTPException(400, str(exc)) from exc
    return SimulationResult(**result)


@router.get("/{scenario_id}/pdf")
def report_pdf(
    scenario_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.INVESTIGADOR, Role.ADMIN)),
) -> Response:
    data = build_pdf_report(_simulate(scenario_id, db, user))
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="mae4_reporte_{scenario_id}.pdf"'},
    )


@router.get("/{scenario_id}/docx")
def report_docx(
    scenario_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.INVESTIGADOR, Role.ADMIN)),
) -> Response:
    data = build_docx_report(_simulate(scenario_id, db, user))
    return Response(
        content=data,
        media_type=_DOCX_TYPE,
        headers={"Content-Disposition": f'attachment; filename="mae4_reporte_{scenario_id}.docx"'},
    )


@router.get("/{scenario_id}/xlsx")
def report_xlsx(
    scenario_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.INVESTIGADOR, Role.ADMIN)),
) -> Response:
    data = build_xlsx_report(_simulate(scenario_id, db, user))
    return Response(
        content=data,
        media_type=_XLSX_TYPE,
        headers={"Content-Disposition": f'attachment; filename="mae4_reporte_{scenario_id}.xlsx"'},
    )
