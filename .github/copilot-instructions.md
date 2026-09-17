# Todo Assessment Workspace Instructions

## Muc tieu

Day la ung dung todo full-stack dung FastAPI, SQLAlchemy async, PostgreSQL, Redis, React, TypeScript va TanStack Query. Khi lam viec trong repo nay, uu tien cach lam ro rang, nho, de review va phu hop muc fresher: hieu luong hien tai, sua dung nguyen nhan, viet test cho regression, sau do moi toi uu.

## Ban do he thong

- Backend entrypoint: `backend/app/main.py`.
- API prefix: `/api/v1`; auth o `backend/app/api/v1/auth.py`; todo o `backend/app/api/v1/todos.py`.
- Dependency auth: `backend/app/api/deps.py`; JWT/password: `backend/app/core/security.py`.
- Business logic: `backend/app/services/`; ORM models: `backend/app/models/`; Pydantic schemas: `backend/app/schemas/`.
- Async DB session: `backend/app/db/session.py`; migrations: `backend/alembic/versions/`; seed: `backend/app/db/seed.py`.
- Redis client: `backend/app/core/redis.py`; todo cache behavior currently lives in todo routes.
- Backend tests: `backend/tests/`, using dependency overrides and SQLite test database.
- Frontend entry: `frontend/src/App.tsx`; routes: `frontend/src/router/`; API client: `frontend/src/lib/api.ts`.
- Auth frontend: `frontend/src/features/auth/`; todo frontend: `frontend/src/features/todos/`; pages: `frontend/src/pages/`.
- Infrastructure: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`.

## Cach doc va convention

1. Bat dau tu route, service hoac test gan nhat voi bug. Truy theo luong request: route -> dependency -> service -> DB/cache -> schema.
2. Giu ownership o backend. Moi truy van todo don le phai scope theo `current_user.id`; khong tin user id tu client.
3. JWT access va refresh la hai loai khac. API protected chi nhan access token, kiem tra signature, expiration va token type.
4. Partial update phai phan biet field khong gui va gia tri falsy hop le, dac biet `completed=False`.
5. Cache key phai scope theo user va tat ca tham so truy van. Mutation tao/sua/xoa phai invalidation cache lien quan.
6. Frontend query key phai bao gom user/filter/page; logout phai xoa token va cache user-scoped.
7. Dung schema Pydantic/Zod hien co; giu API public va style hien tai tru khi thay doi la can thiet.
8. Khong them abstraction moi neu service/helper hien tai da du. Khong sua file khong lien quan.
9. Moi thay doi hanh vi quan trong phai co test regression ngan, de doc, ten mo ta duong happy path va boundary.
10. Khi serialize danh sach, tranh N+1; khi phan trang, dat thu tu deterministic, thuong `created_at DESC, id DESC`.

## Thu tu lam viec fresher

- Doc code va test lien quan, viet mot hypothesis ngan ve nguyen nhan.
- Sua mot slice nho nhat co the test duoc.
- Chay focused test/typecheck ngay sau edit.
- Neu test pass, bo sung test boundary va cap nhat docs/migration neu contract thay doi.
- Cuoi cung chay full backend tests, frontend lint/build va smoke check Docker neu thay doi infrastructure.
- Bao cao file da doi, ly do, lenh validation, ket qua va residual risk.

## Lenh kiem tra chuan

- Backend: `cd backend; pytest tests/ -v`
- Backend migration: `cd backend; alembic upgrade head`
- Frontend: `cd frontend; npm run lint; npm run build`
- Docker: `docker compose config` va `docker compose up --build`
- Seed lon: `docker compose exec -e SEED_USERS=10000 -e SEED_TODOS=1000000 backend python -m app.db.seed`

## Cac diem rui ro da biet can uu tien

- `verify_exp=False` co the chap nhan JWT het han.
- Dependency auth can phan biet access token va refresh token.
- GET/PUT/DELETE todo don le phai ngan truy cap cheo user.
- Cache list khong duoc dung key toan cuc nhu `todos:list`.
- Tao/sua/xoa todo phai invalidation cache.
- Toggle `true -> false` phai persist.
- Logout phai lam sach React Query cache; optimistic update phai rollback khi mutation fail.
- Email can unique constraint/index de tranh duplicate do race condition.
- CORS, secret, healthcheck, Docker ignore va DB index can duoc danh gia theo moi truong.

## Nguyen tac an toan

- Khong commit secret that; dung `.env` va `.env.example` cho gia tri mau.
- Khong dung `git reset --hard`, khong revert thay doi cua user.
- Khong commit neu user khong yeu cau.
- Khong coi test SQLite la bang chung day du cho PostgreSQL/Redis; ghi ro gioi han nay trong ket qua.
