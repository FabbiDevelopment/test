# Tier 3 Verification Matrix

## 3A — Todo Sharing Specification

| Requirement | Evidence | Result |
|---|---|---|
| User stories and acceptance criteria | Five stories covering grant, discovery, viewer/editor behavior, revocation, and ownership | Pass |
| Data model | `todo_list_shares` fields, enum, FKs, uniqueness, self-share check, cascade behavior, and indexes | Pass |
| API design | Nine endpoints, schemas, pagination, success/error codes, and error envelope | Pass |
| Authorization and edge cases | Permission matrix, no re-share, duplicate/self-share, races/locking, immediate revoke invalidation | Pass |
| Explicit out-of-scope | Invitations, per-todo grants, public links, groups, transfer, comments, and other deferred work | Pass |

Artifact: `docs/TODO_SHARING_SPEC.md`.

## 3B — Docker and infrastructure

| Improvement | Evidence | Result |
|---|---|---|
| PostgreSQL/Redis healthchecks | `pg_isready`, authenticated `redis-cli ping` | Pass |
| Startup gating | Backend requires healthy PostgreSQL/Redis; frontend requires healthy backend | Pass |
| Build-context hygiene | Backend/frontend `.dockerignore` exclude dependencies, virtualenvs, test DBs, caches, reports | Pass |
| Smaller/safer backend | Multi-stage wheel build, slim runtime, non-root `app` user | Pass |
| Smaller frontend runtime | Reproducible `npm ci` build copied into Nginx Alpine; SPA and health route configured | Pass |
| Production overlay | Required secrets, DB/cache ports removed, restart policies, SQL echo disabled | Pass |
| Redis security | Password required, authenticated healthcheck, persistent volume; no secret baked into image | Pass |

Validation:

```text
docker-compose -f docker-compose.yml config --quiet                                      PASS
docker-compose -f docker-compose.yml -f docker-compose.prod.yml config --quiet          PASS
production postgres ports = null; production redis ports = null                         PASS
```

Image builds were not executed locally because no Docker daemon is installed; Compose structure and interpolation were validated with Docker Compose 5.5.1.

## 3C — Database indexing and query tuning

| Requirement | Evidence | Result |
|---|---|---|
| EXPLAIN ANALYZE before indexes | Three queries recorded on PostgreSQL 16.15 / 1M todos | Pass |
| Optimal indexes and migration | Two workload-specific composite indexes in revision `c41f86a92d10` | Pass |
| Before/after benchmark table | Exact execution times and plan changes documented | Pass |
| Trade-offs and migration safety | Write/storage/cache costs, concurrent build failure/retry, disk headroom, rollout | Pass |

Measured summary:

| Query | Before | After |
|---|---:|---:|
| User newest 20 | 41.154 ms | 0.053 ms |
| User count | 41.295 ms | 0.401 ms |
| User incomplete newest 20 | 43.872 ms | 0.020 ms |

PostgreSQL migration validation:

```text
upgrade a0790c76a129 -> c41f86a92d10       PASS
downgrade c41f86a92d10 -> a0790c76a129     PASS
upgrade a0790c76a129 -> c41f86a92d10       PASS
```

Artifacts: `backend/scripts/benchmark_todo_queries.sql`, migration `c41f86a92d10`, and `docs/DATABASE_INDEX_BENCHMARK.md`.
