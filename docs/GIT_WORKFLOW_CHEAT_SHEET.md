# Hướng Dẫn Quy Trình Git Workflow Chuẩn

Tài liệu này lưu trữ quy trình tạo nhánh và commit theo đúng chuẩn **Atomic Commits** và **Conventional Commits** áp dụng cho toàn bộ bài kiểm tra.

## 1. Quy Trình Chuẩn Mỗi Khi Làm Một Task Mới

Mỗi khi bắt đầu một Tier mới hoặc một tính năng mới, hãy làm theo 4 bước sau:

**Bước 1: Luôn tạo nhánh mới từ nhánh mặc định**
```bash
# Đảm bảo bạn đang ở nhánh chính và code mới nhất
git checkout main
git pull

# Tạo nhánh mới với tên theo chuẩn (ví dụ: assessment/ten-cua-ban hoặc feature/ten-task)
git checkout -b feature/ten-cua-task
```

**Bước 2: Viết code và chia nhỏ file (Stage)**
Chỉ `git add` những file liên quan đến MỘT vấn đề cụ thể.
```bash
# KHÔNG NÊN dùng lệnh này trừ khi mọi thứ đều liên quan chặt chẽ đến nhau:
# git add . 

# NÊN add từng file cụ thể:
git add duong_dan/file_1.py duong_dan/file_2.py
```

**Bước 3: Ghi Commit Message chuẩn Conventional**
```bash
git commit -m "<type>(<scope>): <mô tả ngắn bằng tiếng anh>"
```
*(Tham khảo `docs/COMMIT_GUIDELINES.md` để xem danh sách các `<type>` như feat, fix, docs, test...)*

**Bước 4: Đẩy code và tạo PR**
```bash
git push -u origin feature/ten-cua-task
```

---

## 2. Áp dụng cụ thể cho Tier 1 (Bug Hunting)

Nếu bạn chưa commit cho Tier 1, hãy copy và paste lần lượt các lệnh sau vào terminal:

```bash
# 1. Tạo nhánh cho Tier 1
git checkout -b feature/tier1-bug-fixes

# 2. Commit tài liệu
git add docs/tier_1_plan.md docs/PR_DESCRIPTION.md
git commit -m "docs(plan): add tier 1 execution plan and PR bug report"

# 3. Commit sửa lỗi cấu hình JWT
git add backend/app/core/security.py
git commit -m "fix(auth): enforce token expiration in verify_token"

# 4. Commit sửa tất cả các lỗi logic và cache của backend todo
git add backend/app/api/v1/todos.py
git commit -m "fix(todos): enforce ownership authorization and fix cache scoping/invalidation"

# 5. Commit sửa lỗi frontend
git add frontend/src/features/todos/api/todos.ts
git commit -m "fix(ui): implement optimistic update rollback on api error"

# 6. Đẩy nhánh lên Github
git push -u origin feature/tier1-bug-fixes
```
