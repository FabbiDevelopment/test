---
name: todo-assessment-fresher
description: Use for this Todo full-stack assessment when reading the codebase, finding bugs, adding backend pytest or Playwright tests, writing specs, improving Docker, tuning PostgreSQL, or implementing fixes with a clear fresher-level workflow.
---

# Todo Assessment Fresher Workflow

## Muc tieu

Xu ly repo theo tung buoc nho, co bang chung va de review. Khong nhay ngay vao refactor lon. Moi ket luan phai gan voi file, ham, test hoac lenh co the lap lai.

## 1. Doc dung luong can sua

- Xac dinh entrypoint va route lien quan.
- Theo dependency auth, service, model/schema, DB va Redis.
- Doc test gan nhat truoc khi sua.
- Viet hypothesis: nguyen nhan nao tao ra behavior sai, va focused check nao co the bac bo no.

## 2. Uu tien bug theo tac dong

Uu tien security va data isolation: expired/tampered token, refresh token dung sai muc dich, cross-user todo access, cache leak. Sau do xu ly data correctness: `completed=False`, partial update, cache invalidation, deterministic pagination. Cuoi cung toi uu: N+1, index, Docker va CORS.

## 3. Cach sua backend

- Auth protected dung dependency hien co; them kiem tra type va expiration tai abstraction auth, khong lap lai o tung route.
- Todo service/query nhan `user_id` va filter ownership tai DB query.
- Partial update dung check field presence/`is not None` phu hop de khong lam mat gia tri falsy.
- Cache key phai co user id va query params; mutation invalidation phai duoc test bang fake Redis.
- Migration moi phai co `upgrade` va `downgrade`, ten index ro rang, va xem xet PostgreSQL large-table lock.

## 4. Cach sua frontend

- Query key bao gom user identity va page/filter.
- Logout xoa access/refresh token, query cache user-scoped va dieu huong login.
- Optimistic mutation luu snapshot, rollback trong `onError`, invalidate trong `onSettled`.
- Giu React Hook Form + Zod va component structure hien tai; khong them state management moi neu chua can.

## 5. Test toi thieu

Backend nen co test cho:

- expired/tampered JWT bi tu choi;
- User A khong doc/update/delete todo cua User B;
- `completed: true -> false`;
- partial title update khong xoa description;
- create/update/delete invalidates cache.

E2E nen co hai context/session tach biet: full user journey va cross-user isolation. Khi chua co Playwright setup, ghi ro server URL, webServer, fixture seed va cach chay headless/headed.

## 6. Tier 3

- Spec sharing: ghi ro user stories, acceptance criteria, data model, API status/error, authorization, race/concurrency, cache revoke va out of scope.
- Docker: healthcheck DB/Redis, backend depends_on healthy, `.dockerignore`, slim/multi-stage image, secrets khong bake vao image.
- DB: chay `EXPLAIN ANALYZE` truoc/sau, index theo predicate + order, ghi benchmark va tradeoff write/storage/lock.

## 7. Validation va bao cao

Chay focused test ngay sau moi edit. Cuoi task chay `cd backend; pytest tests/ -v`, `cd frontend; npm run lint; npm run build`, va `docker compose config` neu co thay doi infrastructure. Bao cao ro test nao da chay, test nao khong the chay, va rui ro con lai.

## 8. Mau ket qua fresher

- Finding: path/function, severity, reproduction, impact.
- Fix: thay doi nho nhat va ly do.
- Test: command + expected/actual.
- Tradeoff: nhung gi chua lam va tai sao.
