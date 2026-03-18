# ── Stage 1: builder ─────────────────────────────────────────────────────────
# Installs all Python deps into /install so the runtime stage stays lean.
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# curl is required for the HEALTHCHECK below
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder — keeps this layer reproducible
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Data dir for SQLite persistence (overridden by volume mount in compose).
# Non-root user uid=1000 so mounted volumes stay writable on most Linux hosts.
RUN mkdir -p /app/data \
    && adduser --disabled-password --gecos "" --uid 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

ENV DATABASE_URL=sqlite:////app/data/gestor.db

EXPOSE 8000 7861

# Requires curl (installed above). Checks the existing /health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production entrypoint: Gunicorn + UvicornWorker serves FastAPI on :8000.
# For the Gradio dashboard (:7861) run: docker exec <container> python run.py dashboard
# or add a second service in docker-compose.yml.
CMD ["gunicorn", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "src.api:app"]
