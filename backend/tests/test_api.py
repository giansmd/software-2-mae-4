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


def test_token_with_non_numeric_sub_returns_401(client):
    # AUTH-001: a signed token whose sub is not a numeric id must be treated as
    # invalid (401), not crash with ValueError (HTTP 500).
    from app.services.security import create_access_token

    token = create_access_token("not-a-number")
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_with_non_numeric_sub_is_anonymous(client):
    # Same malformed token should behave as anonymous on optional-auth endpoints.
    from app.services.security import create_access_token

    token = create_access_token("not-a-number")
    r = client.get("/api/scenarios", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


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


# ---------------------------------------------------------------------------
# Authorization matrix: measurements (isolation by owner / admin)
# ---------------------------------------------------------------------------

def _create_scenario(client, token, name):
    r = client.post(
        "/api/scenarios",
        json={"name": name, "restoration_level": 50, "sea_level_rise": "low", "horizon_year": 2050},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _create_measurement(client, token, scenario_id=None, **overrides):
    body = {
        "date": "2026-01-10",
        "vegetation_cover": 0.6,
        "water_table": -0.2,
        "soil_organic_carbon": 80.0,
        "biomass": 11.0,
        **overrides,
    }
    if scenario_id is not None:
        body["scenario_id"] = scenario_id
    r = client.post("/api/measurements", json=body, headers={"Authorization": f"Bearer {token}"})
    return r


def _ensure_investigator_b(client, admin_token):
    """Create (or reuse) a second INVESTIGADOR via the admin endpoint."""
    email, password = "inv2@mae4.dev", "Invest22345"
    r = client.post(
        "/api/users",
        json={
            "email": email,
            "password": password,
            "full_name": "Investigadora B",
            "institution": "Otra Universidad",
            "role": "INVESTIGADOR",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    if r.status_code == 409:  # already created earlier in this module
        return _login(client, email, password)
    assert r.status_code == 201, r.text
    return _login(client, email, password)


def test_owner_can_list_and_read_own_measurements(client):
    inv_token = _login(client, "inv@mae4.dev", "Invest12345")
    sid = _create_scenario(client, inv_token, "Mediciones del propietario")
    r = _create_measurement(client, inv_token, scenario_id=sid)
    assert r.status_code == 201, r.text
    mid = r.json()["id"]

    listed = client.get("/api/measurements", headers={"Authorization": f"Bearer {inv_token}"})
    assert listed.status_code == 200
    assert any(m["id"] == mid for m in listed.json())

    one = client.get(f"/api/measurements/{mid}", headers={"Authorization": f"Bearer {inv_token}"})
    assert one.status_code == 200
    assert one.json()["scenario_id"] == sid


def test_other_investigator_is_isolated_from_foreign_measurements(client):
    admin_token = _login(client, "admin@mae4.dev", "Admin12345")
    inv_token = _login(client, "inv@mae4.dev", "Invest12345")
    other_token = _ensure_investigator_b(client, admin_token)

    sid = _create_scenario(client, inv_token, "Privado de inv")
    r = _create_measurement(client, inv_token, scenario_id=sid)
    assert r.status_code == 201, r.text
    mid = r.json()["id"]

    # Cannot read another investigator's measurement...
    read = client.get(f"/api/measurements/{mid}", headers={"Authorization": f"Bearer {other_token}"})
    assert read.status_code == 403

    # ...and does not see it in listings.
    listed = client.get("/api/measurements", headers={"Authorization": f"Bearer {other_token}"})
    assert listed.status_code == 200
    assert listed.json() == []


def test_create_measurement_validates_scenario_access(client):
    admin_token = _login(client, "admin@mae4.dev", "Admin12345")
    inv_token = _login(client, "inv@mae4.dev", "Invest12345")
    other_token = _ensure_investigator_b(client, admin_token)

    foreign_sid = _create_scenario(client, inv_token, "Privado ajeno")
    public_sid = client.get("/api/scenarios").json()[0]["id"]

    # Nonexistent scenario -> 404
    assert _create_measurement(client, other_token, scenario_id=999_999).status_code == 404
    # Private scenario of another investigator -> 403
    assert _create_measurement(client, other_token, scenario_id=foreign_sid).status_code == 403
    # Public scenario -> allowed
    assert _create_measurement(client, other_token, scenario_id=public_sid).status_code == 201
    # No scenario linked -> allowed
    assert _create_measurement(client, other_token).status_code == 201


def test_update_measurement_revalidates_scenario(client):
    admin_token = _login(client, "admin@mae4.dev", "Admin12345")
    inv_token = _login(client, "inv@mae4.dev", "Invest12345")
    other_token = _ensure_investigator_b(client, admin_token)

    own_sid = _create_scenario(client, inv_token, "Propio para reasignar")
    foreign_sid = _create_scenario(client, inv_token, "Otro propio")
    r = _create_measurement(client, inv_token, scenario_id=own_sid)
    assert r.status_code == 201, r.text
    mid = r.json()["id"]
    headers = {"Authorization": f"Bearer {inv_token}"}

    # Reassign to a nonexistent scenario -> 404
    put = client.put(f"/api/measurements/{mid}", json={"scenario_id": 999_999}, headers=headers)
    assert put.status_code == 404
    # Reassign to a private scenario of another investigator -> 403
    foreign_priv = _create_scenario(client, other_token, "Privado de la otra")
    put = client.put(f"/api/measurements/{mid}", json={"scenario_id": foreign_priv}, headers=headers)
    assert put.status_code == 403
    # Reassign to own scenario -> allowed
    put = client.put(f"/api/measurements/{mid}", json={"scenario_id": foreign_sid}, headers=headers)
    assert put.status_code == 200
    assert put.json()["scenario_id"] == foreign_sid


def test_admin_can_read_and_list_any_measurement(client):
    admin_token = _login(client, "admin@mae4.dev", "Admin12345")
    inv_token = _login(client, "inv@mae4.dev", "Invest12345")
    sid = _create_scenario(client, inv_token, "Visible para admin")
    r = _create_measurement(client, inv_token, scenario_id=sid)
    assert r.status_code == 201, r.text
    mid = r.json()["id"]

    one = client.get(f"/api/measurements/{mid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert one.status_code == 200
    listed = client.get("/api/measurements", headers={"Authorization": f"Bearer {admin_token}"})
    assert listed.status_code == 200
    assert any(m["id"] == mid for m in listed.json())
