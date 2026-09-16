"""FastAPI application factory and entrypoint."""
from __future__ import annotations

import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, measurements, ml, model_params, realtime, reports, scenarios, simulation, users
from app.seed import seed_database

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.seed_on_startup:
        try:
            seed_database()
        except Exception as exc:  # noqa: BLE001
            print(f"[seed] advertencia al sembrar la base de datos: {exc}")
    if settings.ml_enabled and settings.ml_train_on_startup:
        try:
            from app.ml.registry import get_model

            get_model()
        except Exception as exc:  # noqa: BLE001
            print(f"[ml] advertencia al entrenar el modelo al arrancar: {exc}")
    yield


app = FastAPI(title=settings.project_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (auth, users, scenarios, measurements, model_params, simulation, realtime, reports, ml):
    app.include_router(module.router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.project_name}
