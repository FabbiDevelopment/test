# Technical Specification: Todo Sharing & Access Control (Tính Năng Chia Sẻ Todo)

> Tài liệu đặc tả kỹ thuật tiêu chuẩn sản xuất (Production-grade Specification) cho tính năng Todo Sharing, tuân thủ đúng cấu trúc biểu mẫu [`templates/SPEC_TEMPLATE.md`](../templates/SPEC_TEMPLATE.md).

---

## 1. Overview & Objective (Tổng Quan & Mục Tiêu)

- **Feature Summary**: Tính năng cho phép người dùng (Owner) chia sẻ danh sách Todo cá nhân của mình cho những người dùng khác trong hệ thống với quyền hạn cụ thể (**Viewer - Chỉ xem** hoặc **Editor - Chỉnh sửa**). Chủ sở hữu có toàn quyền thay đổi phân quyền hoặc thu hồi quyền truy cập bất cứ lúc nào.
- **Problem Statement**: Hiện tại, ứng dụng Todo hoạt động theo mô hình dữ liệu cô lập 1-1 (mỗi người dùng chỉ thấy và quản lý Todo của riêng mình). Người dùng không có khả năng cộng tác nhóm, phân chia công việc trong gia đình/dự án hoặc chia sẻ tiến độ cho người khác cùng theo dõi.
- **Target Audience / Roles**:
  - **Owner (Chủ sở hữu)**: Người tạo ra các Todo, sở hữu toàn quyền quản lý dữ liệu, phân quyền và thu hồi quyền chia sẻ.
  - **Collaborator / Editor (Người cộng tác có quyền sửa)**: Được Owner cấp quyền xem và cập nhật trạng thái/tiêu đề/mô tả của các Todo được chia sẻ.
  - **Collaborator / Viewer (Người cộng tác có quyền đọc)**: Chỉ có quyền xem danh sách Todo, không được phép chỉnh sửa hoặc xóa bất kỳ Todo nào.

---

## 2. User Stories & Acceptance Criteria

### User Story 1: Owner chia sẻ danh sách cho người khác qua Email
- **As an** Owner (Chủ sở hữu Todo)
- **I want to** nhập email của một người dùng khác và chọn vai trò (`viewer` hoặc `editor`) để chia sẻ danh sách Todo
- **So that** người đó có thể cùng tôi theo dõi hoặc cập nhật công việc chung
- **Acceptance Criteria**:
  - [ ] Hệ thống kiểm tra email người được mời phải tồn tại trong cơ sở dữ liệu. Nếu không tìm thấy, trả về lỗi HTTP 404 Not Found (`"User with this email not found"`).
  - [ ] Không cho phép Owner tự chia sẻ cho chính mình. Nếu nhập email của chính mình, trả về HTTP 400 Bad Request (`"Cannot share todo list with yourself"`).
  - [ ] Không cho phép gửi lời mời trùng lặp nếu người đó đã được chia sẻ trước đó. Trả về HTTP 409 Conflict (`"User already has access to this todo list"`).
  - [ ] Sau khi chia sẻ thành công, dữ liệu được lưu vào bảng `todo_shares` và lập tức xóa cache liên quan trong Redis.

---

### User Story 2: Collaborator xem và cập nhật Todo được chia sẻ
- **As a** Collaborator (Viewer hoặc Editor)
- **I want to** xem danh sách các Todo được chia sẻ với mình và thao tác theo đúng quyền hạn được cấp
- **So that** tôi có thể nắm bắt tiến độ công việc hoặc hoàn thành các đầu việc được giao
- **Acceptance Criteria**:
  - [ ] **Viewer**: Có thể gọi API đọc (`GET /todos/{id}` hoặc xem danh sách shared). Nếu gửi request sửa (`PUT`) hoặc xóa (`DELETE`), hệ thống lập tức từ chối với mã lỗi HTTP 403 Forbidden (`"Viewer role does not have permission to modify this todo"`).
  - [ ] **Editor**: Có thể cập nhật trạng thái hoàn thành (`completed: true/false`), sửa tiêu đề (`title`) và mô tả (`description`). Tuy nhiên, Editor **không được phép xóa vĩnh viễn** Todo của Owner (`DELETE` chỉ dành riêng cho Owner).
  - [ ] Dữ liệu hiển thị của Collaborator luôn đồng bộ tức thì với các thay đổi từ Owner.

---

### User Story 3: Owner thay đổi quyền hoặc thu hồi quyền truy cập (Revoke Access)
- **As an** Owner
- **I want to** thay đổi quyền của collaborator (từ `viewer` sang `editor` hoặc ngược lại) hoặc bấm "Thu hồi quyền" (Revoke) bất kỳ lúc nào
- **So that** tôi kiểm soát hoàn toàn tính bảo mật dữ liệu của mình khi dự án kết thúc hoặc thay đổi nhân sự
- **Acceptance Criteria**:
  - [ ] Owner có thể cập nhật vai trò qua API `PATCH /shares/{share_id}`.
  - [ ] Owner có thể hủy quyền qua API `DELETE /shares/{share_id}`.
  - [ ] Ngay khi thu hồi quyền thành công, Collaborator bị chặn ngay lập tức ở lần gọi API tiếp theo (HTTP 403 Forbidden).
  - [ ] Toàn bộ Redis cache của cả Owner và Collaborator liên quan đến danh sách Todo dùng chung phải được **xóa ngay lập tức (instant cache invalidation)**.

---

### User Story 4: Collaborator tự rời khỏi danh sách chia sẻ
- **As a** Collaborator
- **I want to** chủ động bấm "Rời khỏi danh sách" (Leave shared list)
- **So that** danh sách của tôi không bị rác bởi những công việc tôi không còn tham gia
- **Acceptance Criteria**:
  - [ ] Collaborator có thể gọi API `DELETE /shares/leave/{share_id}` để tự hủy liên kết chia sẻ.
  - [ ] Hệ thống xác nhận `current_user.id == share.shared_with_user_id` trước khi xóa bản ghi.

---

## 3. Scope (Phạm Vi Tính Năng)

- **In-Scope (Bắt buộc trong phiên bản này)**:
  - Bảng lưu trữ liên kết chia sẻ danh sách giữa Owner và Collaborator.
  - Hai cấp độ phân quyền rõ ràng: `viewer` và `editor`.
  - Bộ API quản lý chia sẻ: Tạo lời mời, danh sách lời mời đã gửi/nhận, đổi quyền, thu hồi quyền, tự rời khỏi danh sách.
  - Middleware / Dependency kiểm tra phân quyền đa tầng trên các endpoint Todo hiện có.
  - Chiến lược xóa cache Redis đa người dùng (Multi-tenant cache invalidation).
  
- **Out-of-Scope (Để dành cho các phiên bản tương lai nhằm tránh Scope Creep)**:
  - Chia sẻ qua liên kết công khai không cần đăng nhập (Public shareable link).
  - Phân quyền chi tiết tới từng Todo con riêng lẻ (Phiên bản này chia sẻ theo toàn bộ Todo List của Owner).
  - Chat, bình luận hoặc nhắc tên (`@mention`) thời gian thực qua WebSocket.
  - Phân quyền cấp 3: Phân chia nhóm người dùng (Team/Workspace organizations).

---

## 4. Database Design (Thiết Kế Cơ Sở Dữ Liệu)

### 4.1. Bảng Mới: `todo_shares`

Lưu trữ quan hệ chia sẻ và phân quyền giữa Owner và Collaborator.

| Tên Cột | Kiểu Dữ Liệu | Ràng Buộc (Constraints) | Mô Tả |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY, DEFAULT gen_random_uuid()` | Định danh duy nhất của bản ghi chia sẻ |
| `owner_id` | `UUID` | `NOT NULL, REFERENCES users(id) ON DELETE CASCADE` | ID người sở hữu danh sách Todo |
| `shared_with_user_id` | `UUID` | `NOT NULL, REFERENCES users(id) ON DELETE CASCADE` | ID người được chia sẻ quyền |
| `role` | `VARCHAR(20)` | `NOT NULL, CHECK (role IN ('viewer', 'editor'))` | Quyền hạn được cấp (`viewer` hoặc `editor`) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT CURRENT_TIMESTAMP` | Thời điểm chia sẻ |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT CURRENT_TIMESTAMP` | Thời điểm cập nhật vai trò gần nhất |

### 4.2. Ràng Buộc & Chỉ Mục (Constraints & Indexes)

1. **Unique Constraint**:
   ```sql
   ALTER TABLE todo_shares 
   ADD CONSTRAINT uq_owner_shared_user UNIQUE (owner_id, shared_with_user_id);
   ```
   *Ý nghĩa*: Ngăn chặn tuyệt đối việc một người dùng được mời nhiều lần vào cùng một danh sách.

2. **Self-Sharing Prevention Check**:
   ```sql
   ALTER TABLE todo_shares 
   ADD CONSTRAINT chk_no_self_share CHECK (owner_id <> shared_with_user_id);
   ```
   *Ý nghĩa*: Đảm bảo tầng database ngăn chặn việc tự chia sẻ cho chính mình kể cả khi có bug từ client/API.

3. **Database Indexes**:
   - `CREATE INDEX idx_todo_shares_shared_with ON todo_shares(shared_with_user_id);`  
     *Mục đích*: Tối ưu truy vấn cực nhanh khi Collaborator đăng nhập và tải danh sách các Todo được chia sẻ với mình.
   - `CREATE INDEX idx_todo_shares_owner ON todo_shares(owner_id);`  
     *Mục đích*: Tối ưu khi Owner xem danh sách những người mình đang chia sẻ.

---

## 5. API Contracts & Endpoints

### 5.1. Danh Sách Endpoints Mới

| Method | Endpoint | Mô Tả | Yêu Cầu Auth | Phân Quyền |
| :--- | :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/shares` | Chia sẻ danh sách cho user khác bằng email | Có (Bearer) | Bất kỳ User đã login (trở thành Owner) |
| `GET` | `/api/v1/shares/outbound` | Lấy danh sách những người Owner đang chia sẻ | Có (Bearer) | Chỉ lấy bản ghi do `current_user` làm Owner |
| `GET` | `/api/v1/shares/inbound` | Lấy danh sách các Todo lists được người khác chia sẻ với mình | Có (Bearer) | Lấy bản ghi do `current_user` làm Collaborator |
| `PATCH` | `/api/v1/shares/{share_id}` | Thay đổi vai trò (`viewer` $\leftrightarrow$ `editor`) | Có (Bearer) | Chỉ Owner của bản ghi share |
| `DELETE` | `/api/v1/shares/{share_id}` | Thu hồi quyền chia sẻ (Revoke) | Có (Bearer) | Chỉ Owner của bản ghi share |
| `DELETE` | `/api/v1/shares/leave/{share_id}` | Collaborator tự rời khỏi danh sách chia sẻ | Có (Bearer) | Chỉ Collaborator của bản ghi share |

---

### 5.2. Schemas & Chi Tiết Payload

#### A. Request Body Tạo Lời Mời: `POST /api/v1/shares`
```json
{
  "email": "collab@example.com",
  "role": "editor"
}
```
*Validation (Pydantic Schema)*:
- `email`: EmailStr, bắt buộc.
- `role`: Enum `["viewer", "editor"]`, bắt buộc.

#### B. Response Khi Tạo Lời Mời Thành Công: `HTTP 201 Created`
```json
{
  "id": "7b8f9e2d-4c3a-4b1e-9f0a-123456789abc",
  "owner_id": "00000000-0000-0000-0000-000000000001",
  "shared_with_user_id": "00000000-0000-0000-0000-000000000002",
  "shared_with_email": "collab@example.com",
  "role": "editor",
  "created_at": "2026-09-16T08:30:00Z",
  "updated_at": "2026-09-16T08:30:00Z"
}
```

#### C. Error Responses Chuẩn Hóa
- **400 Bad Request**: Tự share cho chính mình
  ```json
  { "detail": "Cannot share todo list with yourself" }
  ```
- **404 Not Found**: Không tìm thấy email người nhận
  ```json
  { "detail": "User with email collab@example.com not found" }
  ```
- **409 Conflict**: Đã chia sẻ cho người này trước đó
  ```json
  { "detail": "User already has access to your todo list" }
  ```
- **403 Forbidden**: Không có quyền thao tác trên share của người khác
  ```json
  { "detail": "Not authorized to manage this sharing permission" }
  ```

---

## 6. Business Logic & Security Considerations

### 6.1. Ma Trận Phân Quyền (Authorization & Permission Matrix)

| Hành Động (Action) | Owner | Editor | Viewer | Người Lạ (Unauthorized User) |
| :--- | :---: | :---: | :---: | :---: |
| **Xem danh sách & chi tiết Todo (`GET`)** | ✅ Cho phép | ✅ Cho phép | ✅ Cho phép | ❌ Chặn (403/404) |
| **Tạo mới Todo trong danh sách (`POST`)** | ✅ Cho phép | ✅ Cho phép | ❌ Chặn (403) | ❌ Chặn (401/403) |
| **Cập nhật Todo (`PUT /todos/{id}`)** | ✅ Cho phép | ✅ Cho phép | ❌ Chặn (403) | ❌ Chặn (403) |
| **Xóa vĩnh viễn Todo (`DELETE /todos/{id}`)** | ✅ Cho phép | ❌ Chặn (403) | ❌ Chặn (403) | ❌ Chặn (403) |
| **Thêm / Đổi quyền / Thu hồi Share** | ✅ Cho phép | ❌ Chặn (403) | ❌ Chặn (403) | ❌ Chặn (403) |
| **Tự rời khỏi danh sách shared** | — | ✅ Cho phép | ✅ Cho phép | ❌ Chặn (403) |

> **Nguyên tắc then chốt**: Collaborator có quyền `editor` chỉ được phép tạo và sửa tiến độ, **không có quyền xóa** Todo của Owner để ngăn ngừa hành vi phá hoại dữ liệu (Data destruction prevention).

---

### 6.2. Xử Lý Các Trường Hợp Biên & Tranh Chấp Dữ Liệu (Edge Cases & Race Conditions)

1. **User tự chia sẻ cho chính mình (Self-Sharing)**:
   - Xử lý 2 lớp: Tầng API kiểm tra `if target_user.id == current_user.id: raise HTTPException(400)` và tầng Database bảo vệ bằng `CHECK (owner_id <> shared_with_user_id)`.
2. **Mời trùng lặp hoặc gửi lời mời liên tục (Duplicate Invites / Double Submit)**:
   - Cơ sở dữ liệu bắt ngoại lệ `IntegrityError` từ ràng buộc `UNIQUE (owner_id, shared_with_user_id)` và trả về mã HTTP `409 Conflict`.
3. **Owner thu hồi quyền trong lúc Collaborator đang bấm Lưu (Race Condition Revocation)**:
   - Mọi request `PUT /todos/{id}` luôn kiểm tra quyền trực tiếp tại thời điểm thực thi trong Database Transaction (`SELECT role FROM todo_shares WHERE ...`).
   - Nếu bản ghi share đã bị xóa trước đó vài mili-giây, giao dịch bị từ chối ngay lập tức với mã `403 Forbidden`, ngăn chặn hoàn toàn việc ghi đè dữ liệu sau khi đã bị tước quyền.
4. **Quyền chia sẻ thứ cấp (Cascading Shares Prevention)**:
   - Collaborator **không được phép** chia sẻ danh sách của Owner cho bên thứ ba (User C). Hệ thống chỉ cho phép chính chủ nhân thực sự (`todo.user_id == current_user.id`) được quyền gọi API chia sẻ.
5. **Xóa tài khoản Owner (Cascade Cleanup)**:
   - Nhờ ràng buộc `ON DELETE CASCADE`, khi tài khoản Owner bị xóa, toàn bộ các Todo và các bản ghi `todo_shares` liên kết sẽ tự động được dọn sạch khỏi cơ sở dữ liệu.

---

## 7. Caching & Invalidation Strategy (Chiến Lược Cache Redis)

### 7.1. Cấu Trúc Cache Key
Để hỗ trợ việc chia sẻ danh sách Todo mà không gây rò rỉ dữ liệu giữa các người dùng trong Redis:
- **Cache cá nhân của Owner**:
  ```
  todos:list:{owner_id}:mine:page:{page}:size:{size}
  ```
- **Cache các danh sách được chia sẻ với Collaborator**:
  ```
  todos:list:{collaborator_id}:shared:owner:{owner_id}:page:{page}:size:{size}
  ```
- **Cache quyền hạn của Collaborator (Quyền truy cập nhanh)**:
  ```
  share:permission:{owner_id}:{collaborator_id}  (Giá trị: "viewer" hoặc "editor", TTL = 300s)
  ```

### 7.2. Kịch Bản Xóa Cache (Cache Invalidation Triggers)

| Sự Kiện Nghiệp Vụ | Thao Tác Xóa Cache Redis Cần Thực Hiện |
| :--- | :--- |
| **Owner cập nhật / tạo mới Todo** | 1. Xóa `todos:list:{owner_id}:*`<br>2. Duyệt tìm danh sách Collaborators của Owner và xóa toàn bộ `todos:list:{collab_id}:shared:owner:{owner_id}:*` |
| **Editor cập nhật Todo** | 1. Xóa cache của Owner: `todos:list:{owner_id}:*`<br>2. Xóa cache của chính Editor: `todos:list:{editor_id}:*`<br>3. Xóa cache của các Collaborators khác cùng xem danh sách này |
| **Owner thu hồi quyền (Revoke Access)** | 1. Xóa key phân quyền: `share:permission:{owner_id}:{collab_id}`<br>2. Xóa cache danh sách của Collaborator: `todos:list:{collab_id}:shared:owner:{owner_id}:*` |
| **Owner thay đổi Role (`viewer` $\leftrightarrow$ `editor`)** | 1. Cập nhật / Xóa key `share:permission:{owner_id}:{collab_id}` để ép kiểm tra lại quyền ngay lập tức |

---
*Tài liệu đặc tả này đã sẵn sàng để chuyển giao cho đội ngũ phát triển triển khai mã nguồn và kiểm thử tự động.*
