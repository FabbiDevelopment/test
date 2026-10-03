# Kế Hoạch Triển Khai Tier 1: Bug Hunting & Fixes

Dựa trên yêu cầu của `README.md`, Tier 1 yêu cầu tìm và sửa các lỗi cố ý trong mã nguồn liên quan đến xác thực (authentication), logic nghiệp vụ (business logic), bộ nhớ đệm (caching), và quản lý trạng thái (state management).

## Mục Tiêu Cụ Thể
1. **Tìm và báo cáo** các lỗi nghiêm trọng theo định dạng: Location, Severity, Reason, Fix Proposal.
2. **Sửa ít nhất 5 lỗi ý nghĩa**, trong đó bao gồm:
   - Ít nhất **2 lỗi Backend**.
   - Ít nhất **1 lỗi Frontend**.
3. Tập trung vào tính đúng đắn (correctness), phân quyền (authorization), và cách ly dữ liệu (data isolation).

## Các Bước Triển Khai

### Bước 1: Rà soát & Xác định Lỗi (Bug Hunting)
Chúng ta sẽ rà soát các khu vực có rủi ro cao để tìm lỗi:
- **Backend - Authentication & Authorization**:
  - Kiểm tra logic xác thực JWT (có kiểm tra token hết hạn không? secret key có an toàn không?).
  - Kiểm tra logic phân quyền ở các endpoint `/todos` (User A có thể xem, sửa, xoá Todo của User B không?).
- **Backend - Business Logic & Caching**:
  - Kiểm tra xem Redis cache có được xóa/cập nhật đúng cách khi một Todo được tạo, sửa, hoặc xoá không.
  - Cập nhật trường boolean `completed` có hoạt động đúng không.
- **Frontend - State Management**:
  - Kiểm tra việc cập nhật trạng thái UI sau khi gọi API (ví dụ: state có đồng bộ với database sau khi toggle trạng thái Todo không).
  - Kiểm tra React Query cache có được invalidate đúng cách sau khi mutation không.

### Bước 2: Lập danh sách các lỗi và Đề xuất sửa chữa (Drafting PR Report)
Tạo một tài liệu để ghi chép lại các lỗi tìm được theo đúng cấu trúc yêu cầu:
- **Location**: ...
- **Severity**: Critical / High / Medium / Low
- **Reason**: ...
- **Fix Proposal**: ...

### Bước 3: Sửa lỗi (Implementation)
- Lựa chọn 5 lỗi nổi bật nhất (đảm bảo điều kiện 2 BE, 1 FE).
- Tiến hành sửa đổi mã nguồn.
- Đảm bảo các commit tuân thủ theo `Conventional Commits` như hướng dẫn (ví dụ: `fix(auth): ...`).

### Bước 4: Kiểm thử (Verification)
- Kiểm tra lại thủ công hoặc chạy thử ứng dụng để đảm bảo các lỗi đã được xử lý triệt để và không gây ra side effect.
