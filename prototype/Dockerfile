# syntax=docker/dockerfile:1.7
#
# SSR runtime for the Yomineko prototype (React Router v7, framework mode).
# Replaces the previous static-web-server image: the corpus data + the lesson
# parser live ONLY on the server, so the app MUST run as a Node SSR process.
# Keeps the original container port (80) so Coolify needs no server-side changes.

# ---- deps (full, for building) ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN --mount=type=cache,target=/root/.npm \
    npm install --no-audit --no-fund
COPY . .
RUN npm run build

# ---- production deps only ----
FROM node:22-alpine AS prod-deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN --mount=type=cache,target=/root/.npm \
    npm install --omit=dev --no-audit --no-fund

# ---- runtime ----
FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    PORT=80 \
    HOST=0.0.0.0
# production node_modules, build output, and the serve script
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=build /app/build ./build
COPY package.json ./

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:80/health >/dev/null 2>&1 || exit 1

# react-router-serve reads PORT/HOST from env
CMD ["npm", "run", "start"]
