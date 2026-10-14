# Frontend — Next.js 15 (imagen de producción: build + next start).
# NEXT_PUBLIC_API_URL se resuelve en BUILD-TIME (queda dentro del bundle JS):
# hay que pasarla como build-arg, p.ej. docker build --build-arg
# NEXT_PUBLIC_API_URL=https://dominio/api . (docker-compose.yml ya lo hace).
FROM node:24.20.0-alpine

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

RUN corepack enable && corepack prepare pnpm@11.24.0 --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
RUN pnpm install --frozen-lockfile

ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY . .
RUN pnpm build

EXPOSE 3000
CMD ["./node_modules/.bin/next", "start", "-H", "0.0.0.0", "-p", "3000"]
