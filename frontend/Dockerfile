# Praxis web — production image.
# Build the static Vite bundle, then serve it with nginx (which also proxies
# /api to the API service, so the browser uses same-origin relative requests and
# there is no CORS to configure).

FROM node:20-slim AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Empty base URL => same-origin relative /api requests (proxied by nginx).
ENV VITE_API_BASE_URL=""
RUN npm run build


FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -q -O /dev/null http://localhost:80/ || exit 1
