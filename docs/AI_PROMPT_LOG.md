# AI Prompt Log

Đây là log tóm tắt một số prompt tiêu biểu trong quá trình thực hiện bài Full-Stack Engineering & Quality Assurance Assessment với sự hỗ trợ của AI.

AI chủ yếu được sử dụng để hỗ trợ code review, phân tích vấn đề, debugging, thiết kế test và kiểm tra giải pháp. Việc áp dụng thay đổi, chạy test và verify kết quả được thực hiện trên codebase và môi trường local.

---

## 1. Code Review — Tìm bug Backend

### Prompt

"Đang làm bài test Todo App, giờ t muốn tập trung tìm bug backend/frontend. Review code giúp t, ưu tiên những bug có ảnh hưởng thực tế như authorization, data isolation và correctness."

### Follow-up

"Những bug nào trong phần này đủ meaningful để đưa vào assessment?"

### Mục đích

Hỗ trợ code review và xác định các vấn đề cần kiểm tra sâu hơn.

---

## 2. Authorization — Cross-user Todo

### Prompt

"Phân tích đoạn code này giúp t. Nếu user A biết ID Todo của user B thì có thể get hoặc update Todo đó không? T muốn kiểm tra lỗi authorization."

### Follow-up

"Nếu đúng là có lỗi thì nên check ownership ở đâu để tránh endpoint khác lại quên check?"

### Mục đích

Xác định và sửa lỗi cross-user Todo access.

---

## 3. Todo Update — Boolean `true → false`

### Prompt

"T đang có hàm update Todo kiểu partial update. Có trường hợp completed từ true về false nhưng database không update đúng. Xem giúp t nguyên nhân."

### Follow-up

"Vậy sửa thế nào để false vẫn được update mà không ảnh hưởng các field khác?"

### Mục đích

Sửa lỗi boolean update và đảm bảo partial update hoạt động đúng.

---

## 4. Redis Cache — Data Isolation

### Prompt

"Review phần Redis cache Todo list này giúp t. T nghi cache key đang không tách theo user. Nếu đúng thì user này có thể lấy cache của user khác không?"

### Follow-up

"Nếu không tách cache key thì cho t một flow cụ thể để reproduce vấn đề này."

### Mục đích

Kiểm tra và sửa vấn đề data isolation trong Redis cache.

---

## 5. Redis Cache — Invalidation

### Prompt

"Todo create/update/delete chạy đúng nhưng t thấy cache có thể vẫn trả data cũ. Review flow này giúp t xem invalidate nên đặt ở đâu."

### Follow-up

"Vậy cả create, update và delete đều cần xử lý cache invalidation à?"

### Mục đích

Đảm bảo cache consistency sau Todo mutations.

---

## 6. Frontend — Optimistic Update Rollback

### Prompt

"Đoạn React Query này đang optimistic update. T thấy API báo lỗi nhưng UI vẫn thay đổi. Đây có phải bug không?"

### Follow-up

"Fix cụ thể phần onError như thế nào để UI quay lại state trước đó?"

### Mục đích

Sửa lỗi frontend optimistic update không rollback khi API mutation thất bại.

---

## 7. Backend Tests — Pytest

### Prompt

"Đề yêu cầu ít nhất 3 critical backend scenarios. Với những bug t vừa tìm được thì nên test những case nào để coverage tốt?"

### Follow-up

"T muốn test cả case description không bị mất khi update completed. Case này nên viết như thế nào?"

### Mục đích

Xác định các backend test scenario quan trọng và đảm bảo coverage cho các bug đã phát hiện.

---

## 8. Playwright — E2E

### Prompt

"Giờ làm Playwright. Đề yêu cầu full user journey và cross-user isolation. Giúp t lên test flow."

### Follow-up

"Cross-user isolation thì nên tạo 2 account trong test hay dùng account có sẵn?"

### Mục đích

Thiết kế E2E tests theo yêu cầu assessment.

---

## 9. Todo Sharing — Technical Specification

### Prompt

"Giờ đến Tier 3A, chưa cần code. T phải viết spec cho Todo Sharing. Đề yêu cầu self-sharing, duplicate invite, concurrent update và revoke cache invalidation. Giúp t structure spec."

### Follow-up

"Ngoài mấy case đề nói thì còn edge case nào đáng ghi vào spec?"

### Mục đích

Xây dựng technical specification trước khi triển khai feature.

---

## 10. Docker — Review Configuration

### Prompt

"Review Docker setup giúp t. Đề yêu cầu ít nhất 3 cải tiến. T đang xem healthcheck, depends_on, dockerignore và image size."

### Follow-up

"Phần depends_on có nên dùng service_healthy không? Giải thích giúp t vì sao."

### Mục đích

Cải thiện reliability và build efficiency của Docker setup.

---

## 11. Database — EXPLAIN ANALYZE

### Prompt

"Đây là EXPLAIN ANALYZE query Todo của t. Query filter theo user_id và order theo created_at. Đọc giúp t xem đang chậm ở đâu và nên thêm index gì."

### Follow-up

"Đề còn yêu cầu nói về write latency, storage và migration safety. Giải thích trade-off của index này giúp t."

### Mục đích

Phân tích query performance và xây dựng indexing strategy cho Tier 3C.

---

## 12. Database — Verify After Index

### Prompt

"T đã tạo index rồi. Đây là EXPLAIN ANALYZE mới, xem giúp t PostgreSQL có thực sự dùng index không."

### Follow-up

"Còn query COUNT thì sao? T muốn có evidence riêng cho query này."

### Mục đích

Xác minh hiệu quả của index bằng execution plan thực tế.

---

## 13. Database — Debug Migration

### Prompt

"Alembic báo migration đang ở head nhưng query pg_indexes lại không thấy index. T không muốn chạy migration lung tung làm hỏng DB. Giúp t kiểm tra từng bước."

### Follow-up

"Kết quả là alembic_version đã là c8a33068b5c1 nhưng index vẫn không có. Giờ kiểm tra tiếp thế nào?"

### Mục đích

Debug sự không đồng nhất giữa migration state và database schema.

---

## 14. Git & Pull Request

### Prompt

"T đã làm xong các tier. Giờ giúp t chuẩn bị PR theo đúng yêu cầu đề. Commit phải theo Conventional Commits và PR phải mô tả findings, tests, trade-offs."

### Follow-up

"PR nên chia thành những section nào để reviewer dễ kiểm tra từng requirement?"

### Mục đích

Chuẩn bị Git workflow và Pull Request theo yêu cầu assessment.

---

## Verification

AI được sử dụng để hỗ trợ phân tích, review và debugging. T tự áp dụng các thay đổi vào codebase, chạy test, thực hiện database queries, kiểm tra Docker và verify kết quả trước khi đưa vào submission.