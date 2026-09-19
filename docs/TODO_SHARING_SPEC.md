# Technical Specification: Todo Sharing

> Requirement Analysis & Spec Writing for the Todo Sharing feature.

## 1. Overview & Objective
- **Feature Summary**: Cho phép người dùng (Owner) chia sẻ todo list hoặc todo cụ thể với người dùng khác, với quyền xem (viewer) hoặc chỉnh sửa (editor). Owner có thể thay đổi quyền hoặc thu hồi quyền bất cứ lúc nào đối với viewer hoặc editor 
- **Problem Statement**: Hiện tại, hệ thống Todo đang vận hành theo kiến trúc độc lập, chưa hỗ trợ cơ chế tương tác, chia sẻ hoặc ủy quyền công việc giữa các tài khoản. Việc nâng cấp tính năng Collaborative Sharing kết hợp phân quyền sẽ giải quyết bài toán làm việc nhóm, đồng thời đảm bảo tính bảo mật và an toàn dữ liệu

- **Target Audience / Roles**:
  - Owner: Người tạo Todo ban đầu, có toàn quyền quản trị và chia sẻ.
  - Viewer: người được chia sẻ với quyền chỉ được xem
  - Editor: người được chia sẻ với quyền có thể xem và chỉnh sửa
  - Admin/System: hỗ trợ giám sát quyền và kiểm tra log hoạt động nếu cần

## 2. User Stories & Acceptance Criteria
### User Story 1: Owner shares a todo list with another user
- Owner
- Chia sê các danh sách công việc tới 1 user khác với các quyền lựa chọn (viewer) hoặc (Editor)
- Họ có thể làm các việc mà được phân quyền rõ ràng từng cấp độ mà không sợ lộ tài khoản của Owner
- **Acceptance Criteria**:
  - Owner có thể chọn một user khác làm recipient.
  - Owner có thể chọn quyền `viewer` hoặc `editor`.
  - Hệ thống sẽ chăn từ chối share cho chính mình.
  - Sau khi share thành công, recipient có thể thấy todo list theo đúng quyền.
  - Một share đang hoạt động không được tạo trùng lặp cho cùng `todo_id` và `user_id`.

### User Story 2: Viewer chỉ có quyền đọc các công việc được chia sẻ theo cấp độ
- Viewer
- Có quyền xem danh sách công việc được chia sẻ và kiểm tra các đầu việc mà không làm thay đổi dữ liệu 
- Có thể theo dõi tiến độ công việc mà không gây ra các chỉnh sửa nào khác
- **Acceptance Criteria**:
  - Người xem có thể lấy danh sách (list) và xem chi tiết các công việc được chia sẻ
  - không thể tạo mới (create), cập nhật (update), xóa (delete), hoặc thay đổi trạng thái hoàn thành (toggle status) của các công việc không thuộc quyền chỉnh sửa của mình
  - Nếu người xem cố tình gửi yêu cầu cập nhật hoặc xóa lên hệ thống, backend phải từ chối và trả về mã lỗi 403 Forbidden kèm thông báo lỗi rõ ràng.

### User Story 3: Editor có thể thay đổi các công việc được chia sẻ
- Editor
- Cập nhật các công việc được chia sẻ và tạo thêm các tác vụ mới trong danh sách được phép
- Đóng góp vào tiến độ công việc chung mà không cần phải là chủ sở hữu của danh sách đó
- **Acceptance Criteria**:
  - Người chỉnh sửa có thể tạo mới công việc bên trong danh sách được chia sẻ của từng phân quyền 
  - Người chỉnh sửa có thể cập nhật tiêu đề, mô tả và trạng thái hoàn thành
  - Người chỉnh sửa không thể thay đổi quyền chia sẻ của Owner và không được phép xóa toàn bộ danh sách công việc trừ khi được cấp quyền tương ứng
  - Hệ thống phải có ghi nhận các thay đổi

### User Story 4: Owner người quản trị cao nhất có thể thu hồi quyền bất kỳ lúc nào với các người dùng cấp dưới được share
- Owner
- Thu hồi quyền truy cập của một người dùng khác ngay lập tức
- Họ không còn quyền nhìn thấy hoặc chỉnh sửa danh sách công việc
- **Acceptance Criteria**:
  - Chủ sở hữu có thể thực hiện lệnh thu hồi (revoke) quyền hạn của người nhận ngay lập tức
  - Ngay sau khi thu hồi, người nhận sẽ không còn thấy danh sách công việc đó xuất hiện trong danh mục được quyền truy cập của họ nữa
  - Nếu người nhận đang thực hiện thao tác ngay tại thời điểm bị thu hồi quyền, các request tiếp theo gửi lên hệ thống phải bị chặn và từ chối ngay lập tức
  - Hệ thống phải tiến hành xóa bỏ bộ nhớ đệm liên quan (invalidate cache) ngay lập tức để tránh tình trạng dữ liệu cũ bị lưu giữ

## 3. Scope
- **In-Scope**:
 - Quản lý chia sẻ: Chia sẻ danh sách công việc (todo list) đích danh theo từng người dùng (user) gắn kèm quyền hạn (permission) tương ứng
 - Thao tác dữ liệu: Cho phép tạo mới, cập nhật hoặc xóa bỏ các bản ghi chia sẻ trong cơ sở dữ liệu
 - Phân cấp quyền hạn: Phân định rõ ràng và xử lý logic độc lập giữa hai nhóm quyền: quyền xem (viewer) và quyền chỉnh sửa (editor)
 - Thu hồi quyền: Cơ chế hủy bỏ quyền truy cập của người nhận ngay tức thì khi có yêu cầu từ Owner
 - Xác thực tại tầng API: Thực hiện kiểm tra quyền sở hữu (ownership) và phân quyền hệ thống (authorization) ngay tại lớp API (API Layer) trước khi xử lý logic
 - Vô hiệu hóa bộ nhớ đệm: Tự động xóa hoặc cập nhật lại bộ nhớ đệm (cache) ngay khi có bất kỳ thay đổi nào về quyền hạn hoặc dữ liệu để tránh dữ liệu bị sai lệch
 - Nhật ký: Ghi vết lịch sử hệ thống đối với các thao tác liên quan đến chia sẻ công việc (ai share, share cho ai, khi nào thu hồi) để phục vụ kiểm tra dữ liệu.
- **Out-of-Scope**:
  - Chia sẻ công khai bằng link không xác thực
  - Tạo nhóm share / team-level permissions
  - Quản lý thiết lập thời gian hết hạn
  - Không hỗ trợ tính năng chia sẻ danh sách công việc cho nhiều người dùng cùng một lúc
  - Không hỗ trợ các tính năng tích hợp hoặc chia sẻ dữ liệu công khai ra các nền tảng

## 4. Database Design
- **New Tables / Altered Tables**:

  ### `todo_shares`
  | Column          | Type              | Constraints                       | Notes |
 --------------------------------------------------------------------------------------------
  | `id`            | UUID              | PK                                | Unique share record id |
  | `todo_id`       | UUID              | FK -> `todos.id`, NOT NULL        | Todo được chia sẻ |
  | `owner_id`      | UUID              | FK -> `users.id`, NOT NULL        | Người quản trị cao nhất |
  | `shared_with_user_id`| UUID         | FK -> `users.id`, NOT NULL        | Người nhận quyền |
  | `permission`    | VARCHAR(20)       | CHECK (`viewer`, `editor`), NOT NULL | Quyền truy cập |
  | `created_at`    | TIMESTAMPTZ       | NOT NULL                          | Thời gian share |
  | `updated_at`    | TIMESTAMPTZ       | NOT NULL                          | Cập nhật lần cuối |
  | `revoked_at`    | TIMESTAMPTZ       | NULLABLE                          | Nếu quyền bị thu hồi |

  - Business rule: đổi quyền của share sẽ update `permission` và `updated_at`
  - Một user chỉ được nhận một quyền active cho cùng todo:
    - Unique index: `UNIQUE (todo_id, shared_with_user_id) WHERE revoked_at IS NULL`
  - Optional: `CHECK (shared_with_user_id <> owner_id)` to prevent self-share

  ### `todos` (modified)
  - `owner_id` remains the authoritative owner
  - No direct change in core todo schema unless a `visibility` or `shared` flag is required for UI optimization

- **Constraints & Indexes**:
  - Foreign keys:
    - `todo_shares.todo_id` -> `todos.id` on delete `CASCADE`
    - `todo_shares.owner_id` -> `users.id` on delete `RESTRICT` or `CASCADE` depending product policy
    - `todo_shares.shared_with_user_id` -> `users.id` on delete `CASCADE`
  - Indexes:
    - `idx_todo_shares_todo_id` on `todo_id`
    - `idx_todo_shares_shared_with_user_id` on `shared_with_user_id`
    - `idx_todo_shares_owner_id_permission` on `(owner_id, permission)`
    - `idx_todos_owner_id_created_at` on `(owner_id, created_at DESC)`
    - `idx_todos_user_id_completed_created_at` on `(user_id, completed, created_at DESC)` for regular todo filtering and performance

## 5. API Contracts & Endpoints
| Method  | Endpoint                      Description                            | Auth Required |
-------------------------------------------------------------------------------------------
| GET     | `/api/v1/todos/{todo_id}/shares` | List all active shares for a todo | Yes |
| POST    | `/api/v1/todos/{todo_id}/shares` | Share a todo with another user | Yes |
| PATCH   | `/api/v1/todos/{todo_id}/shares/{share_id}` | Update permission or reactivate a revoked share | Yes |
| DELETE  | `/api/v1/todos/{todo_id}/shares/{share_id}` | Revoke a share | Yes |
| GET      `/api/v1/todos/shared` | List todos visible to the current user due to share | Yes |

## 6. Business Logic & Security Considerations
- **Authorization & Permission Matrix**:
  - Owner: toàn quyền đối với danh sách trong apptodo và tất cả các dữ liệu chia sẻ tới các user khác
  - Editor: Có quyền đọc/ghi (read/write) trên các công việc được chia sẻ; tuyệt đối không thể quản lý hoặc chỉnh sửa quyền hạn của người khác
  - Viewer: Chỉ có quyền xem, không thể thực hiện các thao tác cập nhật hoặc xóa bỏ các công việc được chia sẻ.
  
- **Edge Cases & Race Conditions**:
  - Mời trùng lặp: Nếu một bản ghi chia sẻ đã tồn tại trong hệ thống, backend sẽ từ chối và trả về mã lỗi
  - Khi đang gửi request mà user bị owner thu hồi quyền. Backend phải kiểm tra quyền tại thời điểm xử lý request. Nếu quyền đã bị thu hồi trước khi request được xử lý, request trả 403 Forbidden và không cập nhật dữ liệu. Nếu request đã được xác thực và cập nhật thành công trước khi revoke được xử lý, thay đổi đó được giữ lại; các request tiếp theo của Collaborator sẽ bị từ chối. Việc revoke phải xóa quyền trong DB và invalidate Redis cache ngay lập tức
  - Nếu User tự share cho chính mình? Nếu shared_with_user_id trùng với current_user_id, phía backend sẽ kiểm tra và ném ra 1 mã lỗi

## 7. Caching & Invalidation Strategy
 - Cấu trúc Redis cache key khi áp dụng quyền truy cập: Để đảm bảo quyền truy cập được lưu riêng cho từng User, tránh việc các User dùng chung cache quyền của nhau
 - Khi nào cần invalidate cache (Owner update, Collaborator update, Owner revoke quyền): Khi Cache cần được invalidate khi dữ liệu hoặc quyền truy cập thay đổi. Khi Owner hoặc Collaborator cập nhật, cache dữ liệu Todo liên quan phải được invalidate. Khi Owner revoke quyền của Collaborator, cache quyền và cache Todo của Collaborator phải được invalidate ngay lập tức để đảm bảo request tiếp theo sử dụng quyền mới nhất

