# Backend — FastAPI (imagen de desarrollo con hot-reload)
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000
# bash explícito: funciona igual si el archivo llega sin bit de ejecución
ENTRYPOINT ["/bin/bash", "/app/docker-entrypoint.sh"]
