# Docker & Infrastructure Optimization

## 1. Overview & Problem Analysis

In the initial repository setup, several containerization and orchestration issues were identified:

1. **Cold Boot Race Condition (Unreliable Startup Order)**:
   - In `docker-compose.yml`, the `backend` service used `depends_on: [postgres, redis]` without health condition checks.
   - Docker interprets standard `depends_on` only as "container started", not "service ready to accept TCP connections".
   - When launching services on a cold host or under heavy load, PostgreSQL takes several seconds to initialize database clusters and listen on port 5432. The backend attempted to execute `alembic upgrade head` immediately upon boot, crashing with database connection errors (`ConnectionRefusedError: [Errno 111] Connect call failed`).

2. **Bloated Build Context & Cache Invalidation (Missing `.dockerignore`)**:
   - Neither `backend/` nor `frontend/` had a `.dockerignore` file.
   - When running `docker compose build`, Docker transferred the entire host `node_modules/` (hundreds of megabytes) and Python virtual environment (`.venv`, `__pycache__`) into the build context daemon.
   - This caused excessively long build transfer times, invalidated layer caching unnecessarily on host file changes, and risked platform binary mismatches (e.g. Windows host native modules copied into Linux containers).

3. **Insecure & Unoptimized Production Posture**:
   - The default `docker-compose.yml` exposed PostgreSQL (port 5432) and Redis (port 6379) directly to the host network. In a cloud or VPS deployment, exposing database and cache ports creates severe attack vectors for unauthorized access and brute-force attacks.
   - Backend ran with single-process Uvicorn without worker scaling or restart recovery policies (`restart: unless-stopped`).

---

## 2. Implemented Optimizations

### 2.1 Dependable Healthchecks & Orchestrated Startup Order
- **PostgreSQL**: Configured native healthcheck using `pg_isready -U fabbi -d postgres` with 5s interval, 5s timeout, and 10s start period.
- **Redis**: Configured native healthcheck using `redis-cli ping` with 5s interval and 3s timeout.
- **Backend**:
  - Configured `depends_on` with `condition: service_healthy` for both `postgres` and `redis`. Backend now waits deterministically until database and cache are fully responsive before executing migrations and launching Uvicorn.
  - Added backend application healthcheck invoking `GET /health` via Python standard library `urllib.request`.
- **Frontend**: Configured `depends_on: { backend: { condition: service_healthy } }` ensuring the API is ready before frontend client starts.

```yaml
# docker-compose.yml excerpt
postgres:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U fabbi -d postgres"]
    interval: 5s
    timeout: 5s
    retries: 5
    start_period: 10s

redis:
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 3s
    retries: 5
    start_period: 5s

backend:
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  healthcheck:
    test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health')\" || exit 1"]
    interval: 5s
    timeout: 5s
    retries: 5
    start_period: 10s
```

---

### 2.2 Build Context Optimization (`.dockerignore`)
Added strict `.dockerignore` files for both services:

- **`backend/.dockerignore`**:
  - Excludes `__pycache__`, `*.pyc`, `*.pyo`, `.Python`.
  - Excludes local virtual environments (`.venv`, `venv`, `env`).
  - Excludes test caches and local databases (`.pytest_cache`, `.coverage`, `htmlcov`, `test.db`, `*.sqlite3`).
  - Excludes VCS files (`.git`, `.gitignore`) and IDE configuration (`.vscode`, `.idea`).

- **`frontend/.dockerignore`**:
  - Excludes host `node_modules/` (preventing multi-hundred megabyte context uploads).
  - Excludes build artifacts (`dist/`, `build/`).
  - Excludes test reports (`test-results/`, `playwright-report/`).
  - Excludes environment overrides (`.env.local`, `.env.*.local`) and debug logs.

---

### 2.3 Production Architecture (`docker-compose.prod.yml`)
Created a dedicated production compose specification separating development workflows from production deployments:

1. **Network Isolation (Zero DB/Cache Host Exposure)**:
   - Defined two networks: `app-internal` (`internal: true`) and `app-public` (`driver: bridge`).
   - `postgres` and `redis` attach solely to `app-internal` with **no host port mappings**. They can only be reached by `backend` within the Docker network bridge.
   - `backend` bridges both networks (`app-internal` to query DB/cache, `app-public` to receive API requests).
   - `frontend` attaches to `app-public`.

2. **Process Concurrency & Scalability**:
   - Backend command executes Uvicorn with multiple worker processes:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
     ```
   - This allows concurrent request handling and maximizes multi-core CPU utilization in production.

3. **High Availability & Fault Recovery**:
   - Added `restart: unless-stopped` across all production containers to automatically recover from unhandled runtime panics or host reboots.

4. **Configurable Secrets**:
   - Environment variables dynamically default with fallback or interpolate from `.env.prod`:
     `${POSTGRES_USER}`, `${POSTGRES_PASSWORD}`, `${POSTGRES_DB}`, `${JWT_SECRET}`.

---

## 3. Verification & Validation

### Validate Compose Configurations
```bash
# Verify development compose syntax and healthcheck definitions
docker compose config

# Verify production compose syntax and network isolation
docker compose -f docker-compose.prod.yml config
```

### Cold Boot Verification
When executing `docker compose up -d`:
1. `postgres` and `redis` start first and enter `(health: starting)`.
2. `backend` remains in `waiting` state until both PostgreSQL and Redis transition to `(healthy)`.
3. `backend` executes database migrations and boots Uvicorn cleanly without race conditions.
4. `frontend` starts once `backend` becomes healthy.
