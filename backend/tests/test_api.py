"""Integration tests for auth, scenarios and simulation endpoints."""
from __future__ import annotations


def _login(client, email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_public_scenarios_visible_without_login(client):
    r = client.get("/api/scenarios")
    assert r.status_code == 200
    assert len(r.json()) >= 4  # seeded demo scenarios


def test_visitor_cannot_create_scenario(client):
    token = _login(client, "visit@mae4.dev", "Visit12345")
    r = client.post(
        "/api/scenarios",
        json={"name": "x", "restoration_level": 10, "sea_level_rise": "low"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


def test_investigator_can_create_and_simulate(client):
    token = _login(client, "inv@mae4.dev", "Invest12345")
    r = client.post(
        "/api/scenarios",
        json={"name": "Prueba", "restoration_level": 80, "sea_level_rise": "low", "horizon_year": 2050},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.text
    sid = r.json()["id"]

    sim = client.post(
        "/api/simulations/run",
        json={"scenario_id": sid},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sim.status_code == 200, sim.text
    body = sim.json()
    assert body["horizon_year"] == 2050
    assert len(body["series"]) > 0


def test_reports_export(client):
    token = _login(client, "inv@mae4.dev", "Invest12345")
    # use a seeded public scenario id (first listed)
    public = client.get("/api/scenarios").json()
    sid = public[0]["id"]
    for ext in ("pdf", "docx", "xlsx"):
        r = client.get(f"/api/reports/{sid}/{ext}", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        assert len(r.content) > 100
