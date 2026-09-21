# payment-service image (STEP 4).
# Build from the repository root:
#   docker build -f services/payment_service/Dockerfile -t observability-payment-service .
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependencies first (better layer caching).
COPY services/payment_service/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Only the application files this service needs at runtime.
COPY services/__init__.py ./services/__init__.py
COPY services/events.py ./services/events.py
COPY services/registry.py ./services/registry.py
COPY services/common/ ./services/common/
COPY services/payment_service/__init__.py ./services/payment_service/__init__.py
COPY services/payment_service/app/ ./services/payment_service/app/

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8003

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8003/health', timeout=5).status == 200 else 1)"]

CMD ["uvicorn", "services.payment_service.app.main:app", "--host", "0.0.0.0", "--port", "8003"]