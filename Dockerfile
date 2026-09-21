# ============================================================
# AI-Based Cloud Observability System - backend image
# Multi-stage: builder compiles dependencies, runtime is slim.
# ============================================================
FROM python:3.13-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production \
    AWS_ENABLED=false

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

# Application source packages.
COPY backend/ ./backend/
COPY dataset/ ./dataset/
COPY ai/ ./ai/
COPY monitoring/ ./monitoring/
COPY agents/ ./agents/
COPY blockchain/ ./blockchain/
COPY services/ ./services/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).status == 200 else 1)"]

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]