#!/usr/bin/env bash
# Entrypoint del backend: espera a PostgreSQL, siembra la BD y arranca Uvicorn con hot-reload.
set -e

echo "Esperando a PostgreSQL (${DATABASE_URL})..."
until python - <<'PY'
import os
import psycopg2
try:
    psycopg2.connect(os.environ["DATABASE_URL"])
except Exception:
    raise SystemExit(1)
PY
do
  sleep 1
done

echo "PostgreSQL listo. Sembrando base de datos..."
python -m app.seed

echo "Arrancando Uvicorn en 0.0.0.0:8000 (hot-reload)"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
