# Technical Specification: Todo Sharing

## 1. Overview & Objective

### Feature Summary

Cho phép owner chia sẻ Todo list của mình cho user khác với một trong hai quyền:

- `viewer`: chỉ được xem Todo.
- `editor`: được xem, tạo, cập nhật và xóa Todo trong list được chia sẻ.

Owner có thể thu hồi quyền bất kỳ lúc nào.

### Problem Statement

Todo hiện chỉ thuộc về một user và không hỗ trợ cộng tác. Tính năng này cung cấp quyền truy cập có kiểm soát mà không làm thay đổi owner của Todo.

### Target Audience / Roles

- **Owner**: User sở hữu Todo list, có toàn quyền và quản lý quyền chia sẻ.
- **Viewer**: User được cấp quyền đọc.
- **Editor**: User được cấp quyền đọc và chỉnh sửa nội dung Todo.
- **Admin**: Không thuộc scope phiên bản đầu; không có quyền đặc biệt trong API sharing.

## 2. User Stories & Acceptance Criteria

### User Story 1: Chia sẻ Todo list

- **As an** owner
- **I want to** share Todo list với một user bằng email và chọn role
- **So that** user đó có thể cộng tác theo đúng quyền được cấp

- **Acceptance Criteria**:
  - [ ] Owner có thể tạo share với email hợp lệ và role `viewer` hoặc `editor`.
  - [ ] User được share phải tồn tại trong hệ thống.
  - [ ] Owner không thể share cho chính mình.
  - [ ] Một owner không thể tạo hai share đang active cho cùng một user.
  - [ ] Request thành công trả về share record với `id`, owner, grantee và role.

### User Story 2: Xem Todo được chia sẻ

- **As a** viewer hoặc editor
- **I want to** xem Todo list đã được share cho mình
- **So that** mình có thể theo dõi công việc được chia sẻ

- **Acceptance Criteria**:
  - [ ] User chỉ nhìn thấy các list có share đang active.
  - [ ] Viewer và editor đều có thể đọc Todo.
  - [ ] Share bị revoke không còn xuất hiện trong danh sách.
  - [ ] User không được suy đoán hoặc truy cập list không được cấp quyền.

### User Story 3: Chỉnh sửa Todo với quyền editor

- **As an** editor
- **I want to** tạo, cập nhật và xóa Todo trong list được share
- **So that** mình có thể cộng tác với owner

- **Acceptance Criteria**:
  - [ ] Editor được phép create, update và delete Todo thuộc list được share.
  - [ ] Viewer gọi mutation API phải nhận `403 Forbidden`.
  - [ ] Owner vẫn có toàn quyền sau khi share.
  - [ ] Quyền được kiểm tra tại thời điểm request, không dựa trên dữ liệu cache cũ.

### User Story 4: Quản lý và thu hồi quyền

- **As an** owner
- **I want to** xem, đổi role và revoke share
- **So that** mình kiểm soát được người đang truy cập Todo list

- **Acceptance Criteria**:
  - [ ] Owner có thể xem danh sách share active của mình.
  - [ ] Owner có thể đổi role `viewer` ↔ `editor`.
  - [ ] Owner có thể revoke share.
  - [ ] User bị revoke mất quyền ngay lập tức ở các request tiếp theo.
  - [ ] User bị revoke không thể tạo, sửa hoặc xóa Todo bằng URL/ID cũ.

## 3. Scope

### In-Scope

- Chia sẻ toàn bộ Todo list của owner.
- Role `viewer` và `editor`.
- Share theo email của user đã đăng ký.
- List share active của current user.
- Tạo, cập nhật role và revoke share.
- Authorization ở backend cho list và mutation.
- Redis cache isolation/invalidation theo owner và grantee.
- Audit timestamps `created_at`, `updated_at`, `revoked_at`.

### Out-of-Scope

- Share Todo đơn lẻ.
- Public link hoặc anonymous access.
- Email invitation cho user chưa đăng ký.
- Team, group hoặc organization sharing.
- Comment, notification, activity feed.
- Transfer ownership.
- Admin override.
- Offline editing và conflict merge tự động.

## 4. Database Design

### New Table: `todo_shares`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary key | Share identifier |
| `owner_id` | UUID | FK `users.id`, not null | User sở hữu Todo list |
| `grantee_id` | UUID | FK `users.id`, not null | User được cấp quyền |
| `role` | VARCHAR(20) | Not null, check `viewer/editor` | Mức quyền |
| `created_at` | TIMESTAMPTZ | Not null | Thời điểm share |
| `updated_at` | TIMESTAMPTZ | Not null | Thời điểm đổi role |
| `revoked_at` | TIMESTAMPTZ, nullable | Nullable | Thời điểm thu hồi |

### Constraints

- `owner_id != grantee_id`.
- Foreign key `owner_id` và `grantee_id` dùng `ON DELETE CASCADE`.
- Unique constraint trên `(owner_id, grantee_id)` để không có duplicate share.
- Chỉ một share record cho mỗi cặp owner/grantee; revoke dùng `revoked_at` thay vì tạo record mới.
- Check constraint giới hạn role vào `viewer` hoặc `editor`.

### Indexes

- `INDEX todo_shares_owner_active ON todo_shares(owner_id) WHERE revoked_at IS NULL`.
- `INDEX todo_shares_grantee_active ON todo_shares(grantee_id) WHERE revoked_at IS NULL`.
- Unique index hoặc unique constraint `(owner_id, grantee_id)`.

Partial index active phù hợp với các query kiểm tra quyền vì mọi request chỉ quan tâm share chưa bị revoke.

## 5. API Contracts & Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/v1/todo-shares` | Owner share Todo list | Yes |
| GET | `/api/v1/todo-shares/owned` | List share do current user tạo | Yes |
| GET | `/api/v1/todo-shares/received` | List share current user nhận | Yes |
| PATCH | `/api/v1/todo-shares/{share_id}` | Owner đổi role | Yes |
| DELETE | `/api/v1/todo-shares/{share_id}` | Owner revoke share | Yes |
| GET | `/api/v1/shared-todos` | List Todo từ các share active | Yes |

### Create Share

`POST /api/v1/todo-shares`

Request:

```json
{
  "grantee_email": "collaborator@example.com",
  "role": "editor"
}
```

Validation:

- `grantee_email` phải là email hợp lệ.
- `role` chỉ nhận `viewer` hoặc `editor`.
- User phải tồn tại.
- Không được là email của owner.

Response `201 Created`:

```json
{
  "id": "share-uuid",
  "owner_id": "owner-uuid",
  "grantee_id": "grantee-uuid",
  "role": "editor",
  "created_at": "2026-09-18T00:00:00Z",
  "updated_at": "2026-09-18T00:00:00Z",
  "revoked_at": null
}
```

### Update Role

`PATCH /api/v1/todo-shares/{share_id}`

Request:

```json
{
  "role": "viewer"
}
```

Chỉ owner của share được gọi endpoint này.

### Revoke Share

`DELETE /api/v1/todo-shares/{share_id}`

Response:

```text
204 No Content
```

Không xóa vật lý record để giữ audit history; cập nhật `revoked_at`.

### Shared Todo List

`GET /api/v1/shared-todos?page=1&size=20`

Response giữ cùng format pagination với Todo list hiện tại và chỉ gồm Todo từ share active của current user.

### Error Codes

| Status | Use case |
|---:|---|
| `400` | Self-share hoặc request business rule không hợp lệ |
| `401` | Thiếu, hết hạn hoặc revoked JWT |
| `403` | User không phải owner hoặc viewer gọi mutation |
| `404` | User/share/Todo không tồn tại hoặc không thuộc quyền truy cập |
| `409` | Share active đã tồn tại |
| `422` | Payload hoặc role không hợp lệ |

## 6. Business Logic & Security Considerations

### Authorization Matrix

| Action | Owner | Editor | Viewer | Unshared user |
|---|---:|---:|---:|---:|
| Xem Todo list | Yes | Yes | Yes | No |
| Tạo Todo | Yes | Yes | No | No |
| Cập nhật Todo | Yes | Yes | No | No |
| Xóa Todo | Yes | Yes | No | No |
| Tạo share | Yes | No | No | No |
| Đổi role | Yes | No | No | No |
| Revoke share | Yes | No | No | No |

Mọi mutation phải query share/ownership trong cùng request và không tin role do client gửi lên ngoài payload đã validate.

### Security Rules

- Không cho self-share.
- Không cho share cho user không tồn tại.
- Không expose thông tin share của owner khác.
- Không dùng email hoặc role từ client để bypass ownership; xác định user từ JWT.
- Kiểm tra quyền trước khi load hoặc mutate Todo.
- Trả `404` cho tài nguyên không thuộc quyền để hạn chế resource enumeration.
- Revoke phải có hiệu lực ở request kế tiếp, không chờ cache TTL.

### Edge Cases & Race Conditions

- **Mời trùng lặp**: unique constraint trả `409`; không tạo record thứ hai.
- **Re-share sau revoke**: update record cũ, xóa `revoked_at`, cập nhật role và timestamp trong transaction.
- **Owner tự share**: trả `400`.
- **User bị xóa**: cascade xóa share liên quan.
- **Revoke trong lúc editor update**: transaction mutation phải kiểm tra active share tại thời điểm update; request bắt đầu sau revoke nhận `403/404`.
- **Đổi role đồng thời**: dùng transaction và row lock khi cần; kết quả cuối cùng theo commit order.
- **Owner xóa Todo**: Todo bị xóa theo behavior hiện tại; share list không được tạo bản copy.
- **Pagination**: áp dụng giới hạn `size` tối đa giống Todo list hiện tại.

## 7. Caching & Invalidation Strategy

### Cache Keys

- Owner list:
  ```text
  todos:list:owner:{owner_id}:{page}:{size}
  ```
- Shared list:
  ```text
  todos:list:shared:{grantee_id}:{page}:{size}
  ```
- Permission lookup:
  ```text
  todo-share:permission:{owner_id}:{grantee_id}
  ```

Cache payload không được dùng để quyết định authorization cuối cùng; permission phải được xác nhận server-side và cache phải có TTL ngắn.

### Invalidation Events

- Owner tạo/cập nhật/xóa Todo: invalidate cache của owner và mọi grantee có share active.
- Owner tạo share: invalidate shared-list cache của grantee.
- Owner đổi role: invalidate permission cache và shared-list cache của grantee.
- Owner revoke: xóa permission cache ngay lập tức và invalidate shared-list cache của grantee.
- Grantee logout: frontend clear query cache; backend JWT blacklist xử lý token revocation độc lập.

### Consistency

Mutation và cache invalidation phải nằm sau database transaction thành công. Nếu invalidation thất bại, request phải log lỗi và retry theo cơ chế vận hành; không được cấp quyền dựa trên cache cũ sau revoke.

## 8. Rollout & Observability

- Tạo migration trước khi bật API sharing.
- Backfill không cần thiết vì bảng mới rỗng.
- Theo dõi tỷ lệ `403`, `404`, `409` và latency permission lookup.
- Có metric số share active theo owner/grantee.
- Rollback migration chỉ thực hiện sau khi tắt API sharing và xác nhận không còn request phụ thuộc bảng mới.
