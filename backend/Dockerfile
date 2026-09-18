# ---- Builder stage: compile/install dependencies only ----
FROM python:3.12-slim AS builder

WORKDIR /app

# gcc is only needed to build wheels for a handful of C-extension deps
# (cryptography, cffi, ...) - it never needs to exist in the runtime image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Runtime stage: slim image, no compiler, non-root user ----
FROM python:3.12-slim AS runtime

# Run as a non-root user rather than the container default root.
RUN useradd --create-home --uid 1000 --shell /bin/bash appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
