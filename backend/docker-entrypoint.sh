#!/usr/bin/env bash
# Entrypoint del backend: espera a PostgreSQL, siembra la BD y arranca Uvicorn con hot-reload.
set -e

# Log sin credenciales: solo host:puerto/db (se omite el userinfo de DATABASE_URL).
DB_TARGET="${DATABASE_URL#*@}"
echo "Esperando a PostgreSQL (${DB_TARGET})..."
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

echo "PostgreSQL listo."
if [ "${SEED_ON_STARTUP:-false}" = "true" ]; then
    echo "SEED_ON_STARTUP=true: sembrando base de datos (perfil demo)..."
    python -m app.seed
else
    echo "SEED_ON_STARTUP no activo: seed omitido (credenciales demo no se siembran)."
fi

echo "Arrancando Uvicorn en 0.0.0.0:8000 (hot-reload)"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
