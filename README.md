# MAE-4 — Gemelo digital hidrogeomorfológico de humedales costeros y carbono azul

Prototipo funcional para Ingeniería de Software II. Representa un humedal costero y
simula cómo la **restauración hidrológica** afecta la retención de **carbono azul**
bajo escenarios de aumento del nivel del mar (IPCC) y restauración.

**Hipótesis del trabajo:** la restauración hidrológica puede aumentar la retención de
carbono **≥ +25 % a 2050**.

> Entorno 100 % local. Se orquesta con Docker Compose (db + backend + frontend).
> No hay despliegue a la nube ni CI/CD.

---

## Stack

| Capa | Tecnología (versión fijada) |
|---|---|
| Backend | Python 3.12, FastAPI 0.141, Uvicorn 0.52, SQLAlchemy 2.0, Pydantic v2, JWT (python-jose) |
| Base de datos | PostgreSQL 18.6 |
| Frontend | Next.js 15.5 (App Router), React 19.2, TypeScript 5.7, Tailwind CSS 4.3.3, Recharts 3.10 |
| Gestor de paquetes | pnpm 11 (frontend), uv/pip (backend) |
| Reportes | ReportLab 5.0 (PDF), python-docx 1.2 (Word), openpyxl 3.1 (Excel) |

## Estructura

```
software-2-mae-4/
├── docker-compose.yml          # orquesta db + backend + frontend
├── .env.example                # variables de entorno (plantilla)
├── backend/
│   ├── Dockerfile
│   ├── docker-entrypoint.sh    # espera a Postgres, siembra y arranca Uvicorn
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py             # app FastAPI + CORS + lifespan(seed)
│   │   ├── config.py           # settings (env)
│   │   ├── database.py         # engine / sesión
│   │   ├── dependencies.py     # auth + control de roles
│   │   ├── models/             # User, Scenario, Measurement, ModelParam
│   │   ├── schemas/            # Pydantic v2 (request/response)
│   │   ├── services/           # security (hash/JWT), params
│   │   ├── routers/            # auth, users, scenarios, measurements, model_params, simulation, reports
│   │   ├── simulations/engine.py  # motor de retención de carbono
│   │   ├── realtime/              # estados sintéticos en tiempo real
│   │   ├── reports/            # pdf.py, docx.py, xlsx.py
│   │   └── seed.py             # datos de demostración + 3 usuarios
│   └── tests/                  # pytest (motor + integración)
└── frontend/
    ├── Dockerfile
    ├── app/                    # páginas (dashboard, login, scenarios, measurements, admin, profile)
    ├── components/             # ui/ (button, card), Navbar
    └── lib/                    # types.ts, api.ts, auth.ts
```

## Puesta en marcha (un solo comando)

Requiere Docker + el plugin `docker compose` en una máquina Linux.

```bash
# 1) (opcional) define tus variables:
cp .env.example .env

# 2) levanta todo:
docker compose up --build
```

- Frontend:  http://localhost:3000
- Backend API (docs Swagger): http://localhost:8000/docs
- Salud:     http://localhost:8000/health

La base de datos se **crea** al arrancar el backend (el entrypoint espera a
Postgres vía healthcheck y luego Uvicorn). El **seed de demostración es opt-in
(DOC-001)**: solo se ejecuta cuando `SEED_ON_STARTUP=true`; el perfil demo de
`docker compose` ya lo fija así, por lo que al primer arranque del stack demo
hay un humedal, 4 escenarios públicos y mediciones cargadas. Sin esa variable,
arranca limpio sin credenciales ni datos demo.

Para detener y limpiar volúmenes: `docker compose down -v`.

Si ya existía un volumen creado con PostgreSQL anterior a 18, después de actualizar
la imagen hay que eliminarlo en desarrollo (`docker compose down -v`) y volver a
levantar el stack. Para conservar esos datos se requiere una migración con
`pg_upgrade`; no se debe borrar el volumen.

## Variables de entorno

Ver `.env.example`. La mayoría tiene valor por defecto en `docker-compose.yml`.
**`JWT_SECRET` y `POSTGRES_PASSWORD` son obligatorios**: `docker compose` aborta el
arranque si faltan (SEC-001 / SEC-006); el backend también rechaza `JWT_SECRET`
débil o conocido. **`DATABASE_URL` no tiene default funcional** (el de
`docker-compose.yml` es un marcador `***` que no conecta): defínela con la
contraseña real, p. ej. `postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/mae4`.
El seed de demo está desactivado por defecto (DOC-001) y solo el perfil demo de
compose lo activa explícitamente con `SEED_ON_STARTUP=true`.

## Credenciales de seed (SOLO perfil demo)

Estas credenciales **solo existen cuando el seed está activo** (`SEED_ON_STARTUP=true`,
perfil demo local de `docker compose`). Son públicas, conocidas y **nunca deben
usarse fuera de la demo local** (DOC-001): no habilites el seed en entornos
compartidos ni de producción, y si algún día se activa en otro entorno, cámbialas
o elimina el seed.

| Rol | Email | Contraseña |
|---|---|---|
| ADMIN | admin@mae4.dev | Admin12345 |
| INVESTIGADOR | inv@mae4.dev | Invest12345 |
| VISITANTE | visit@mae4.dev | Visit12345 |

El **dashboard es público** (acceso sin login) usando los escenarios marcados
`is_public`. VISITANTE solo lectura; INVESTIGADOR crea escenarios/mediciones y exporta
reportes; ADMIN gestiona usuarios y calibra el modelo.

## Módulos

- **Usuarios / roles / perfiles**: registro y login con JWT. Perfil editable
  (nombre, email, institución) y cambio de contraseña. Rutas protegidas por rol.
- **Escenarios**: CRUD de escenarios (nivel de restauración 0–100 %, SLR bajo/medio/alto,
  año horizonte, área y densidad base).
- **Mediciones**: CRUD de muestras temporales del humedal (cobertura, tabla de agua,
  carbono orgánico del suelo, biomasa).
- **Parámetros del modelo**: tabla `model_params` editable por ADMIN (calibración).
- **Motor de simulación**: ver abajo.
- **Monitoreo en vivo**: stream WebSocket de estados sintéticos del escenario
  (`/api/realtime/ws/{scenario_id}`), con controles de inicio, pausa, reinicio y velocidad.
- **Dashboard**: KPIs (retención base, proyección a horizonte, % variación, superficie
  efectiva), comparación de escenarios superpuestos (Recharts) e indicador de hipótesis.
- **Dashboard en vivo**: `/realtime`, con buffer de los últimos estados y gráficas de
  carbono, superficie, nivel freático y cobertura vegetal. La fuente se etiqueta como
  `simulated`; todavía no representa lecturas de sensores.
- **Reportes**: PDF / Word / Excel de la simulación de un escenario (INVESTIGADOR/ADMIN).

## Base científica del modelo de retención de carbono

El motor (`backend/app/simulations/engine.py`) es un modelo **explicable**, no un mock.
Parte de la métrica de carbono azul costero: humedales (marismas, manglares, turba)
secuestran y almacenan carbono en suelo y biomasa, y su productividad depende de la
hidrología (regímenes de agua y salinidad).

**Línea base** (año inicial):

```
C0 = A0 · D0
A0 = superficie efectiva del humedal (ha)
D0 = densidad de carbono suelo + biomasa (tC/ha)
```

**Restauración hidrológica** (nivel `R` en 0–1) — curva saturante:

```
factor_restauracion = Bmax · (1 − e^(−k·R))
densidad(t) = D0 · (1 + factor_restauracion)
```

La ganancia de retención es máxima a restauración total (`Bmax`, p.ej. 0.50) pero con
**rendimientos decrecientes** (ley de saturación exponencial, parámetro `k`): cada
porcentaje extra de restauración aporta menos que el anterior. Esto refleja la literatura
de blue carbon donde la recuperación de la hidrología mejora el secuestro hasta un tope.

**Subida del nivel del mar** (escenario SLR IPCC) — pérdida progresiva:

```
frac = (año − año_inicial) / (horizonte − año_inicial)
area_efectiva(t) = A0 · (1 − pérdida_area(SLR) · frac)
densidad(t)       = D0 · (1 + factor_restauracion) · (1 − pérdida_densidad(SLR) · frac)
```

La superficie se reduce por inundación/salinización y la densidad de carbono decae, con
**mayor impacto en escenarios altos** (IPCC ~ +1.0 m para 2100 frente a ~ +0.4 m bajo).
Los factores de pérdida (`slr_area_loss_*`, `slr_density_loss_*`) son parámetros
calibrubles por el ADMIN en la tabla `model_params`.

**Retenido** y variación:

```
Retenido(t) = area_efectiva(t) · densidad(t)
Variación % = (Retenido(t) − C0) / C0 · 100
Hipótesis   = Variación(horizonte) ≥ +25 %
```

Valores por defecto (realistas para humedal tipo, ~80–85 tC/ha de suelo + biomasa):
`baseline_area_ha = 120`, `baseline_carbon_density = 85`, `restoration_boost_max = 0.50`,
`restoration_k = 2.5`, pérdidas SLR bajo/medio/alto = 0.06/0.12/0.22 (área) y
0.05/0.12/0.20 (densidad). Con restauración alta (90 %) + SLR bajo el modelo alcanza
~ +37 % a 2050, validando la hipótesis; sin restauración + SLR alto cae por debajo de la
base. Se documentan como parámetros editables, no como constantes ocultas.

**Alcance de la calibración:** el motor usa exclusivamente los parámetros de la tabla
`model_params` (editables por ADMIN). Las mediciones de campo registradas en
`measurements` (cobertura, tabla de agua, carbono orgánico del suelo y biomasa) se
almacenan como datos de colección del proyecto, pero **no alimentan el motor de
simulación** en esta versión; quedan disponibles como entrada futura de calibración o
validación del modelo.

## Pruebas

```
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest
```

Incluye tests del motor (restauración alta > baja; hipótesis ≥ +25 %; SLR reduce retención)
y tests de integración contra SQLite (auth, control de roles, CRUD, simulación y exportación
de los tres formatos de reporte). **33 tests pasan.**

Los tests siempre corren contra una base SQLite local hermética (`test_mae4.db`),
ignorando cualquier `DATABASE_URL` presente en el entorno: nunca escriben sobre una
base real ni dependen de su esquema.

### Seguridad

- Autenticación con rate limiting por IP en memoria (SEC-004): login 60 intentos / 15 min
  y registro 20 / 15 min por IP. Por defecto la cuota se calcula sobre la IP directa del
  peer e **ignora `X-Forwarded-For`** (RATE-001, fail-safe ante spoofing); si el backend se
  despliega detrás de un proxy inverso de confianza, activa `RATE_LIMIT_TRUST_PROXY=true`
  para que la cuota use el primer salto de ese header. El limitador es en memoria y por
  proceso: no se comparte entre workers; al escalar, sustituir por un store compartido.

## Notas

- Sin LLM/Gemini ni APIs externas: todo el cálculo es local.
- El frontend consume la API vía `NEXT_PUBLIC_API_URL` (por defecto `http://localhost:8000/api`).
- Las imágenes Docker son solo para desarrollo local (hot-reload en backend y frontend).
