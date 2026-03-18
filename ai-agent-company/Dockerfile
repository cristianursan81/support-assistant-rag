FROM python:3.11-slim

WORKDIR /app

# Prevent .pyc files; force unbuffered stdout/stderr (critical for container logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install deps first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Data dir for SQLite persistence (mount as volume)
# Non-root user created after chown so the volume mount is writable
RUN mkdir -p /app/data \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

USER appuser

ENV DATABASE_URL=sqlite:////app/data/gestor.db

EXPOSE 8000 7861

# Uses the existing /health endpoint — fails fast if API is unresponsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "run.py"]
