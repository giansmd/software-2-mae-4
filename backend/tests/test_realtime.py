"""Integration tests for the local realtime simulator."""
from __future__ import annotations

import pytest
from starlette.websockets import WebSocketDisconnect


def test_public_realtime_stream_can_be_controlled(client):
    public = client.get("/api/scenarios").json()
    scenario_id = public[0]["id"]

    with client.websocket_connect(f"/api/realtime/ws/{scenario_id}") as websocket:
        first = websocket.receive_json()
        assert first["type"] == "state"
        assert first["source"] == "simulated"
        assert first["sequence"] == 0
        assert "retained_carbon" in first["values"]

        websocket.send_json({"type": "pause"})
        assert websocket.receive_json() == {"type": "status", "status": "paused"}

        websocket.send_json({"type": "set_speed", "value": 10})
        speed = websocket.receive_json()
        assert speed["type"] == "status"
        assert speed["value"] == 10.0

        websocket.send_json({"type": "reset"})
        assert websocket.receive_json() == {"type": "status", "status": "reset"}
        reset_state = websocket.receive_json()
        assert reset_state["type"] == "state"
        assert reset_state["sequence"] == 0


def test_private_realtime_stream_requires_access(client):
    token_response = client.post(
        "/api/auth/login",
        json={"email": "inv@mae4.dev", "password": "Invest12345"},
    )
    token = token_response.json()["access_token"]
    scenario = client.post(
        "/api/scenarios",
        json={
            "name": "Escenario privado en vivo",
            "restoration_level": 40,
            "sea_level_rise": "medium",
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    with pytest.raises(WebSocketDisconnect) as error:
        with client.websocket_connect(f"/api/realtime/ws/{scenario['id']}") as websocket:
            websocket.receive_json()
    assert error.value.code == 1008

    with client.websocket_connect(
        f"/api/realtime/ws/{scenario['id']}?token={token}"
    ) as websocket:
        assert websocket.receive_json()["type"] == "state"


def test_admin_realtime_stream_allows_private_scenario_of_other_user(client):
    admin_token = client.post(
        "/api/auth/login",
        json={"email": "admin@mae4.dev", "password": "Admin12345"},
    ).json()["access_token"]
    inv_token = client.post(
        "/api/auth/login",
        json={"email": "inv@mae4.dev", "password": "Invest12345"},
    ).json()["access_token"]
    scenario = client.post(
        "/api/scenarios",
        json={
            "name": "Escenario privado para ADMIN",
            "restoration_level": 30,
            "sea_level_rise": "medium",
        },
        headers={"Authorization": f"Bearer {inv_token}"},
    ).json()

    with client.websocket_connect(
        f"/api/realtime/ws/{scenario['id']}?token={admin_token}"
    ) as websocket:
        first = websocket.receive_json()
        assert first["type"] == "state"
