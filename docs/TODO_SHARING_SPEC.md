# Technical Specification: Todo List Sharing

> Spec cho tính năng chia sẻ todo list với quyền viewer/editor, dựa trên
> [`templates/SPEC_TEMPLATE.md`](../templates/SPEC_TEMPLATE.md).
> **Không implement code** — đây là tài liệu thiết kế.

## 1. Overview & Objective

- **Feature Summary**: Cho phép chủ sở hữu (owner) một todo list chia sẻ
  *toàn bộ danh sách todo của mình* cho user khác đã có tài khoản, với quyền
  **viewer** (chỉ xem) hoặc **editor** (xem + tạo/sửa/tick/xoá todo trong
  list đó). Owner có thể thu hồi quyền bất kỳ lúc nào, có hiệu lực ngay lập
  tức.
- **Problem Statement**: Hiện tại mỗi todo chỉ thuộc về đúng 1 user
  (`Todo.user_id`), không có cách nào để cộng tác (vd: vợ/chồng cùng quản lý
  1 to-do list gia đình, hoặc leader xem tiến độ task của thành viên).
- **Target Audience / Roles**:
  - **Owner**: user tạo ra todo list, có toàn quyền (đọc/ghi/chia sẻ/thu
    hồi).
  - **Collaborator — Viewer**: chỉ đọc được todo của owner, không tạo/sửa/xoá
    được.
  - **Collaborator — Editor**: đọc + tạo/sửa (title, description,
    completed)/xoá todo trong list được chia sẻ, **nhưng không được** chia
    sẻ tiếp cho người khác hay thu hồi quyền của người khác (chỉ owner mới
    quản lý share).

**Giả định thiết kế quan trọng**: hệ thống hiện tại không có khái niệm
"TodoList" là 1 entity riêng — mỗi user chỉ có đúng 1 "danh sách" ngầm định
là tập hợp tất cả `Todo` có `user_id` của họ. Vì vậy "share todo list" trong
spec này nghĩa là **cấp quyền truy cập vào toàn bộ tập todo của 1 owner**,
không phải chia sẻ từng todo riêng lẻ. Nếu sau này cần chia sẻ từng todo
riêng, cần thêm bảng `todo_id` vào scope — ghi nhận ở mục Out-of-Scope.

## 2. User Stories & Acceptance Criteria

### User Story 1: Owner chia sẻ todo list

- **As a** todo list owner
- **I want to** mời 1 user khác (theo email) vào xem hoặc cùng chỉnh sửa
  todo list của tôi, với quyền viewer hoặc editor
- **So that** chúng tôi có thể cộng tác quản lý công việc chung
- **Acceptance Criteria**:
  - [ ] Owner nhập email của user đã tồn tại trong hệ thống + chọn quyền
        (`viewer`/`editor`) → tạo bản ghi share thành công, hiệu lực ngay.
  - [ ] Không thể tự chia sẻ cho chính mình (email trùng với email của
        owner) → lỗi 400.
  - [ ] Không thể chia sẻ cho email chưa đăng ký tài khoản → lỗi 404 (v1
        không hỗ trợ invite-by-email cho người chưa có tài khoản).
  - [ ] Chia sẻ trùng lặp (đã share cho user đó, chưa revoke) → lỗi 409,
        gợi ý dùng API update quyền thay vì tạo mới.

### User Story 2: Collaborator xem/sửa todo được chia sẻ

- **As a** collaborator (viewer hoặc editor)
- **I want to** xem danh sách todo mà người khác đã chia sẻ với tôi, và sửa
  được nếu tôi có quyền editor
- **So that** tôi biết mình đang được truy cập vào những list nào và làm
  việc trên đó
- **Acceptance Criteria**:
  - [ ] `GET /todo-lists/shared-with-me` trả về danh sách các owner đã chia
        sẻ cho tôi, kèm quyền hiện tại (`viewer`/`editor`).
  - [ ] Viewer gọi `GET` todo của owner → 200, thấy đúng dữ liệu.
  - [ ] Viewer gọi `POST/PUT/DELETE` todo của owner → 403 Forbidden.
  - [ ] Editor gọi `POST/PUT/DELETE` todo của owner → thành công, thay đổi
        có hiệu lực với owner và mọi collaborator khác ngay lập tức.
  - [ ] Editor **không** thể xoá/sửa bản ghi share hay mời thêm người khác.

### User Story 3: Owner thu hồi quyền truy cập

- **As a** todo list owner
- **I want to** thu hồi quyền của 1 collaborator bất kỳ lúc nào
- **So that** tôi kiểm soát được ai đang truy cập vào dữ liệu của mình
- **Acceptance Criteria**:
  - [ ] `DELETE` share → collaborator ngay lập tức không còn gọi được bất kỳ
        endpoint nào liên quan đến todo list đó (kể cả nếu họ đang có
        request đang xử lý dở — request tiếp theo phải bị chặn ngay, không
        đợi cache TTL).
  - [ ] Sau khi revoke, `GET /todo-lists/shared-with-me` của collaborator
        không còn liệt kê owner đó nữa.
  - [ ] Owner có thể mời lại (share lại) cùng user đó sau khi đã revoke,
        không bị chặn bởi unique constraint (vì bản ghi cũ đã revoke, coi
        như không còn active).

### User Story 4: Owner thay đổi quyền của collaborator

- **As a** todo list owner
- **I want to** đổi quyền của 1 collaborator từ viewer → editor (hoặc
  ngược lại) mà không cần revoke rồi share lại
- **So that** thao tác gọn hơn và giữ được lịch sử/thời điểm share ban đầu
- **Acceptance Criteria**:
  - [ ] `PATCH /todo-lists/shares/{share_id}` với `{"permission": "editor"}`
        → cập nhật thành công, có hiệu lực ngay ở request tiếp theo của
        collaborator.

## 3. Scope

### In-Scope

- Share theo **toàn bộ todo list** của 1 owner cho 1 user khác đã có tài
  khoản, với 2 mức quyền: `viewer`, `editor`.
- Owner thu hồi / đổi quyền bất kỳ lúc nào.
- Danh sách "ai tôi đã share cho" (owner view) và "ai đã share cho tôi"
  (collaborator view).
- Editor được tạo/sửa/tick/xoá todo trong list được chia sẻ; không được
  quản lý share.
- Authorization + cache invalidation nhất quán với cơ chế hiện có của
  `todos` (đã fix ở Tier 1: cache theo per-owner key, invalidate on write).

### Out-of-Scope (v1)

- Chia sẻ **từng todo riêng lẻ** (thay vì cả list) — để dành phiên bản sau,
  cần thêm `todo_id` (nullable) vào bảng share.
- Invite user **chưa có tài khoản** qua email (magic-link signup) — v1 yêu
  cầu người được mời đã đăng ký sẵn.
- Luồng **accept/decline lời mời** — v1 owner cấp quyền trực tiếp, có hiệu
  lực ngay, không cần collaborator xác nhận. (Cân nhắc thêm ở v2 nếu cần
  UX "tôi được mời, tôi đồng ý mới thấy".)
- **Resharing** — collaborator (kể cả editor) không được mời thêm người
  khác vào list mà mình chỉ đang được chia sẻ.
- **Role thứ 3 dạng "admin/co-owner"** (có thể tự quản lý share) — chỉ có
  đúng 1 owner cố định = `todos.user_id`.
- Thông báo real-time (WebSocket/push) khi có thay đổi từ collaborator khác
  — client tự poll/refetch theo cơ chế React Query hiện có.
- Optimistic concurrency control (ví dụ `If-Match` theo `updated_at`) khi 2
  editor sửa cùng 1 todo cùng lúc — giữ nguyên hành vi last-write-wins hiện
  tại của hệ thống, ghi nhận là hạn chế đã biết.

## 4. Database Design

### New Table: `todo_list_shares`

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | PK, default `gen_random_uuid()` |
| `owner_id` | UUID | FK → `users(id)` ON DELETE CASCADE, NOT NULL |
| `shared_with_user_id` | UUID | FK → `users(id)` ON DELETE CASCADE, NOT NULL |
| `permission` | VARCHAR(10) (hoặc native enum `share_permission`) | NOT NULL, CHECK IN (`'viewer'`, `'editor'`) |
| `created_at` | TIMESTAMPTZ | NOT NULL, default `now()` |
| `updated_at` | TIMESTAMPTZ | NOT NULL, default `now()`, on update `now()` |
| `revoked_at` | TIMESTAMPTZ | NULL — `NULL` = đang active, có giá trị = đã bị thu hồi |

**Vì sao soft-delete (`revoked_at`) thay vì xoá cứng?**
Giữ lịch sử ai từng có quyền gì (audit trail) và cho phép owner "share lại"
đúng người mà không bị lỗi trùng khoá do bản ghi cũ chưa dọn.

### Constraints & Indexes

```sql
-- Không tự share cho chính mình
ALTER TABLE todo_list_shares
  ADD CONSTRAINT chk_no_self_share CHECK (owner_id <> shared_with_user_id);

-- Chỉ tối đa 1 share "đang active" giữa 1 cặp (owner, collaborator)
-- Partial unique index: bỏ qua các bản ghi đã revoke.
CREATE UNIQUE INDEX uq_active_share
  ON todo_list_shares (owner_id, shared_with_user_id)
  WHERE revoked_at IS NULL;

-- Tra cứu "list được share cho tôi" nhanh
CREATE INDEX ix_shares_shared_with_active
  ON todo_list_shares (shared_with_user_id)
  WHERE revoked_at IS NULL;

-- Tra cứu "tôi đã share cho ai" nhanh
CREATE INDEX ix_shares_owner_active
  ON todo_list_shares (owner_id)
  WHERE revoked_at IS NULL;
```

**Cascade delete**: nếu `owner_id` hoặc `shared_with_user_id` bị xoá tài
khoản (`users` row deleted) → toàn bộ share liên quan tự động bị xoá
(`ON DELETE CASCADE`), tránh orphan record và tránh lộ quyền truy cập vào
dữ liệu của tài khoản đã không còn tồn tại.

`todos` table: **không đổi schema** — authorization layer sẽ join sang
`todo_list_shares` khi cần, không thêm cột vào `todos`.

## 5. API Contracts & Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/v1/todo-lists/shares` | Owner mời 1 user (theo email) với quyền viewer/editor | Yes |
| GET | `/api/v1/todo-lists/shares` | Owner xem danh sách mình đã share cho ai | Yes |
| PATCH | `/api/v1/todo-lists/shares/{share_id}` | Owner đổi quyền của 1 share | Yes |
| DELETE | `/api/v1/todo-lists/shares/{share_id}` | Owner thu hồi 1 share | Yes |
| GET | `/api/v1/todo-lists/shared-with-me` | Collaborator xem các owner đã share cho mình + quyền hiện tại | Yes |
| GET | `/api/v1/todo-lists/{owner_id}/todos` | Xem todo list của `owner_id` (owner hoặc collaborator có quyền) — tái dùng pagination như `GET /todos` | Yes |
| POST | `/api/v1/todo-lists/{owner_id}/todos` | Tạo todo trong list của `owner_id` — chỉ owner hoặc editor | Yes |
| PUT | `/api/v1/todo-lists/{owner_id}/todos/{todo_id}` | Sửa todo — chỉ owner hoặc editor | Yes |
| DELETE | `/api/v1/todo-lists/{owner_id}/todos/{todo_id}` | Xoá todo — chỉ owner hoặc editor | Yes |

> `GET/POST/PUT/DELETE /api/v1/todos` (không có `owner_id` trong path) giữ
> nguyên hành vi hiện tại — luôn chỉ thao tác trên todo của **chính người
> gọi**. Các endpoint `/todo-lists/{owner_id}/todos/...` là bộ endpoint mới
> dành riêng cho truy cập chéo user qua cơ chế share, để tách bạch rõ ràng
> và không thay đổi behavior/test hiện có của `/todos`.

### Request/Response chi tiết

**`POST /api/v1/todo-lists/shares`**

```jsonc
// Request
{
  "email": "collaborator@example.com",
  "permission": "editor"          // "viewer" | "editor"
}

// 201 Created
{
  "id": "b7e6...",
  "owner_id": "1111...",
  "shared_with_user_id": "2222...",
  "shared_with_email": "collaborator@example.com",
  "permission": "editor",
  "created_at": "2026-09-17T10:00:00Z"
}

// 400 Bad Request — tự share cho chính mình
{ "detail": "Cannot share your todo list with yourself" }

// 404 Not Found — email chưa có tài khoản
{ "detail": "No registered user with this email" }

// 409 Conflict — đã share (đang active) cho user này
{ "detail": "This user already has access. Use PATCH to change their permission." }
```

**`PATCH /api/v1/todo-lists/shares/{share_id}`**

```jsonc
// Request
{ "permission": "viewer" }

// 200 OK -> share object đã cập nhật
// 403 Forbidden -> người gọi không phải owner của share này
// 404 Not Found -> share_id không tồn tại hoặc đã bị revoke
```

**`DELETE /api/v1/todo-lists/shares/{share_id}`**

- 204 No Content khi thành công (set `revoked_at = now()`).
- 403 Forbidden nếu người gọi không phải owner.
- 404 nếu share không tồn tại/đã revoke từ trước (idempotent — gọi lại
  không lỗi 500, nhưng cũng không lộ thông tin share thuộc user khác).

**`GET /api/v1/todo-lists/{owner_id}/todos`**

- Query params giống hệt `GET /todos` hiện có: `page`, `size`.
- 200 OK — cùng schema `TodoListResponse` hiện có.
- 403 Forbidden nếu người gọi không phải owner và không có share active
  nào (viewer hoặc editor) với `owner_id` này. **Dùng 403, không dùng 404**
  ở đây (khác với hành vi IDOR-safe 404 của `/todos/{id}` hiện tại) vì
  `owner_id` là tham số path công khai chọn chủ động bởi client (không phải
  ID tài nguyên nhạy cảm bị đoán mò) — trả 403 rõ ràng "không có quyền" hợp
  lý hơn và không có rủi ro information disclosure tương đương IDOR.

**`POST/PUT/DELETE /api/v1/todo-lists/{owner_id}/todos[/...]`**

- 403 Forbidden nếu người gọi không phải owner và không có quyền `editor`
  active (viewer gọi các endpoint ghi → 403).
- Còn lại tái sử dụng toàn bộ validation hiện có của `TodoCreate`/
  `TodoUpdate` (bao gồm fix `exclude_unset=True` đã làm ở Tier 1).

**`GET /api/v1/todo-lists/shared-with-me`**

```jsonc
// 200 OK
{
  "items": [
    {
      "owner_id": "1111...",
      "owner_email": "owner@example.com",
      "permission": "viewer",
      "shared_since": "2026-09-10T08:00:00Z"
    }
  ]
}
```

## 6. Business Logic & Security Considerations

### Authorization & Permission Matrix

| Hành động | Owner | Collaborator (viewer) | Collaborator (editor) | Người ngoài (không share) |
|---|---|---|---|---|
| Xem todo list | ✅ | ✅ | ✅ | ❌ (403) |
| Tạo/sửa/xoá/tick todo | ✅ | ❌ (403) | ✅ | ❌ (403) |
| Mời thêm collaborator | ✅ | ❌ | ❌ | ❌ |
| Đổi quyền / thu hồi share | ✅ | ❌ | ❌ | ❌ |
| Xem danh sách "tôi đã share cho ai" | ✅ | — | — | — |

Hàm authorization trung tâm (dùng lại cho mọi endpoint `/todo-lists/{owner_id}/...`):

```
def resolve_access(current_user_id, owner_id, db) -> "owner" | "editor" | "viewer" | None:
    if current_user_id == owner_id:
        return "owner"
    share = query todo_list_shares
              where owner_id = owner_id
                and shared_with_user_id = current_user_id
                and revoked_at IS NULL
    return share.permission if share else None
```

Quan trọng: **permission luôn được resolve bằng 1 query DB trực tiếp tại
thời điểm request**, không cache permission vào JWT hay Redis. Đây là quyết
định thiết kế cốt lõi để đáp ứng yêu cầu "revoke có hiệu lực ngay lập tức"
(xem mục 7).

### Edge Cases & Race Conditions

- **Tự share cho chính mình**: chặn ở cả DB level (`CHECK` constraint) lẫn
  API level (validate `email` resolve ra `user.id != current_user.id` →
  400 trước khi chạm DB, để trả message rõ ràng thay vì lỗi constraint
  chung chung).
- **Mời trùng lặp**: chặn bằng partial unique index `uq_active_share`. API
  bắt `IntegrityError` và convert thành 409 Conflict thay vì 500.
- **Owner thu hồi quyền đúng lúc collaborator đang gửi request sửa**: vì
  permission được resolve trực tiếp từ DB mỗi request (không cache), race
  condition duy nhất còn lại là "request ghi của collaborator đã đi vào
  transaction ngay trước khi transaction revoke commit" — đây là race
  condition bình thường ở mức DB (2 transaction độc lập), Postgres
  read-committed isolation đã đảm bảo mỗi transaction thấy trạng thái nhất
  quán tại thời điểm nó bắt đầu; request ghi hoàn tất trước hoặc sau lệnh
  revoke tuỳ thứ tự commit — chấp nhận được, không cần lock đặc biệt vì đây
  không phải thao tác tài chính cần serializable isolation.
- **Editor bị revoke rồi được share lại với quyền viewer**: do
  `uq_active_share` chỉ tính bản ghi `revoked_at IS NULL`, thao tác share
  lại tạo **row mới** (không update lại row cũ) → giữ đúng lịch sử audit
  (share lần 1: editor, 10:00–10:05; share lần 2: viewer, từ 10:10).
- **Owner tự xoá tài khoản**: `ON DELETE CASCADE` tự dọn hết share liên
  quan; collaborator sẽ thấy owner đó biến mất khỏi
  `GET /shared-with-me` ở lần gọi tiếp theo (không cần xử lý gì thêm nhờ
  permission luôn resolve trực tiếp từ DB).

## 7. Caching & Invalidation Strategy

- **Dữ liệu todo list** (nội dung todo) tiếp tục dùng đúng cache key hiện
  có từ Tier 1: `todos:list:{owner_id}:{page}:{size}`. Vì nội dung list là
  **giống nhau** dù người xem là owner hay collaborator (không lọc theo
  viewer), owner và mọi collaborator **dùng chung 1 cache entry** theo
  `owner_id` — không cần nhân bản cache theo từng viewer.
  - Khi editor tạo/sửa/xoá todo qua `/todo-lists/{owner_id}/todos/...`:
    invalidate đúng key pattern `todos:list:{owner_id}:*` — **tái dùng
    y nguyên** cơ chế `_invalidate_list_cache(redis, owner_id)` đã có sẵn
    từ Tier 1, không cần thêm logic mới.
- **Permission (quyền share) không được cache** — luôn query DB trực tiếp
  (mục 6). Vì vậy revoke/đổi quyền **không cần bước invalidate cache nào
  cả**, vì không có gì để invalidate: đây là cách đơn giản nhất để đảm bảo
  đúng yêu cầu "revoke có hiệu lực ngay lập tức" mà không cần thiết kế thêm
  1 tầng cache + invalidation riêng cho permission.
  - **Tradeoff**: mỗi request vào `/todo-lists/{owner_id}/...` tốn thêm 1
    query nhỏ (index lookup theo partial index `ix_shares_shared_with_active`,
    rất rẻ) so với việc cache permission. Ở quy mô hiện tại (todo app cho
    nhóm nhỏ, không phải hệ thống permission hàng triệu QPS), đánh đổi này
    hợp lý để giữ đúng tính nhất quán ngay lập tức thay vì phải tự xây cơ
    chế invalidate phức tạp (dễ sai, dễ leak quyền cũ trong vài giây).
  - Nếu sau này cần cache permission (ví dụ do query share trở thành
    bottleneck), đề xuất cache key `perm:{owner_id}:{shared_with_user_id}`
    với TTL ngắn (≤30s) **cộng với** invalidate tường minh tại 3 điểm ghi:
    tạo share, đổi quyền (PATCH), thu hồi (DELETE) — nhưng đây là
    optimization để dành cho sau, out of scope v1.
