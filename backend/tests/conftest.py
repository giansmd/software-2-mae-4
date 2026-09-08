"""Pytest configuration: run the app against an isolated SQLite database."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_mae4.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("SEED_ON_STARTUP", "true")

import pytest
from fastapi.testclient import TestClient

from app.main import app

TEST_DB_PATH = "test_mae4.db"


@pytest.fixture(scope="module")
def client():
    # Hermetic test database: always start from an empty file so repeated runs
    # do not accumulate users or rows.
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    with TestClient(app) as c:
        yield c
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
