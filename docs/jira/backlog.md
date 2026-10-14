# Backlog MAE-4 — referencia del CSV de Jira

Fuente de verdad: `README.md` y la estructura actual del repo. El CSV
(`jira-issues.csv`) es el artefacto importable; este MD es solo lectura rápida.

## Épicas y alcance

| Epic | Contiene (stories大事 con IDs de docs del README) |
|---|---|
| AUTH — Usuarios y acceso | Registro/login JWT, roles (VISITANTE/INVESTIGADOR/ADMIN), perfil editable y cambio de contraseña, rate limiting (SEC-004, RATE-001) |
| ESC — Escenarios | CRUD con nivel de restauración, SLR bajo/medio/alto, horizonte, área y densidad; visibilidad pública |
| MED — Mediciones | CRUD de muestras (cobertura, tabla de agua, carbono orgánico, biomasa); solo INVESTIGADOR/ADMIN |
| PAR — Calibración | Tabla `model_params` editable por ADMIN; motor lee exclusivamente de ahí |
| SIM — Motor de simulación | Curva saturante de restauración, pérdida por SLR, cálculo de hipótesis ≥ +25 %, selector método engine/ml/ensemble, 503 si IA desactivada |
| RT — Monitoreo en vivo y 3D | WS `/api/realtime/ws/{id}`, dashboard `/realtime`, buffer, escena R3F, mapeo variable→visual, `prefers-reduced-motion` |
| DASH — Dashboard | KPIs públicos, comparación de escenarios (Recharts), indicador de hipótesis |
| REP — Reportes | Export PDF/Word/Excel con método usado (INVESTIGADOR/ADMIN) |
| ML — Modelo de IA | Dataset sintético (ML-001), lazy training, artefacto `joblib`, métricas R²/MAE/RMSE/ROC-AUC, página `/ml` |
| SEC — Seguridad y puesta en marcha | Env obligatorios (SEC-001/SEC-006), política de contraseña, seed opt-in (DOC-001), Docker Compose one-command |

## Importar a Jira (plan gratuito)

1. Jira → Proyecto creado → **Importar issues desde CSV** (Settings > System > External import, o el botón "Import issues" del backlog).
2. Subir `docs/jira/jira-issues.csv`, mapear: `Summary`→Summary, `Issue Type`, `Description`, `Parent`, `Priority`, `Story points`, `Labels`, `Epic Name`.
3. El campo `Parent` (referenciando `Issue id`) crea la jerarquía Epic→Story→Subtask en Jira Cloud moderno (team-managed y company-managed).

Nota límites free: sin tope de issues; 10 usuarios y 2 GB de adjuntos. Este CSV no usa adjuntos.
