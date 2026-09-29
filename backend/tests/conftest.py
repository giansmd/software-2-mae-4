"""Pytest configuration: run the app against an isolated SQLite database."""
import os

# Hermetic test database: always force a local SQLite file, ignoring any
# DATABASE_URL present in the environment, so the suite never connects to a
# real database (schema drift, writes on external data) or fails because of
# the host's environment.
os.environ["DATABASE_URL"] = "sqlite:///./test_mae4.db"
# Hermetic test secret: strong enough to satisfy the SEC-001 config guard, so
# the suite never depends on (or is broken by) a JWT_SECRET from the host.
os.environ["JWT_SECRET"] = "test-secret-key-0123456789abcdef0123456789abcdef"
os.environ.setdefault("SEED_ON_STARTUP", "true")

import gc

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


@pytest.fixture(autouse=True)
def _release_ml_singleton():
    """Drop the cached surrogate between tests to bound suite memory.

    ``app.ml.registry`` memoises the trained model in a module-level singleton.
    Each module that trains a fresh surrogate (``train_model``) plus the cached
    one keeps an ``ExtraTreesRegressor`` with 250 unbounded-depth trees alive.
    Across the suite that growth is monotonic and the process is OOM-killed
    under a 4 GB cgroup before the run completes. Releasing the cache and
    forcing a collection at each teardown keeps peak RSS bounded without
    changing the model configuration (accuracy thresholds still apply).
    """
    yield
    from app.ml import registry

    registry._model = None
    gc.collect()
