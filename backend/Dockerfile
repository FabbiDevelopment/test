# THÊM: Multi-stage build — giảm kích thước image runtime (Level 3B)
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime

WORKDIR /app

# SAI (cũ): single-stage COPY toàn bộ + gcc trong image runtime → image lớn, attack surface cao
# THÊM: chỉ copy packages đã build từ builder stage
COPY --from=builder /install /usr/local

COPY . .

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Dev/default CMD — prod dùng docker-compose.prod.yml (workers, secrets qua env)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
