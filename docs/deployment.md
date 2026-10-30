# Despliegue

Guía operativa del prototipo MAE-4: ejecución local, despliegue en Dokploy, respaldo y
verificación. El objetivo es que un tercero pueda levantar el sistema y comprobar que
responde sin depender de esta máquina.

## Arquitectura

Tres servicios definidos en `docker-compose.yml`:

| Servicio | Imagen / build | Puerto interno | Rol |
|---|---|---|---|
| `db` | `postgres:18.6` | 5432 | Base de datos con volumen `pgdata` |
| `backend` | `backend/Dockerfile` | 8000 | API FastAPI, motor, emulador ML y WebSocket |
| `frontend` | `frontend/Dockerfile` | 3000 | Next.js 15 (App Router) |

En Dokploy, Traefik publica el frontend en `/` y el backend en `/api` sobre el mismo
dominio. Los contenedores **no publican puertos en el host**: el enrutamiento se resuelve
por la red externa `dokploy-network`.

## Variables de entorno

| Variable | Obligatoria | Valor en producción | Nota |
|---|---|---|---|
| `POSTGRES_PASSWORD` | Sí | secreto | El compose aborta si falta |
| `DATABASE_URL` | Sí | `postgresql://postgres:<clave>@db:5432/mae4` | Sin valor por defecto funcional |
| `JWT_SECRET` | Sí | secreto de 32+ caracteres | El backend rechaza valores débiles |
| `CORS_ORIGINS` | Sí | `https://<dominio>` | Debe incluir el dominio público |
| `NEXT_PUBLIC_API_URL` | Sí | `https://<dominio>/api` | Se compila en el bundle: cambiarla exige reconstruir el frontend |
| `SEED_ON_STARTUP` | No | `false` | `true` crea credenciales demo; solo en local |
| `RATE_LIMIT_TRUST_PROXY` | No | `true` | Necesario detrás de Traefik |
| `ML_ENABLED` | No | `true` | Habilita el emulador |
| `ML_TRAIN_ON_STARTUP` | No | `true` | Evita el entrenamiento perezoso en la primera visita |

## Ejecución local

```bash
cp .env.example .env      # completa POSTGRES_PASSWORD, DATABASE_URL y JWT_SECRET
docker network create dokploy-network   # requerido por la red externa
docker compose up --build
```

El archivo `docker-compose.override.yml` (no versionado) publica los puertos
`3000`, `8000` y `5433` y activa el sembrado demo. Sin ese archivo, el stack se comporta
como en producción.

- Panel: <http://localhost:3000>
- API y Swagger: <http://localhost:8000/docs>
- Salud: <http://localhost:8000/health>

## Despliegue en Dokploy

1. Crear un proyecto y un recurso **Compose** apuntando al repositorio
   `giansmd/software-2-mae-4`, rama `main`, ruta `./docker-compose.yml`.
2. Cargar las variables de la tabla anterior en el panel del recurso. No versionar
   secretos.
3. Definir dos dominios sobre el mismo host: servicio `frontend`, puerto `3000`, ruta `/`;
   servicio `backend`, puerto `8000`, ruta `/api`. Activar Let's Encrypt.
4. Desplegar y esperar el estado `done`.
5. Verificar en este orden:

```bash
curl -fsS https://<dominio>/ | head -c 200
curl -fsS https://<dominio>/api/health
curl -fsS https://<dominio>/api/ml/metadata
```

El WebSocket se comprueba desde el panel en vivo (`/realtime`): debe abrir la conexión y
recibir estados. Si el navegador muestra 404 en todo el dominio, el compose está detenido
o el dominio no apunta al servicio correcto.

## Respaldo y restauración

```bash
# Respaldo
docker compose exec -T db pg_dump -U postgres mae4 > respaldo_$(date +%F).sql

# Restauración
cat respaldo_2026-10-29.sql | docker compose exec -T db psql -U postgres mae4
```

El volumen `pgdata` conserva los datos entre despliegues. No borrarlo (`docker compose
down -v`) salvo que se quiera reiniciar la base.

## Reversión

Dokploy conserva el historial de despliegues. Para volver a una versión anterior, redeploy
del commit afectado o `git revert` del cambio y nuevo despliegue. Si el cambio tocó
`NEXT_PUBLIC_API_URL`, reconstruir el frontend: el valor queda fijado en el bundle.

## Verificación posterior al despliegue

- [ ] `/` responde 200 y muestra el panel.
- [ ] `/api/health` responde 200.
- [ ] El registro de un usuario nuevo funciona y el login devuelve token.
- [ ] El panel público no requiere credenciales.
- [ ] No existe ningún usuario `admin@mae4.dev` (sembrado desactivado).
- [ ] El certificado TLS es válido y el puerto 5432 no está expuesto.
