# Manual Test Plan — Authentication and Todo Authorization

## 1. Scope and objective

Kế hoạch này xác minh các luồng xác thực, phân quyền và cô lập dữ liệu Todo giữa các tài khoản. Mục tiêu là bảo đảm người dùng có thể đăng ký, đăng nhập và đăng xuất an toàn; đồng thời chỉ có thể xem hoặc thay đổi Todo thuộc sở hữu của mình.

## 2. Test environment

- Frontend URL: `http://localhost:3000`
- Backend URL: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Browser: Chrome phiên bản ổn định mới nhất
- Database và Redis phải được khởi động và ở trạng thái healthy.

## 3. General preconditions

1. Chạy ứng dụng bằng `docker compose up --build`.
2. Xác nhận frontend mở được tại `http://localhost:3000`.
3. Xác nhận `GET http://localhost:8000/health` trả về HTTP 200.
4. Chuẩn bị hai email chưa được sử dụng cho User A và User B.
5. Dùng cửa sổ ẩn danh hoặc browser profile riêng khi kiểm tra hai session.
6. Xóa dữ liệu test cũ nếu email hoặc tên Todo có thể gây trùng lặp.

## 4. Authentication test cases

### AUTH-01 — Register with valid information

- Preconditions: Email test chưa tồn tại trong hệ thống.
- Test steps:
  1. Mở trang `/register`.
  2. Nhập email hợp lệ.
  3. Nhập password dài ít nhất 6 ký tự và confirm password giống nhau.
  4. Nhấn **Create Account**.
- Expected result:
  - Tài khoản được tạo thành công.
  - Người dùng được chuyển đến trang Todo.
  - Email của người dùng được hiển thị trên header.
- Actual result: Chưa chạy.
- Severity: Major
- Priority: High
- Status: Not Run

### AUTH-02 — Login with valid credentials

- Preconditions: Tài khoản test đã được đăng ký và người dùng đang ở trạng thái logout.
- Test steps:
  1. Mở trang `/login`.
  2. Nhập đúng email và password.
  3. Nhấn **Sign In**.
- Expected result:
  - Đăng nhập thành công.
  - Người dùng được chuyển đến trang Todo.
  - Chỉ danh sách Todo của tài khoản hiện tại được hiển thị.
- Actual result: Chưa chạy.
- Severity: Major
- Priority: High
- Status: Not Run

### AUTH-03 — Reject an incorrect password

- Preconditions: Tài khoản test đã tồn tại.
- Test steps:
  1. Mở trang `/login`.
  2. Nhập đúng email nhưng nhập sai password.
  3. Nhấn **Sign In**.
- Expected result:
  - Đăng nhập bị từ chối.
  - Giao diện hiển thị thông báo lỗi chung, không tiết lộ email có tồn tại hay không.
  - Người dùng vẫn ở trang login và không nhận được access token.
- Actual result: Chưa chạy.
- Severity: Major
- Priority: High
- Status: Not Run

### AUTH-04 — Reject an expired or tampered access token

- Preconditions: Có access token hợp lệ của một tài khoản test và có thể gửi request bằng API client.
- Test steps:
  1. Gửi `GET /api/v1/auth/me` với access token đã hết hạn.
  2. Thay đổi một ký tự trong chữ ký của token hợp lệ.
  3. Gửi lại `GET /api/v1/auth/me` với token đã bị thay đổi.
- Expected result:
  - Cả hai request đều trả HTTP 401.
  - Không có dữ liệu người dùng được trả về.
- Actual result: Chưa chạy.
- Severity: Critical
- Priority: High
- Status: Not Run

### AUTH-05 — Logout removes access to protected pages

- Preconditions: Người dùng đã đăng nhập.
- Test steps:
  1. Nhấn **Logout**.
  2. Xác nhận trình duyệt chuyển đến `/login`.
  3. Nhập trực tiếp URL `/` trên thanh địa chỉ.
- Expected result:
  - Access token và refresh token bị xóa khỏi local storage.
  - Người dùng không thể mở trang Todo và được chuyển về `/login`.
- Actual result: Chưa chạy.
- Severity: Major
- Priority: High
- Status: Not Run

## 5. Authorization test cases

### AUTHZ-01 — User B cannot list User A's Todo

- Preconditions:
  - User A và User B là hai tài khoản khác nhau.
  - User A đã tạo Todo có title duy nhất `Private Todo A`.
- Test steps:
  1. Đăng xuất User A.
  2. Mở một browser session khác và đăng nhập bằng User B.
  3. Kiểm tra toàn bộ danh sách Todo của User B.
  4. Reload trang và kiểm tra lại.
- Expected result:
  - `Private Todo A` không xuất hiện trong session của User B trước hoặc sau reload.
  - Todo vẫn xuất hiện khi đăng nhập lại bằng User A.
- Actual result: Chưa chạy.
- Severity: Critical
- Priority: High
- Status: Not Run

### AUTHZ-02 — User B cannot read User A's Todo by ID

- Preconditions: User A đã tạo Todo và tester đã ghi lại Todo ID.
- Test steps:
  1. Đăng nhập API client bằng User B.
  2. Gửi `GET /api/v1/todos/{todo_id}` với ID Todo của User A.
- Expected result:
  - API trả HTTP 404 để không tiết lộ tài nguyên của tài khoản khác.
  - Response không chứa nội dung Todo của User A.
- Actual result: Chưa chạy.
- Severity: Critical
- Priority: High
- Status: Not Run

### AUTHZ-03 — User B cannot update User A's Todo

- Preconditions: User A đã tạo Todo và tester đã ghi lại Todo ID cùng nội dung ban đầu.
- Test steps:
  1. Đăng nhập API client bằng User B.
  2. Gửi `PUT /api/v1/todos/{todo_id}` với title mới.
  3. Đăng nhập lại bằng User A và đọc Todo đó.
- Expected result:
  - Request update của User B trả HTTP 404.
  - Title và description của Todo không bị thay đổi.
- Actual result: Chưa chạy.
- Severity: Critical
- Priority: High
- Status: Not Run

### AUTHZ-04 — User B cannot delete User A's Todo

- Preconditions: User A đã tạo Todo và tester đã ghi lại Todo ID.
- Test steps:
  1. Đăng nhập API client bằng User B.
  2. Gửi `DELETE /api/v1/todos/{todo_id}` với ID Todo của User A.
  3. Đăng nhập lại bằng User A và đọc Todo đó.
- Expected result:
  - Request delete của User B trả HTTP 404.
  - User A vẫn đọc được Todo và dữ liệu không bị mất.
- Actual result: Chưa chạy.
- Severity: Critical
- Priority: High
- Status: Not Run

## 6. Todo regression test cases

### TODO-01 — Persist completed state after reload

- Preconditions: Người dùng đã đăng nhập và có một Todo chưa hoàn thành.
- Test steps:
  1. Chọn checkbox để đánh dấu Todo hoàn thành.
  2. Reload trang.
  3. Quan sát title và checkbox của Todo.
- Expected result:
  - Todo vẫn xuất hiện đúng title.
  - Checkbox vẫn ở trạng thái checked sau reload.
- Actual result: Chưa chạy.
- Severity: Major
- Priority: High
- Status: Not Run

### TODO-02 — Partial title update preserves description

- Preconditions: Có một Todo chứa cả title và description.
- Test steps:
  1. Chỉ sửa title của Todo và lưu.
  2. Reload trang.
  3. Kiểm tra lại title và description.
- Expected result:
  - Title được cập nhật.
  - Description cũ vẫn được giữ nguyên.
- Actual result: Chưa chạy.
- Severity: Major
- Priority: Medium
- Status: Not Run

## 7. Severity and priority definitions

### Severity

- Critical: Rò rỉ dữ liệu, vượt quyền hoặc mất dữ liệu giữa các tài khoản.
- Major: Chức năng chính không hoạt động hoặc trạng thái không được lưu chính xác.
- Minor: Lỗi không chặn luồng chính và có giải pháp tạm thời.

### Priority

- High: Phải sửa trước khi release.
- Medium: Nên sửa trong iteration hiện tại.
- Low: Có thể lên kế hoạch cho iteration sau.

## 8. Execution summary

| Total | Passed | Failed | Blocked | Not Run |
|---:|---:|---:|---:|---:|
| 11 | 0 | 0 | 0 | 11 |

Sau khi thực hiện manual test, cập nhật **Actual result**, **Status** và bảng tổng kết. Không đánh dấu Pass nếu trường hợp kiểm thử chưa được chạy thực tế.
