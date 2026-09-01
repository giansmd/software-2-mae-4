"""WebSocket endpoint for the local realtime wetland simulator."""
from __future__ import annotations

import asyncio
import datetime

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.database import SessionLocal
from app.models.scenario import Scenario
from app.models.user import User
from app.services.params import load_model_params
from app.services.security import decode_access_token
from app.realtime.stream import DEFAULT_SPEED, MAX_SPEED, MIN_SPEED, TICKS_PER_HORIZON, build_live_state

router = APIRouter(prefix="/realtime", tags=["realtime"])


def _resolve_user(token: str | None, db) -> User | None:
    if not token:
        return None
    subject = decode_access_token(token)
    if subject is None:
        return None
    try:
        user = db.get(User, int(subject))
    except (TypeError, ValueError):
        return None
    return user if user and user.is_active else None


@router.websocket("/ws/{scenario_id}")
async def stream_scenario(
    websocket: WebSocket,
    scenario_id: int,
    token: str | None = Query(default=None),
) -> None:
    db = SessionLocal()
    await websocket.accept()
    try:
        scenario = db.get(Scenario, scenario_id)
        user = _resolve_user(token, db)
        if scenario is None:
            await websocket.close(code=1008, reason="Escenario no encontrado")
            return
        if not scenario.is_public and (user is None or scenario.owner_id != user.id):
            await websocket.close(code=1008, reason="No tiene permiso para este escenario")
            return
        params = load_model_params(db)
    finally:
        db.close()

    tick = 0
    speed = DEFAULT_SPEED
    running = True
    virtual_start = datetime.datetime(
        int(params.get("start_year", 2025)), 1, 1, tzinfo=datetime.timezone.utc
    )

    try:
        while True:
            if running:
                await websocket.send_json(
                    build_live_state(
                        restoration_level=scenario.restoration_level,
                        sea_level_rise=scenario.sea_level_rise,
                        horizon_year=scenario.horizon_year,
                        baseline_area_ha=scenario.baseline_area_ha,
                        baseline_carbon_density=scenario.baseline_carbon_density,
                        params=params,
                        tick=tick,
                        virtual_start=virtual_start,
                    )
                )
                if tick >= TICKS_PER_HORIZON:
                    running = False
                    await websocket.send_json({"type": "status", "status": "horizon_reached"})

            try:
                command = await asyncio.wait_for(
                    websocket.receive_json(), timeout=1.0 / speed if running else None
                )
            except asyncio.TimeoutError:
                tick += 1
                continue

            action = command.get("type") if isinstance(command, dict) else None
            if action == "start":
                running = True
                await websocket.send_json({"type": "status", "status": "running"})
            elif action == "pause":
                running = False
                await websocket.send_json({"type": "status", "status": "paused"})
            elif action == "reset":
                tick = 0
                running = True
                await websocket.send_json({"type": "status", "status": "reset"})
            elif action == "set_speed":
                try:
                    speed = max(MIN_SPEED, min(MAX_SPEED, float(command.get("value", speed))))
                    await websocket.send_json({"type": "status", "status": "speed", "value": speed})
                except (TypeError, ValueError):
                    await websocket.send_json({"type": "error", "message": "Velocidad inválida"})
            else:
                await websocket.send_json({"type": "error", "message": "Comando no reconocido"})
    except WebSocketDisconnect:
        return
