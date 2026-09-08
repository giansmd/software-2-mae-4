"""Pytest configuration: run the app against an isolated SQLite database."""
import os

# Hermetic test database: always force a local SQLite file, ignoring any
# DATABASE_URL present in the environment, so the suite never connects to a
# real database (schema drift, writes on external data) or fails because of
# the host's environment.
os.environ["DATABASE_URL"] = "sqlite:///./test_mae4.db"
os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("SEED_ON_STARTUP", "true")

import pytest
from fastapi.testclient import TestClient

from app.database import engine
from app.main import app

TEST_DB_PATH = "test_mae4.db"


@pytest.fixture(scope="module")
def client():
    # Hermetic test database: dispose the engine and remove the SQLite file per
    # module so repeated runs and different modules never share stale rows or
    # connections (a pooled connection to a deleted file makes SQLite readonly).
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    with TestClient(app) as c:
        yield c
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
