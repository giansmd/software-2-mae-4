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
| Frontend | Next.js 15.5 (App Router), React 19.2, TypeScript 5.7, Tailwind CSS 4.3.3, Recharts 3.10, Three.js 0.186 (react-three-fiber 9.7, drei 10.7) |
| Gestor de paquetes | pnpm 11 (frontend), uv/pip (backend) |
| Reportes | ReportLab 5.0 (PDF), python-docx 1.2 (Word), openpyxl 3.1 (Excel) |
| Machine Learning | scikit-learn 1.9 (Extra Trees + Random Forest, modelo *surrogate* del motor) |

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
│   │   ├── ml/                 # modelo ML: dataset sintético, train y registry
│   │   ├── realtime/              # estados sintéticos en tiempo real
│   │   ├── reports/            # pdf.py, docx.py, xlsx.py
│   │   └── seed.py             # datos de demostración + 3 usuarios
│   └── tests/                  # pytest (motor + integración)
└── frontend/
    ├── Dockerfile
    ├── app/                    # páginas (dashboard, login, scenarios, measurements, admin, profile, ml)
    ├── components/             # ui/ (button, card), Navbar
    └── lib/                    # types.ts, api.ts, auth.ts
```

## Puesta en marcha — Quickstart (un solo comando)

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
- Modelo de IA (UI): http://localhost:3000/ml

Al abrir `/ml` por primera vez el backend **entrena el modelo de IA** (unos
segundos) y lo guarda en `backend/app/ml/artifacts/`. Como se añadió
`scikit-learn`, hay que **reconstruir la imagen del backend** (`docker compose up
--build`) tras actualizar el proyecto; el primer entrenamiento es la única espera.

La base de datos se **crea** al arrancar el backend (el entrypoint espera a
Postgres vía healthcheck y luego Uvicorn). El **seed de demostración es opt-in
(DOC-001)**: solo se ejecuta cuando `SEED_ON_STARTUP=true`; el perfil demo de
`docker compose` ya lo fija así, por lo que al primer arranque del stack demo
hay un humedal, 4 escenarios públicos y mediciones cargadas. Sin esa variable,
arranca limpio sin credenciales ni datos demo.

Para detener y limpiar volúmenes: `docker compose down -v`.

Si cambias `frontend/package.json` o el lockfile, el volumen nombrado
`frontend_node_modules` (aislado del host por compatibilidad de binarios) queda
desincronizado. Reconstrúyelo con:

```bash
docker compose up -d --build frontend
# si el contenedor sigue viendo dependencias obsoletas:
docker compose rm -sf frontend
docker volume rm software-2-mae-4_frontend_node_modules
docker compose up -d frontend
```

El archivo `frontend/.npmrc` fija `confirm-modules-purge=false` para que `pnpm`
pueda regenerar `node_modules` dentro del contenedor sin abortar por falta de TTY.

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
- **Gemelo digital 3D**: capa de visualización sobre el mismo flujo simulado (ver abajo).
- **Reportes**: PDF / Word / Excel de la simulación de un escenario (INVESTIGADOR/ADMIN).
- **Modelo de IA**: emulador (*surrogate*) entrenado con escenarios sintéticos del motor;
  métricas y predicción en `/ml` (ver abajo).

## Gemelo digital 3D (capa de visualización)

El módulo **Gemelo digital 3D** añade una capa de visualización tridimensional
**encima de la lógica que ya funciona**: no modifica el motor de simulación, los
esquemas ni la API. Consume el mismo stream WebSocket de `/realtime`
(`/api/realtime/ws/{scenario_id}`) y se muestra incrustado en esa página, entre
las métricas y las gráficas Recharts.

La escena es una **recreación esquemática y procedural** del humedal (sin datos
geoespaciales ni georreferenciación). Un único escenario se anima **en vivo** al
iniciar la simulación, y cada variable del modelo se traduce a un parámetro
visual (mapeo en `frontend/components/twin/wetlandModel.ts`):

| Variable del modelo | Efecto en la escena 3D |
|---|---|
| `effective_area_ha` (vs. baseline) | Superficie emergida: al perder área sube el plano de agua y se inunda más terreno |
| `water_table` | Ajuste fino del nivel de agua (con oscilación estacional del stream) |
| `vegetation_cover` | Densidad de vegetación (instanced mesh, máx. 3000 matas) |
| `soil_organic_carbon` | Color de la vegetación (verde sano → marrón degradado) |
| `retained_carbon` / `variation_pct` | Baliza de carbono de altura y color variables |

Componentes: `components/twin/wetlandModel.ts` (mapeo puro y testeable, sin React
ni WebGL), `components/twin/WetlandScene.tsx` (escena R3F) y
`components/twin/WetlandTwinPanel.tsx` (panel con carga diferida
`next/dynamic({ ssr: false })`, leyenda y aviso de fuente simulada). Respeta
`prefers-reduced-motion` y pausa el loop de render cuando la simulación no está
en ejecución.

### Elección tecnológica: Three.js frente a Babylon.js

| Criterio | Three.js (+ react-three-fiber / drei) | Babylon.js |
|---|---|---|
| Integración React 19 / Next 15 | Nativa y declarativa (R3F 9 soporta React 19) | Imperativa, o `react-babylonjs` de terceros |
| Peso / tree-shaking | Núcleo ligero, carga diferida en cliente | Core grande; Babylon Lite es WebGPU-only |
| Enfoque | Visualización de datos 3D (terreno, agua, instancing) | Motor de juegos/XR con física y GUI |
| Ajuste al prototipo | Óptimo: mínimo peso, sobre el stack React existente | Sobredimensionado |

**Decisión: Three.js con `@react-three/fiber` + `@react-three/drei`.** Babylon.js
solo se justificaría si se requirieran física, WebXR/AR o herramientas de motor
complejas, fuera del alcance de este prototipo.

## Modelo de IA (emulador del motor)

El módulo **Modelo de IA** entrena un modelo *real* de machine learning con
`scikit-learn` que **emula** al motor determinista. No modifica la lógica
científica: la aprende y la reproduce en milisegundos. Además de la página
`/ml`, el modelo está **integrado en la predicción** de toda la app mediante un
selector de método (ver abajo).

- **Datos de entrenamiento (ML-001):** **sintéticos**, generados por el propio
  motor (`app/ml/dataset.py`) con una semilla fija; cada etiqueta es la salida
  de `calculate_state`. Se muestrean ~2 000 escenarios × 16 posiciones
  temporales (~32 000 filas). El conjunto es reproducible y no depende de datos
  externos ni de la base de datos. **No** se usan las mediciones de campo
  (siguen reservadas a calibración).
- **Modelos:** un `ExtraTreesRegressor` multi-salida sobre la **curva anual**
  (carbono retenido, superficie efectiva, cobertura vegetal y variación %) y un
  `RandomForestClassifier` (¿cumple la hipótesis ≥ +25 %?). Se separan en
  *train/test* (80/20) y se valida con CV (3 folds). Los escenarios se muestrean
  con énfasis en los extremos de restauración (0 % y 100 %) para reducir el
  sesgo de los árboles en los bordes del dominio.
- **Métricas** (expuestas en `/api/ml/metadata`): R², MAE y RMSE por variable,
  accuracy y ROC-AUC de clasificación, además de la **importancia de variables**.
  Con los parámetros por defecto el emulador supera R² ≈ 0.99.
- **Artefacto y ciclo de vida:** el modelo se entrena de forma perezosa en el
  primer uso (~30-60 s) y se guarda en `app/ml/artifacts/carbon_model_v2.joblib`
  (ignorado por git; se regenera). `ML_ENABLED` (por defecto `true`) y
  `ML_TRAIN_ON_STARTUP` (por defecto `false`) controlan el módulo.
- **API:** `GET /api/ml/metadata` y `POST /api/ml/predict` (acepta `scenario_id`
  o parámetros inline). La predicción se devuelve **junto al resultado del
  motor** para comparar el emulador con el cálculo científico.
- **Frontend:** página `/ml` con las métricas, la importancia de variables, una
  comparación ML vs motor por nivel de restauración y un formulario de
  predicción.

### Método de predicción (motor / IA / ensemble)

Los endpoints de simulación y de reportes aceptan `method`:

| `method` | Predicción |
|---|---|
| `engine` (por defecto) | Motor determinista (sin cambios respecto a versiones previas) |
| `ml` | Serie y horizonte generados por el modelo de IA |
| `ensemble` | Promedio ponderado motor + IA (`ENSEMBLE_WEIGHT`, por defecto 0.5) |

El dashboard y el detalle de escenario incorporan un **selector de método**; los
reportes PDF/Word/Excel incluyen el método usado y la comparación motor vs IA.
La respuesta `SimulationResult` siempre trae el titular del método elegido
(`horizon_variation_pct`, `meets_hypothesis`) y, en paralelo,
`engine_horizon_variation_pct` y `ml_horizon_variation_pct`. Si `method` requiere
IA y `ML_ENABLED=false`, la API responde **503**.

> Al ser un *surrogate* de datos sintéticos, la app etiqueta explícitamente su
> origen (`synthetic`) para no confundirlo con mediciones de campo.

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

Incluye tests del motor (restauración alta > baja; hipótesis ≥ +25 %; SLR reduce retención),
tests de integración contra SQLite (auth, control de roles, CRUD, simulación y exportación
de los tres formatos de reporte) y tests del modelo de IA (dataset reproducible, calidad de
la regresión/clasificación, monotonía, selector de método `engine`/`ml`/`ensemble` y endpoints
`/api/ml`). **59 tests pasan.**

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

- Sin LLM/Gemini ni APIs externas: todo el cálculo y el entrenamiento del modelo
  de IA son locales (scikit-learn). El *surrogate* se entrena en el primer uso
  (unos segundos); su artefacto no se versiona.
- El frontend consume la API vía `NEXT_PUBLIC_API_URL` (por defecto `http://localhost:8000/api`).
- Las imágenes Docker son solo para desarrollo local (hot-reload en backend y frontend).
