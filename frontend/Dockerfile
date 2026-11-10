# syntax=docker/dockerfile:1
# Production image only. Development runs Vite with the local Node toolchain (`uv run poe fe-dev`).
FROM --platform=linux/amd64 node:26.13.0-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build


# Static files served by unprivileged nginx, which also proxies /api to the backend.
FROM --platform=linux/amd64 nginxinc/nginx-unprivileged:1.29-alpine AS final
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
