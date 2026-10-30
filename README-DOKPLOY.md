# Plan de trabajo — despliegue y reproducibilidad (Dokploy)

Documento de traspaso para el agente que ejecute los cambios de infraestructura del
proyecto **MAE-4**. El artículo ya cita este sistema como desplegado y reproducible; las
tareas de este plan son las que hacen verdaderas esas afirmaciones.

## Estado de partida (verificado el 2026-10-29)

| Elemento | Estado |
|---|---|
| Proyecto Dokploy | `software-2-mae-4` |
| ID del proyecto | `6hoJRXCqx-KZ_COjBKDGR` |
| Compose | `web` (`XEpPUz8DDsYiAYuaJh0d1`) |
| Tipo | `docker-compose` |
| Origen | GitHub `giansmd/software-2-mae-4`, rama `main`, ruta `./docker-compose.yml` |
| Estado | `idle` (sin contenedores levantados) |
| Dominio | `software2mae4-web-vbickj-ec658a-169-58-140-8.sslip.io` |
| Rutas | frontend (3000) en `/`; backend (8000) en `/api`; TLS con Let's Encrypt |
| Respuesta HTTP | `404` en `/`, `/api/health` y `/api/ml/metadata` |
| Último despliegue correcto | `a65d8f8` — 2026-10-20 14:28 |
| Repositorio | público, 54 confirmaciones, con `LICENSE` MIT |

El `404` es coherente con el estado `idle`: no hay ruta que Traefik pueda resolver porque
los contenedores están detenidos. Confirmar en el panel antes de tocar configuración.

## Hallazgos que deben corregirse

1. **Credenciales de demostración en producción.** `docker-compose.yml` fija
   `SEED_ON_STARTUP: "true"`, lo que siembra los usuarios `admin@mae4.dev`,
   `inv@mae4.dev` y `visit@mae4.dev` con contraseñas públicas. El `.env` local también
   tiene `SEED_ON_STARTUP=true`. Riesgo alto.
2. **CORS y proxy.** `CORS_ORIGINS` debe apuntar al dominio público y
   `RATE_LIMIT_TRUST_PROXY=true` debe estar activo, porque el backend solo es alcanzable
   a través de Traefik.
3. **URL de API cocinada en el bundle.** `NEXT_PUBLIC_API_URL` se resuelve en tiempo de
   compilación: cualquier cambio de dominio exige reconstruir la imagen del frontend.
4. **Sin respaldo documentado** del volumen `pgdata`.
5. **Sin artefacto citable**: falta `CITATION.cff`, etiqueta de versión y DOI de archivo.
6. **Sin documentación de despliegue** en el repositorio (`docs/deployment.md`).
7. **Sin integración continua**: las pruebas se ejecutan solo en local.

## Fase 1 — Endurecimiento de la configuración

- [ ] Cambiar en `docker-compose.yml` el valor fijo por `${SEED_ON_STARTUP:-false}` y
      mover el `true` únicamente a `docker-compose.override.yml` (no versionado).
- [ ] Verificar que `.env`, `docker-compose.override.yml` y `backend/app/ml/artifacts/`
      siguen ignorados por Git.
- [ ] Definir en Dokploy: `CORS_ORIGINS=https://<dominio>`,
      `RATE_LIMIT_TRUST_PROXY=true`, `NEXT_PUBLIC_API_URL=https://<dominio>/api`,
      `SEED_ON_STARTUP=false`, `ML_ENABLED=true`, `ML_TRAIN_ON_STARTUP=true`.
- [ ] Rotar `JWT_SECRET` y `POSTGRES_PASSWORD` si existiera cualquier posibilidad de que
      hayan estado en texto plano fuera del panel.
- [ ] Mantener `DATABASE_URL` apuntando al servicio `db` por la red interna; no publicar
      puertos del host (regla del proyecto).
- [ ] Añadir `healthcheck` al backend (`/health`) y usarlo como condición de arranque del
      frontend.

## Fase 2 — Despliegue y verificación

- [ ] Redesplegar el compose desde Dokploy y confirmar estado `done`.
- [ ] Verificar en este orden: `/` (200 HTML), `/api/health` (200), `/api/ml/metadata`
      (200 tras el primer entrenamiento), WebSocket `/api/realtime/ws/{id}` (101).
- [ ] Comprobar que el certificado TLS es válido y que el dominio no expone el puerto 5432.
- [ ] Probar login con un usuario creado por el administrador, **nunca** con las
      credenciales de demostración.
- [ ] Registrar en `docs/deployment.md`: fecha, commit desplegado y resultado de cada
      comprobación.

## Fase 3 — Reproducibilidad y citación

- [ ] `LICENSE` (MIT) — hecho; verificar que figura en la raíz y en el README.
- [ ] `CITATION.cff` con título, autores, ORCID, versión y repositorio.
- [ ] Etiqueta `v1.0.0` sobre el commit que produce el artículo y publicación en Zenodo
      para obtener DOI.
- [ ] Exportar el dataset híbrido a `artifacts/dataset/` en CSV, con diccionario de
      variables y las semillas 42 (modelado) y 43 (holdout).
- [ ] Añadir al README el apartado **Quickstart en Dokploy** (variables obligatorias,
      dominio, puertos internos, reconstrucción del frontend al cambiar la URL de API).
- [ ] Enlazar el DOI, la licencia y la instancia en línea en el README.

## Fase 4 — Calidad y pruebas

- [ ] Integración continua en GitHub Actions: `pytest` en `backend/` y `pnpm build` en
      `frontend/`. Sin pruebas con Docker en local (regla del proyecto).
- [ ] Cubrir con pruebas unitarias los modelos de dominio (`backend/app/models/`), según
      la regla de pruebas de modelos.
- [ ] Revisar que `backend/tests/` no dependa de red ni de la base real (ya usa SQLite).

## Criterios de aceptación

1. `docker-compose.yml` no contiene credenciales ni activa el sembrado de demostración.
2. La URL pública responde 200 en `/` y `/api/health`, con TLS válido.
3. El repositorio declara licencia, versión y DOI, y contiene instrucciones de despliegue.
4. Un tercero puede reproducir las tablas del artículo ejecutando
   `paper/regenerate_v2.py` con las semillas declaradas.
5. El artículo puede citar la instancia en línea sin que el revisor encuentre un enlace
   caído.

## Datos que debe devolver al artículo

Al terminar, comunicar: URL final, commit y etiqueta desplegados, fecha de verificación,
resultado de `/api/health`, DOI de Zenodo y cualquier cambio de dominio que obligue a
actualizar `paper/content-es/04-metodologia.md` y `referencias.json`.
