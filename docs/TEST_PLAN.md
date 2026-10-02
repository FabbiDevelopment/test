# Manual Test Plan: Authentication, Authorization & Todo Regression

## 1. Scope & Objective

- Kiểm tra Authentication, Authorization và cách ly dữ liệu giữa các user.
- Kiểm tra hồi quy Todo CRUD, partial update, toggle và cache sau các bản sửa.

## 2. Test Environment & Prerequisites

- Ngày kiểm tra: **2026-10-02**; commit `1e4c5c4` cùng thay đổi Tier 2B và bản sửa login trong working tree. TC-04 được chạy lại sau bản sửa; các case khác giữ kết quả lượt kiểm tra trước.
- Backend: `http://localhost:8000`; Frontend: `http://localhost:3000`; PostgreSQL và Redis thật qua Docker Compose.
- Hai tài khoản test đã tạo: `manual-a-1790925635737@example.com` (A), `manual-b-1790925635737@example.com` (B); password: `ManualPassword123!`.
- A tạo todo X, B tạo todo Y, mỗi todo có title/description riêng. Các request API dùng Bearer token của user tương ứng; đường dẫn trong bảng có prefix `/api/v1`.
- Đã thao tác UI trên hai phiên trình duyệt độc lập và gọi API thật. Case token hết hạn/response chậm dùng proxy test tạm tại frontend `3001`, API `8002` để kiểm soát điều kiện.

**Chạy lại TC-06:** Login A trong Swagger `/docs`, dùng access token gọi `/auth/me` lấy `id`. Từ thư mục repo, thay `<USER_ID_A>` bằng ID đó để tạo token hết hạn có chữ ký đúng:

```powershell
docker compose exec backend python -c "from datetime import timedelta; from app.core.security import create_access_token; print(create_access_token({'sub': '<USER_ID_A>'}, expires_delta=timedelta(seconds=-1)))"
```

Dùng token vừa tạo trong Swagger Authorize, gọi `/auth/me` và `/todos`: cả hai phải trả 401. Trên tab UI của A, mở DevTools → Application → Local Storage → `http://localhost:3000`, thay giá trị `access_token` bằng token đó rồi reload: phải về `/login`.

**Chạy lại TC-21:** A mở list → Logout → login B trong cùng tab, không reload; xác nhận email/todo B và không có dữ liệu A. Với nhánh 401 trả muộn, từ `frontend/` chạy helper có sẵn:

```powershell
npx playwright test --project=session-cache --grep "401: true" --debug
```

Trong Playwright Inspector dùng Step over theo các bước của `e2e/session-isolation.spec.ts`: giữ PUT của A → logout A → login B → `state.releaseUpdate()` thả response 401. Quan sát UI trước/sau response: phải giữ phiên và dữ liệu B. Nhánh này mock API để kiểm tra FE; lượt manual ghi trong bảng đã dùng proxy với backend thật.

## 3. Test Cases Matrix

Priority: **High / Medium**. Severity: **Critical / High / Medium**, biểu thị tác động nếu case không đạt.

| TC ID | Module / Feature | Test Scenario | Preconditions | Test Steps | Expected Result | Actual Result | Priority / Severity | Status (Pass/Fail) |
|---|---|---|---|---|---|---|---|---|
| TC-01 | Auth | Register thành công | Email mới | Nhập email/password/confirm hợp lệ; Create Account | 201; vào Todo page, đúng email, list rỗng | A/B đăng ký thành công; UI đúng email và list rỗng | High / High | Pass |
| TC-02 | Auth | Register email trùng | A đã tồn tại | Register lại email A | 400; báo email đã đăng ký | API 400; UI báo `Email already registered`, vẫn ở Register | Medium / Medium | Pass |
| TC-03 | Auth | Login thành công | A đã đăng ký | Logout; login bằng thông tin A | 200; vào Todo page của A | API 200; UI hiển thị email và todo A | High / High | Pass |
| TC-04 | Auth | Login lỗi không tiết lộ tài khoản | Có email A và email chưa tồn tại | POST /auth/login từng email với cùng password sai; so sánh lỗi | Cùng 401 và thông báo chung | Sau sửa BE, API Docker thật trả cùng 401 và `Invalid email or password`; login đúng vẫn 200 | Medium / Medium | Pass |
| TC-05 | Auth | Truy cập không token | Đã logout | GET /todos không token; mở UI `/` | API từ chối, không trả dữ liệu; UI về Login | API 403; UI chuyển `/login` | High / High | Pass |
| TC-06 | Auth | Token hết hạn | Access token có chữ ký đúng, exp đã qua | GET /auth/me và /todos; UI login nhận token hết hạn qua proxy | API 401; UI về Login | Hai API trả 401; UI chuyển `/login` khi profile trả 401 | High / High | Pass |
| TC-07 | Auth | Token sai chữ ký | Có access token A | Sửa ký tự đầu phần chữ ký; GET /auth/me | 401, không trả profile | API 401 | High / High | Pass |
| TC-08 | Auth | Refresh token không thay access token | Có refresh token A | Dùng refresh token làm Bearer; GET /auth/me | 401 | API 401 | High / High | Pass |
| TC-09 | Auth | Logout và bảo vệ route | A đang login | Logout; mở lại `/` | Về Login; không hiện dữ liệu riêng | UI về `/login`; mở `/` vẫn bị chuyển về Login | High / High | Pass |
| TC-10 | Auth | Validation đăng ký | Chưa login | Register email sai; thử confirm password khác; gửi email sai qua API | UI chặn dữ liệu lỗi; API 422 | Browser chặn email sai; UI báo `Passwords don't match`; API 422 | Medium / Medium | Pass |
| TC-11 | Authorization | Hai phiên user độc lập | A có X, B có Y | A prime cache; B đọc list; reload cả hai phiên | Mỗi user chỉ thấy todo và email của mình | UI/API đều chỉ trả dữ liệu của đúng user, kể cả sau reload | High / Critical | Pass |
| TC-12 | Authorization | User khác không đọc được todo | X thuộc A | B GET /todos/X; A GET X | B 404; A 200 | B 404 `Todo not found`; A 200 | High / Critical | Pass |
| TC-13 | Authorization | User khác không sửa được todo | Có snapshot X của A | B PUT X; A GET và so sánh toàn bộ dữ liệu | B 404; X không đổi | B 404; snapshot X giữ nguyên, gồm user_id và updated_at | High / Critical | Pass |
| TC-14 | Authorization | User khác không xóa được todo | X thuộc A | B DELETE X; A GET X | B 404; X còn nguyên | B 404; A GET 200 với snapshot không đổi | High / Critical | Pass |
| TC-15 | Authorization | Todo không tồn tại | UUID mới, token hợp lệ | GET/PUT/DELETE UUID mới; so lỗi với truy cập chéo user | Cùng 404, không tiết lộ chủ sở hữu | Cả ba 404; payload giống lỗi truy cập chéo user | High / High | Pass |
| TC-16 | Todo | Tạo todo | A đang login | Add Todo với title/description; reload; GET theo ID | 201; thuộc A; completed=false; nội dung đúng | UI/API lưu đúng nội dung, owner và completed=false | High / High | Pass |
| TC-17 | Todo | Toggle cả hai chiều | X chưa hoàn thành, có description | Tích; reload; bỏ tích; reload; đợi từng PUT xong | Lưu true rồi false; giữ description | UI/API đúng sau mỗi reload; description giữ nguyên | High / High | Pass |
| TC-18 | Todo | Partial update description | X có description | PUT chỉ title; GET; sau đó PUT description=null | Bỏ qua giữ description; null xóa có chủ đích | API giữ description khi chỉ sửa title, xóa khi gửi null; UI sửa title cũng giữ description | High / High | Pass |
| TC-19 | Todo | Xóa todo của mình | List đã được cache | Xóa bằng UI; reload; GET todo và list | DELETE 204; GET 404; list không còn todo | UI rỗng sau reload; GET X/Y 404, total=0; DELETE API cũng trả 204 trong lượt cache test | High / High | Pass |
| TC-20 | Cache | Invalidation và phân trang | A có X; B có Y | Prime page/size: 1/1, 1/2, 2/1; A create/update/delete; đọc lại từng query và list B | Metadata đúng; cache A cập nhật ngay; B không bị ảnh hưởng | Ba query phản ánh từng mutation và total mới; list B giữ dữ liệu riêng, không chờ TTL | High / High | Pass |
| TC-21 | Session | Đổi tài khoản cùng tab | A/B có todo riêng | A logout rồi login B, không reload; lặp lại với PUT A pending rồi trả 401 muộn | B chỉ thấy dữ liệu B; response A không đổi hoặc logout B | Cùng tab hiển thị B; 401 muộn của A không làm mất phiên B | High / Critical | Pass |

## 4. Defect Tracking & Known Limitations

Kết quả trong phạm vi test plan: **21 case đã chạy — 21 Pass**.

- TC-04 đã sửa và kiểm tra lại trên API Docker thật; bộ test auth có **8 Pass**, gồm regression cho hai nhánh login lỗi.
- Logout chỉ kết thúc phiên client; access token cũ vẫn được API chấp nhận đến khi hết hạn. TC-09 không đánh giá revoke JWT.
- Đã xóa todo test, logout các phiên và dừng proxy; tài khoản test còn trong DB vì chưa có API xóa account.
