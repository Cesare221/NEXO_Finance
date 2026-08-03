# ── Build stage ──────────────────────────────────────────────
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml requirements.lock ./
RUN python -m pip install --upgrade pip && \
    python -m pip install --require-hashes -r requirements.lock

# ── Runtime stage ───────────────────────────────────────────
FROM python:3.14-slim

LABEL org.opencontainers.image.source="https://github.com/nexo-finance/nexo"
LABEL org.opencontainers.image.description="Nexo API"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

RUN addgroup --system nexo && \
    adduser --system --ingroup nexo nexo

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

RUN chown -R nexo:nexo /app

USER nexo

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/ready', timeout=3)"

ENTRYPOINT ["python", "-m"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
