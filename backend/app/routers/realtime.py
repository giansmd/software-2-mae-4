"""WebSocket endpoint for the local realtime wetland simulator."""
from __future__ import annotations

import asyncio
import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import SessionLocal
from app.models.scenario import Scenario
from app.models.user import Role, User
from app.services.params import load_model_params
from app.services.security import decode_access_token
from app.realtime.stream import DEFAULT_SPEED, MAX_SPEED, MIN_SPEED, TICKS_PER_HORIZON, build_live_state

router = APIRouter(prefix="/realtime", tags=["realtime"])


def _resolve_user(token: str | None, db) -> User | None:
    if not token:
        return None
    claims = decode_access_token(token)
    if claims is None:
        return None
    try:
        user = db.get(User, int(claims[0]))
    except (TypeError, ValueError):
        return None
    if user is None or not user.is_active:
        return None
    if claims[1] != user.token_version:  # SEC-002: token revocado tras cambiar contraseña
        return None
    return user


def _extract_token(websocket: WebSocket) -> str | None:
    """Extrae el token JWT del subprotocolo Sec-WebSocket-Protocol.

    El token viaja como subprotocolo del handshake en lugar del query string,
    evitando su exposición en logs de proxy, historial y referrers. Si el
    cliente envía varios subprotocolos, se usa el primero (orden de
    preferencia del cliente).
    """
    header = websocket.headers.get("sec-websocket-protocol")
    if not header:
        return None
    return header.split(",")[0].strip() or None


@router.websocket("/ws/{scenario_id}")
async def stream_scenario(
    websocket: WebSocket,
    scenario_id: int,
) -> None:
    db = SessionLocal()
    token = _extract_token(websocket)
    await websocket.accept(subprotocol=token)
    try:
        scenario = db.get(Scenario, scenario_id)
        user = _resolve_user(token, db)
        if scenario is None:
            await websocket.close(code=1008, reason="Escenario no encontrado")
            return
        if not scenario.is_public and (
            user is None or (user.role != Role.ADMIN and scenario.owner_id != user.id)
        ):
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
