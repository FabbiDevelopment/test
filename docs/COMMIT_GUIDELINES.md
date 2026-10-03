# Hướng dẫn Quy tắc Commit

Để đảm bảo lịch sử mã nguồn rõ ràng và chuyên nghiệp, dự án này áp dụng tiêu chuẩn **Conventional Commits**. Mọi commit đều phải tuân thủ các quy tắc dưới đây.

## 1. Cấu trúc của một Commit Message

Mỗi commit message cần tuân theo định dạng sau:

```
<loại>(<phạm vi>): <mô tả ngắn gọn>

[tùy chọn: phần thân giải thích chi tiết hơn]
```

### Các thành phần:
- **Loại (Type):** Bắt buộc. Phân loại mục đích của commit.
- **Phạm vi (Scope):** Tùy chọn. Cho biết phần code nào bị ảnh hưởng (ví dụ: `auth`, `todo`, `ui`).
- **Mô tả (Subject):** Bắt buộc. Viết bằng tiếng Anh (hoặc tiếng Việt tùy quy định team), mô tả ngắn gọn thay đổi (thường không viết hoa chữ cái đầu và không có dấu chấm ở cuối).

## 2. Các Loại Commit (Types) Được Cho Phép

- `fix`: Vá một lỗi (bug fix).
- `feat`: Thêm một tính năng mới (new feature).
- `test`: Thêm hoặc sửa các bài kiểm thử (tests) hiện có.
- `docs`: Cập nhật tài liệu (ví dụ: thay đổi README, viết docs).
- `refactor`: Sửa đổi mã nguồn mà không sửa lỗi hay thêm tính năng (ví dụ: đổi tên biến, chia nhỏ hàm).
- `chore`: Cập nhật cấu hình, hệ thống build, thay đổi thư viện dependencies mà không sửa code production.
- `style`: Thay đổi không ảnh hưởng đến ý nghĩa của code (khoảng trắng, định dạng, thiếu dấu phẩy...).
- `perf`: Thay đổi mã nguồn nhằm cải thiện hiệu năng.

## 3. Atomic Commits (Nguyên tắc Nguyên tử)

- Không gộp nhiều thay đổi không liên quan vào cùng một commit.
- Mỗi commit chỉ nên giải quyết **một vấn đề duy nhất**.
  - *Sai:* `git commit -m "fix(auth): sửa lỗi đăng nhập và làm xong giao diện todo"`
  - *Đúng (tách làm 2 commit):*
    - `git commit -m "fix(auth): sửa lỗi không nhận diện token"`
    - `git commit -m "feat(ui): thêm giao diện danh sách todo"`

## 4. Ví dụ Thực tế

**Sửa lỗi trong module auth:**
```
fix(auth): enforce token expiration in verify_token
```

**Thêm tính năng kiểm tra quyền sở hữu todo:**
```
feat(todos): check user ownership before updating todo
```

**Cập nhật test E2E cho Playwright:**
```
test(e2e): add playwright cross-user isolation test
```

**Cập nhật tài liệu kỹ thuật:**
```
docs(spec): add todo sharing technical specification
```

## 5. Cấu hình Commitlint
Dự án này đã được cấu hình `.commitlintrc.json` để kiểm tra quy tắc commit. Nếu bạn viết sai định dạng, commit có thể bị từ chối. Hãy đảm bảo tuân thủ đúng cấu trúc trên!
