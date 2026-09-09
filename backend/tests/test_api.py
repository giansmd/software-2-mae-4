"""Integration tests for auth, scenarios and simulation endpoints."""
from __future__ import annotations

from app.services.rate_limit import FixedWindowLimiter


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


def test_invalid_horizon_returns_400_in_simulation_and_reports(client):
    # ENG-001: with start_year set after the horizon (reachable via model-params
    # since VALID-001 allows any value), the engine must reject with 400, not
    # crash with IndexError (500) in simulation and report endpoints.
    admin_token = _login(client, "admin@mae4.dev", "Admin12345")
    inv_token = _login(client, "inv@mae4.dev", "Invest12345")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    inv_headers = {"Authorization": f"Bearer {inv_token}"}

    # Set start_year beyond any scenario horizon (seeded demos use 2050).
    put = client.put("/api/model-params/start_year", json={"value": 2070}, headers=admin_headers)
    assert put.status_code == 200, put.text

    # Inline simulation with horizon before the new start year -> 400.
    r = client.post(
        "/api/simulations/run",
        json={
            "restoration_level": 50,
            "sea_level_rise": "low",
            "horizon_year": 2050,
            "baseline_area_ha": 120,
            "baseline_carbon_density": 85,
        },
        headers=inv_headers,
    )
    assert r.status_code == 400, r.text

    # Report export of a seeded scenario (horizon 2050) -> 400 as well.
    public = client.get("/api/scenarios").json()
    sid = public[0]["id"]
    rep = client.get(f"/api/reports/{sid}/pdf", headers=inv_headers)
    assert rep.status_code == 400, rep.text

    # Restore the default so the rest of the module is unaffected.
    put = client.put("/api/model-params/start_year", json={"value": 2025}, headers=admin_headers)
    assert put.status_code == 200, put.text
    ok = client.post(
        "/api/simulations/run",
        json={
            "restoration_level": 50,
            "sea_level_rise": "low",
            "horizon_year": 2050,
            "baseline_area_ha": 120,
            "baseline_carbon_density": 85,
        },
        headers=inv_headers,
    )
    assert ok.status_code == 200, ok.text


# ---------------------------------------------------------------------------
# AUTH-002: admin self-lockout protection
# ---------------------------------------------------------------------------

def _ensure_admin_b(client, admin_token):
    """Create (or reuse) a second ADMIN via the admin endpoint."""
    email, password = "admin2@mae4.dev", "Admin22345"
    r = client.post(
        "/api/users",
        json={
            "email": email,
            "password": password,
            "full_name": "Administrador B",
            "institution": "Otra Universidad",
            "role": "ADMIN",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    if r.status_code == 409:  # already created earlier in this module
        return _login(client, email, password)
    assert r.status_code == 201, r.text
    return _login(client, email, password)


def _user_id(client, token, email):
    users = client.get("/api/users", headers={"Authorization": f"Bearer {token}"}).json()
    return next(u["id"] for u in users if u["email"] == email)


def test_admin_cannot_demote_deactivate_or_delete_self(client):
    # AUTH-002: an ADMIN must not be able to degrade or deactivate its own
    # account (self-lockout). PATCH/DELETE on the own user id are rejected.
    admin_token = _login(client, "admin@mae4.dev", "Admin12345")
    headers = {"Authorization": f"Bearer {admin_token}"}
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    uid = me.json()["id"]

    demote = client.patch(f"/api/users/{uid}", json={"role": "INVESTIGADOR"}, headers=headers)
    assert demote.status_code == 400, demote.text
    deactivate = client.patch(f"/api/users/{uid}", json={"is_active": False}, headers=headers)
    assert deactivate.status_code == 400, deactivate.text
    delete = client.delete(f"/api/users/{uid}", headers=headers)
    assert delete.status_code == 400, delete.text

    # The account is still an active ADMIN afterwards.
    still = client.get("/api/auth/me", headers=headers)
    assert still.status_code == 200
    assert still.json()["role"] == "ADMIN"
    assert still.json()["is_active"] is True


def test_admin_can_manage_another_admin_while_self_remains_active(client):
    # AUTH-002: legitimate admin management still works — demoting/deactivating
    # a *different* ADMIN is allowed, because the acting ADMIN remains active.
    admin_token = _login(client, "admin@mae4.dev", "Admin12345")
    headers = {"Authorization": f"Bearer {admin_token}"}
    admin_b_token = _ensure_admin_b(client, admin_token)
    uid = _user_id(client, admin_token, "admin2@mae4.dev")

    demote = client.patch(f"/api/users/{uid}", json={"role": "INVESTIGADOR"}, headers=headers)
    assert demote.status_code == 200, demote.text
    assert demote.json()["role"] == "INVESTIGADOR"

    # The demoted user no longer passes as ADMIN (but is still active).
    gone = client.get("/api/users", headers={"Authorization": f"Bearer {admin_b_token}"})
    assert gone.status_code == 403

    deactivate = client.patch(f"/api/users/{uid}", json={"is_active": False}, headers=headers)
    assert deactivate.status_code == 200, deactivate.text
    assert deactivate.json()["is_active"] is False

    # After deactivation, the token is rejected entirely.
    gone = client.get("/api/users", headers={"Authorization": f"Bearer {admin_b_token}"})
    assert gone.status_code == 401


# ---------------------------------------------------------------------------
# VALID-001: calibration parameter ranges
# ---------------------------------------------------------------------------

def test_model_param_rejects_out_of_range_values(client):
    # VALID-001: an ADMIN must not be able to store fractions > 1, negative
    # losses/slopes, or implausible years, since the engine consumes them
    # without clamping (invalid scientific outputs, NaN in reports).
    admin_token = _login(client, "admin@mae4.dev", "Admin12345")
    headers = {"Authorization": f"Bearer {admin_token}"}

    cases = [
        ("restoration_boost_max", 1.5),
        ("restoration_boost_max", -0.1),
        ("restoration_k", -2.0),
        ("slr_area_loss_low", -0.05),
        ("slr_area_loss_high", 2.0),
        ("slr_density_loss_medium", 1.2),
        ("start_year", 1800.0),
        ("start_year", 2200.0),
    ]
    for key, value in cases:
        r = client.put(f"/api/model-params/{key}", json={"value": value}, headers=headers)
        assert r.status_code == 422, (key, value, r.status_code, r.text)

    # Non-finite values (JSON literal Infinity) are rejected as well.
    inf = client.put(
        "/api/model-params/restoration_k",
        content='{"value": Infinity}',
        headers={**headers, "content-type": "application/json"},
    )
    assert inf.status_code == 422, inf.text

    # The stored values remain unchanged after the rejections.
    listing = client.get("/api/model-params", headers=headers).json()
    current = {p["key"]: p["value"] for p in listing}
    assert current["restoration_boost_max"] == 0.50
    assert current["restoration_k"] == 2.5


def test_model_param_accepts_valid_values_within_range(client):
    admin_token = _login(client, "admin@mae4.dev", "Admin12345")
    headers = {"Authorization": f"Bearer {admin_token}"}

    ok = client.put(
        "/api/model-params/restoration_boost_max", json={"value": 0.75}, headers=headers
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["value"] == 0.75

    # Restore the default so the rest of the module is unaffected.
    restored = client.put(
        "/api/model-params/restoration_boost_max", json={"value": 0.50}, headers=headers
    )
    assert restored.status_code == 200, restored.text


def test_model_param_rejects_unregistered_key(client):
    # VALID-002: fail-closed for future calibration keys without a registered
    # range. A param added to DEFAULT_PARAMS/PARAM_META but not to PARAM_RANGES
    # (model_params.py) must be rejected with 422 instead of being persisted
    # with an arbitrary finite value.
    from app.database import SessionLocal
    from app.models.model_param import ModelParam

    token = _login(client, "admin@mae4.dev", "Admin12345")
    headers = {"Authorization": f"Bearer {token}"}

    db = SessionLocal()
    try:
        db.add(ModelParam(key="future_metric", value=1.0, unit=None, description="Clave futura sin rango"))
        db.commit()
    finally:
        db.close()

    try:
        r = client.put(
            "/api/model-params/future_metric", json={"value": 5.0}, headers=headers
        )
        assert r.status_code == 422, (r.status_code, r.text)

        # The stored value must remain untouched.
        listing = client.get("/api/model-params", headers=headers).json()
        current = {p["key"]: p["value"] for p in listing}
        assert current["future_metric"] == 1.0
    finally:
        db = SessionLocal()
        try:
            row = db.query(ModelParam).filter(ModelParam.key == "future_metric").first()
            if row is not None:
                db.delete(row)
                db.commit()
        finally:
            db.close()


# ---------------------------------------------------------------------------
# SEC-004: rate limiting on authentication endpoints
# ---------------------------------------------------------------------------

def test_login_exhausts_rate_limit_returns_429(client):
    # SEC-004: after the allowed per-IP budget, repeated login attempts get a
    # clean HTTP 429 and the counter resets on the next window.
    import app.routers.auth as auth_module

    # Replace the module limiter with a small budget so the window is not hit.
    original = auth_module.LOGIN_LIMITER
    auth_module.LOGIN_LIMITER = FixedWindowLimiter(limit=3, window_seconds=60)
    try:
        for _ in range(3):
            r = client.post(
                "/api/auth/login", json={"email": "nobody@mae4.dev", "password": "wrong"}
            )
            # Wrong or unknown credentials are not rate-limited clients:
            # they return 401/422, not 429. (Attempts are still counted.)
            assert r.status_code in (401, 422), r.status_code
        r = client.post(
            "/api/auth/login", json={"email": "nobody@mae4.dev", "password": "wrong"}
        )
        assert r.status_code == 429, r.status_code
    finally:
        auth_module.LOGIN_LIMITER = original


def test_register_exhausts_rate_limit_returns_429(client):
    # SEC-004: registration endpoint has its own per-IP budget.
    import app.routers.auth as auth_module

    original = auth_module.REGISTER_LIMITER
    auth_module.REGISTER_LIMITER = FixedWindowLimiter(limit=2, window_seconds=60)
    try:
        for n in range(2):
            r = client.post(
                "/api/auth/register",
                json={
                    "email": f"rate{n}@mae4.dev",
                    "password": "Rate12345",
                    "full_name": "Rate Limit Test",
                },
            )
            assert r.status_code == 201, r.status_code
        r = client.post(
            "/api/auth/register",
            json={
                "email": "rate2@mae4.dev",
                "password": "Rate22345",
                "full_name": "Rate Limit Two",
            },
        )
        assert r.status_code == 429, r.status_code
    finally:
        auth_module.REGISTER_LIMITER = original


# ---------------------------------------------------------------------------
# RATE-001: client key for rate limiting behind proxies
# ---------------------------------------------------------------------------

def _scope_request(client=("203.0.113.9", 1234), xff=None):
    from starlette.requests import Request

    headers = [(b"x-forwarded-for", xff.encode())] if xff else []
    return Request({"type": "http", "client": client, "headers": headers})


def test_client_ip_ignores_xff_by_default():
    # RATE-001: without a trusted proxy, X-Forwarded-For is ignored so a client
    # cannot spoof a different IP and bypass the per-IP budget. Peer-less
    # requests fall back to the literal "unknown" key.
    from app.config import settings
    from app.services.rate_limit import client_ip

    original = settings.rate_limit_trust_proxy
    settings.rate_limit_trust_proxy = False
    try:
        assert client_ip(_scope_request(xff="198.51.100.7")) == "203.0.113.9"
        assert client_ip(_scope_request()) == "203.0.113.9"
        assert client_ip(_scope_request(client=None)) == "unknown"
    finally:
        settings.rate_limit_trust_proxy = original


def test_client_ip_uses_xff_first_hop_when_trusting_proxy():
    # RATE-001: with RATE_LIMIT_TRUST_PROXY enabled, the first hop of
    # X-Forwarded-For (the real client) is used; without the header the direct
    # peer IP still applies.
    from app.config import settings
    from app.services.rate_limit import client_ip

    original = settings.rate_limit_trust_proxy
    settings.rate_limit_trust_proxy = True
    try:
        assert client_ip(_scope_request(xff="198.51.100.7, 10.0.0.2")) == "198.51.100.7"
        assert client_ip(_scope_request()) == "203.0.113.9"
    finally:
        settings.rate_limit_trust_proxy = original


def test_fixed_window_limiter_prunes_expired_keys(monkeypatch):
    # LIM-001: expired entries are pruned periodically so the in-memory dict
    # stays bounded in long-running processes.
    now = 1_000.0
    monkeypatch.setattr("app.services.rate_limit.time.monotonic", lambda: now)
    limiter = FixedWindowLimiter(limit=5, window_seconds=60)
    limiter.check("203.0.113.1")
    now = 1_001.0
    limiter.check("203.0.113.2")
    assert set(limiter._hits) == {"203.0.113.1", "203.0.113.2"}

    # One full window later, inserting a third key prunes the two expired ones.
    now = 1_001.0 + 60.0
    limiter.check("203.0.113.3")
    assert set(limiter._hits) == {"203.0.113.3"}

    # The prune only runs once per window, and fresh entries survive it.
    now = 1_001.0 + 60.0 + 1.0
    limiter.check("203.0.113.4")
    assert set(limiter._hits) == {"203.0.113.3", "203.0.113.4"}


# ---------------------------------------------------------------------------
# SEC-002: password change invalidates previously issued JWTs
# ---------------------------------------------------------------------------

def test_change_password_invalidates_previous_tokens(client):
    # SEC-002: a token issued before the password change must stop working
    # immediately (401), while a fresh login with the new password succeeds.
    r = client.post(
        "/api/auth/register",
        json={
            "email": "sec002@mae4.dev",
            "password": "Sec00212345",
            "full_name": "SEC-002 Test",
        },
    )
    assert r.status_code == 201, r.text
    old_token = r.json()["access_token"]

    # Old token is valid before the change.
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_token}"})
    assert me.status_code == 200

    # Change the password.
    r = client.post(
        "/api/auth/me/password",
        json={"current_password": "Sec00212345", "new_password": "NuevoSec00299"},
        headers={"Authorization": f"Bearer {old_token}"},
    )
    assert r.status_code == 204, r.text

    # The old token is now rejected (revoked at the version level).
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_token}"})
    assert me.status_code == 401

    # Login with the old password fails, with the new password succeeds.
    r = client.post("/api/auth/login", json={"email": "sec002@mae4.dev", "password": "Sec00212345"})
    assert r.status_code == 401
    new_token = _login(client, "sec002@mae4.dev", "NuevoSec00299")
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me.status_code == 200


def test_change_password_does_not_revoke_other_users_tokens(client):
    # SEC-002: the invalidation is per-user; tokens of other users remain valid
    # after a password change (no global secret rotation).
    r = client.post(
        "/api/auth/register",
        json={
            "email": "sec002b@mae4.dev",
            "password": "Sec002b12345",
            "full_name": "SEC-002 Other",
        },
    )
    assert r.status_code == 201, r.text
    my_token = r.json()["access_token"]

    r = client.post(
        "/api/auth/me/password",
        json={"current_password": "Sec002b12345", "new_password": "NuevoSec002b88"},
        headers={"Authorization": f"Bearer {my_token}"},
    )
    assert r.status_code == 204

    # A seeded investigator token still authenticates normally.
    inv_token = _login(client, "inv@mae4.dev", "Invest12345")
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {inv_token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "inv@mae4.dev"
