"""Pytest configuration: run the app against an isolated SQLite database."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_mae4.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("SEED_ON_STARTUP", "true")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
