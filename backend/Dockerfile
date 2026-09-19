# Praxis API — production image.
# Multi-stage: resolve dependencies with uv into a venv, then run as non-root.
# The core API image is lean (no GeoPandas/GDAL); the ETL extra is installed only
# when you need to load seed data (see docs/DEPLOYMENT.md).

FROM python:3.12-slim AS builder

# uv: fast, reproducible dependency resolution from the committed lockfile.
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install dependencies first (cached layer) using only the manifests.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Then the application code (README is referenced by pyproject at build time).
COPY README.md ./README.md
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.12-slim AS runtime

# Non-root runtime user.
RUN groupadd --system praxis && useradd --system --gid praxis --home /app praxis

WORKDIR /app
COPY --from=builder --chown=praxis:praxis /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Entrypoint applies migrations, then starts the API.
COPY --chown=praxis:praxis docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh

USER praxis
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=3).status==200 else 1)"

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
