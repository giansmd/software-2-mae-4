# Gemelo Digital de Humedales Costeros — Frontend

Prototipo de frontend (Next.js 15 + React 19 + TypeScript + Tailwind v4 + Recharts)
para el gemelo digital de humedales costeros. Se comunica con un backend FastAPI
cuya base URL se configura con `NEXT_PUBLIC_API_URL`.

## Puesta en marcha

```bash
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 24.20.0
export PATH="/opt/data/.local:$PATH"
pnpm install
pnpm dev      # http://localhost:3000
pnpm build    # build de producción
```

## Variables de entorno

Copia `.env.example` a `.env.local` y ajusta:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Estructura

- `app/page.tsx` — Dashboard público (escenarios públicos, KPIs, gráfico comparativo, indicador de hipótesis ≥+25%).
- `app/realtime/page.tsx` — Monitoreo en vivo de un escenario público mediante WebSocket.
- `app/login/page.tsx` — Login y registro.
- `app/scenarios/page.tsx` — CRUD de escenarios + exportar PDF/Word/Excel.
- `app/scenarios/[id]/page.tsx` — Simulación con ajuste de parámetros en vivo.
- `app/measurements/page.tsx` — CRUD de mediciones.
- `app/admin/page.tsx` — Gestión de usuarios y calibración de model-params (ADMIN).
- `app/profile/page.tsx` — Edición de perfil y contraseña.
- `lib/api.ts` — Cliente fetch con token Bearer.
- `lib/auth.ts` — Gestión de token/rol y hook `useAuth`.
- `lib/realtime.ts` — Hook de conexión, controles y buffer de estados en vivo.

## Notas

- El dashboard carga escenarios públicos sin token (GET /scenarios sin auth).
- Las descargas de reportes usan `fetch` con header `Authorization` y Blob.
- Todas las páginas que consumen datos son componentes cliente que fetch en `useEffect`.
