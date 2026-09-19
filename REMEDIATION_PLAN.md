# Kế hoạch xử lý và nâng cấp dự án

## 1. Mục tiêu

Tài liệu này là kế hoạch và lịch sử quyết định cho assessment của Fabbi Todo App. Các hạng mục bắt buộc đã có implementation và bằng chứng tương ứng; trạng thái hiện hành được theo dõi trong `docs/BUG_REPORT.md` và `docs/TEST_PLAN.md`. Tier 4 là phần bonus đã được yêu cầu và triển khai end to end; Todo Sharing vẫn chỉ là đặc tả. Mục tiêu của kế hoạch là đảm bảo:

- Không có truy cập hoặc rò rỉ dữ liệu chéo người dùng.
- Token được xác thực, xoay vòng và thu hồi đúng.
- Cache không làm sai tính nhất quán hoặc phá vỡ data isolation.
- Backend, frontend, database và hạ tầng có cùng một hợp đồng hành vi.
- Mỗi lỗi có ý nghĩa đều được ghi vào issue register, có quyết định xử lý và có test hồi quy phù hợp.
- Thay đổi có thể review, rollout và rollback độc lập.
- Mỗi yêu cầu trong README có artefact và bằng chứng kiểm chứng tương ứng.

Tier 4 đã được hoàn thành theo vertical slice gồm Tags, filtering, bulk actions,
cache isolation, frontend controls và regression tests. Todo Sharing vẫn chỉ
được viết đặc tả production-grade theo đúng README; không triển khai code Todo
Sharing vì đó không phải yêu cầu của Task 3A.

## 2. Nguyên tắc thực hiện

1. Ưu tiên bảo mật và tính toàn vẹn dữ liệu trước UX, hiệu năng và refactor.
2. Viết test tái hiện lỗi trước hoặc trong cùng PR với bản sửa.
3. Sửa tại persistence boundary; không dựa vào việc frontend giấu nút hoặc kiểm tra client-side.
4. Mỗi PR chỉ giải quyết một nhóm rủi ro có liên quan và phải có đường rollback rõ ràng.
5. Không thay đổi API contract công khai nếu chưa ghi lại migration path hoặc compatibility impact.
6. Không benchmark database bằng SQLite. Các kết luận về index phải dựa trên PostgreSQL và dữ liệu đại diện.
7. Cache chỉ được tối ưu sau khi tính đúng đắn và data isolation đã được chứng minh.
8. Không đưa secret thật vào repository, image layer, log, fixture hoặc tài liệu.
9. Mọi yêu cầu phải được truy vết từ README → thay đổi → test → bằng chứng trong PR.
10. Git discipline được áp dụng trong suốt quá trình, không để đến cuối mới sửa lịch sử.
11. Tier bắt buộc phải hoàn thành và ổn định trước khi merge Tier 4 bonus.
12. Không tuyên bố “đã giải quyết toàn bộ” khi issue register còn mục chưa triage, chưa có lý do chấp nhận rủi ro hoặc chưa có bằng chứng kiểm chứng.

## 3. Thứ tự ưu tiên tổng thể

| Thứ tự | Nhóm xử lý | Mức độ | Lý do ưu tiên |
|---:|---|---|---|
| 0 | Baseline, test tái hiện và phương án khẩn cấp | P0 | Cần bằng chứng trước khi sửa và tránh regression |
| 1 | Authorization và cô lập Todo | P0 / Critical | Có thể đọc, sửa hoặc xóa dữ liệu người khác |
| 2 | Cache isolation và invalidation | P0 / Critical | Cache có thể trả dữ liệu của user khác |
| 3 | JWT, refresh và logout | P0 / Critical | Token hết hạn hoặc sai loại vẫn có thể được dùng |
| 4 | Correctness của update và API contract | P1 / High | Có thể mất dữ liệu hoặc cập nhật sai trạng thái |
| 5 | Frontend auth/query state isolation | P1 / High | Cache client có thể tồn tại qua lần đổi tài khoản |
| 6 | Database integrity và race condition | P1 / High | Dữ liệu trùng hoặc không nhất quán dưới concurrency |
| 7 | Query performance và pagination | P2 / Medium | Tăng tải, N+1 query và kết quả phân trang không ổn định |
| 8 | Docker, secrets và production hardening | P1–P2 | Cold-start, exposure và build không tái lập |
| 9 | E2E, manual test plan và tài liệu bắt buộc | P2 | Hoàn thiện safety net và deliverable 100 điểm |
| 10 | Tier 4: Tags, filtering và bulk actions | Bonus | Hoàn thành đầy đủ để đạt thêm 15 điểm |
| 11 | Audit chấm điểm và submission gate | Release gate | Chứng minh không thiếu yêu cầu hoặc bằng chứng |

P0 phải hoàn tất trước khi coi ứng dụng an toàn cho bất kỳ môi trường dùng chung nào.

### Ma trận điểm và bằng chứng bắt buộc

| Hạng mục README | Điểm | Deliverable tối thiểu | Bằng chứng để đóng gate |
|---|---:|---|---|
| Tier 1 — Bug Hunting & Fixes | 30 | Báo cáo lỗi và ít nhất 5 bản sửa có ý nghĩa, gồm ít nhất 2 backend và 1 frontend | Issue register, diff, regression tests, PR findings theo Location/Severity/Reason/Fix |
| Tier 2A — Backend tests | Thuộc 25 | Ít nhất 3 critical scenarios trong danh sách README | Kết quả `pytest tests/ -v` và liên kết test → issue |
| Tier 2B — Playwright E2E | Thuộc 25 | Ít nhất 2 flow bắt buộc | Kết quả headless, lệnh headed, trace/screenshot khi cần |
| Tier 2C — Manual test plan | Thuộc 25 | Test plan có precondition, steps, expected/actual, severity/priority | `docs/TEST_PLAN.md` đã thực thi và điền kết quả |
| Tier 3A — Todo Sharing spec | 10 | Spec production-grade, không triển khai code | `docs/TODO_SHARING_SPEC.md` được review theo template |
| Tier 3B — Docker/Infrastructure | 10 | Ít nhất 3 cải tiến; kế hoạch này nhắm hoàn thành cả 5 nhóm | Compose validation, image inspection, cold-start và security checks |
| Tier 3C — Database performance | 10 | EXPLAIN trước/sau, Alembic index migration, benchmark và tradeoff | `docs/PERFORMANCE_REPORT.md`, raw plans và migration test |
| Git workflow/submission | 15 | Branch đúng quy ước, commit atomic/conventional, PR đầy đủ, AI disclosure | Git log, commitlint nếu có, PR checklist và `docs/AI_USAGE.md` |
| Tier 4 — Bonus | +15 | Tags, filtering, bulk actions và toàn bộ rule liên quan | Backend/frontend tests, migration, E2E và API evidence |

### Issue register bắt buộc

Tạo `docs/BUG_REPORT.md` làm nguồn theo dõi duy nhất. Mỗi mục phải có ID, location, severity, impact/reproduction, root cause, fix, test, PR/commit và status. Danh sách ban đầu ít nhất phải bao phủ:

- JWT expiration bị tắt; access dependency không kiểm token type.
- Refresh token không được rotate/revoke đúng và logout không thu hồi session.
- Login làm lộ user tồn tại; JWT secret mặc định; chưa có policy/rate limit phù hợp.
- Todo detail/update/delete không owner-scoped.
- Cache key dùng chung giữa user/page/query và mutation không invalid cache.
- Cache invalidation chưa gắn đúng với transaction commit.
- `completed=false` không cập nhật; partial update có thể xóa description.
- Pagination không giới hạn và không có deterministic ordering.
- N+1 user lookup; thiếu index cho query chính.
- Email thiếu database uniqueness và race-safe registration handling.
- Model/migration/default/nullability/cascade cần được đối chiếu.
- React Query key thiếu user/params; logout không clear cache; optimistic update không rollback.
- Frontend tải 10.000 Todo, dùng array index làm key và xử lý 401 gây reload login.
- Rủi ro token trong local storage và auth transition không đồng bộ.
- CORS quá rộng, SQL echo mặc định, Redis không auth và DB/cache port bị publish.
- Compose thiếu healthcheck/readiness; container chạy root; thiếu `.dockerignore`.
- Frontend image dùng install không tái lập, global package không pin và Vite runtime env sai mô hình.
- Requirements production chứa dependency dev/CLI dư thừa hoặc trùng chức năng.
- Test hiện chỉ thiên về happy path, SQLite/Redis mock không đại diện integration behavior.
- Playwright chưa được thiết lập; frontend README còn là template mặc định.
- `.env` được track và `docs/` bị ignore trái với deliverable README.

Trong quá trình làm, mọi phát hiện mới phải được thêm vào register trước khi sửa. Mục không sửa phải có quyết định `accepted/deferred` kèm lý do; để đạt mục tiêu của kế hoạch này, không được còn lỗi Critical/High ở trạng thái đó.

## 4. Giai đoạn 0 — Thiết lập baseline và containment

### Việc cần làm

- Fork repository và tạo branch `assessment/<your-name>`; không làm trực tiếp trên default branch.
- Sửa `.gitignore` theo hướng chỉ ignore `docs/ANSWER_KEY.md`, cho phép track các deliverable hợp lệ dưới `docs/`.
- Tạo bộ artefact ngay từ đầu:
  - `docs/BUG_REPORT.md`;
  - `docs/TEST_PLAN.md`;
  - `docs/TODO_SHARING_SPEC.md`;
  - `docs/PERFORMANCE_REPORT.md`;
  - `docs/AI_USAGE.md` và prompt/config log đã loại bỏ secret.
- Lập ma trận traceability: Requirement ID → Issue/Test/Artifact → PR/Commit → Command evidence → Status.
- Chạy và ghi lại trạng thái ban đầu của backend test, frontend lint/build và Docker startup.
- Bổ sung test tái hiện tối thiểu cho cross-user access, cache leak và expired token.
- Không sửa test để hợp thức hóa hành vi sai; test phải mô tả hành vi an toàn mong muốn.
- Nếu hệ thống đã từng được public:
  - tạm tắt cache Todo hoặc purge toàn bộ cache;
  - rotate JWT secret và buộc đăng nhập lại;
  - đổi credential PostgreSQL/Redis;
  - giới hạn network exposure;
  - kiểm tra access log để tìm truy cập chéo user.

### Điều kiện hoàn thành

- Có test thất bại chứng minh từng lỗi P0 trước khi sửa.
- Có log của các lệnh kiểm tra và danh sách giới hạn môi trường.
- Có issue register và traceability matrix bao phủ toàn bộ yêu cầu README.
- Các deliverable trong `docs/` xuất hiện trong `git status` và không cần `git add -f`.
- Branch và commit strategy đã tuân thủ Git workflow của README.
- Không có thay đổi chức năng không liên quan trong PR baseline.

## 5. Giai đoạn 1 — Authorization và data isolation

### Vấn đề

Các endpoint lấy, sửa và xóa Todo đang truy vấn chỉ bằng `todo_id`. Một user đã đăng nhập có thể thao tác Todo của user khác nếu biết UUID.

### Cách xử lý

- Đổi service lookup thành truy vấn owner-scoped, ví dụ nhận cả `todo_id` và `user_id`.
- Áp dụng cùng một policy cho GET, UPDATE và DELETE; không sửa riêng từng route bằng logic rời rạc.
- Trả `404 Not Found` cho tài nguyên không tồn tại hoặc không thuộc user để tránh resource enumeration.
- Không nhận `user_id` từ request body cho thao tác tạo Todo; luôn lấy từ authenticated principal.
- Nếu sau này có Todo Sharing, mở rộng policy bằng một authorization service rõ ràng thay vì bỏ owner filter.

### Test bắt buộc

- User A không đọc được Todo của user B.
- User A không sửa được title, description hoặc completed của Todo user B.
- User A không xóa được Todo của user B.
- Owner vẫn thao tác được Todo của mình.
- UUID không tồn tại và UUID thuộc user khác có cùng public error behavior.

### Điều kiện hoàn thành

- Ownership nằm trong câu truy vấn database hoặc authorization service dùng chung.
- Không có đường CRUD nào dựa riêng vào kiểm tra frontend.
- Toàn bộ test cross-user chạy qua.

## 6. Giai đoạn 2 — Cache isolation và consistency

### Vấn đề

Cache key hiện tại dùng chung cho mọi user và bỏ qua pagination. Create, update và delete không invalid cache.

### Cách xử lý

- Tạm thời có thể disable list cache để đóng lỗ hổng nhanh, sau đó bật lại khi thiết kế mới có test.
- Chuẩn hóa input cache: user ID, page, size, filter, sort và schema version.
- Dùng key có namespace/version, ví dụ:

  ```text
  todos:list:v1:{user_id}:{cache_version}:{canonical_query_hash}
  ```

- Sau mỗi mutation đã commit thành công, tăng `todos:version:{user_id}` bằng thao tác atomic. Cách này tránh wildcard delete/`KEYS` và làm mọi list cache cũ không còn được tham chiếu.
- Chỉ invalid cache sau khi database commit thành công. Nếu vẫn dùng auto-commit trong dependency, cần tái cấu trúc transaction boundary hoặc commit rõ ràng trước khi bump version.
- Cache failure không được làm hỏng thao tác database đã thành công. Ghi log/metric và dựa vào TTL làm fallback.
- Không cache error response hoặc dữ liệu chưa được authorization.

### Test bắt buộc

- Hai user có cache key khác nhau và không nhận dữ liệu của nhau.
- Page/size/filter khác nhau tạo cache entry khác nhau.
- Create, update và delete làm request kế tiếp nhận dữ liệu mới.
- Transaction rollback không invalid cache như một mutation thành công.
- Redis unavailable có behavior đã xác định và không gây data leak.

### Điều kiện hoàn thành

- Không dùng global key như `todos:list`.
- Mutation và invalidation có thứ tự nhất quán với transaction.
- Integration test với Redis thật được chạy ít nhất cho cache versioning/invalidation.

## 7. Giai đoạn 3 — JWT, refresh token và logout

### Vấn đề

JWT expiration đang bị bỏ qua, access dependency không kiểm tra token type, refresh token không có rotation/revocation hoàn chỉnh và logout chỉ trả thông báo.

### Cách xử lý

- Để thư viện kiểm tra `exp`; không đặt `verify_exp=False`.
- Yêu cầu các claim tối thiểu: `sub`, `exp`, `type`; refresh token cần thêm `jti`.
- Tạo hàm verify nhận `expected_type` hoặc tách rõ access/refresh verification.
- Cố định allowlist algorithm từ server config; không tin algorithm do token khai báo.
- Refresh flow phải:
  1. xác thực expiration, signature, type và subject;
  2. kiểm tra user còn tồn tại/được phép đăng nhập;
  3. kiểm tra `jti` chưa bị revoke hoặc reuse;
  4. revoke refresh token cũ;
  5. phát access và refresh token mới.
- Lưu trạng thái refresh token trong Redis với TTL bằng expiration. Với yêu cầu bảo mật cao hơn, dùng token family và revoke toàn family khi phát hiện reuse.
- Logout revoke refresh token/session thực tế. Nếu cần revoke access token ngay lập tức, dùng access-token denylist ngắn hạn hoặc session version.
- Production phải fail fast nếu JWT secret vẫn là giá trị mặc định hoặc quá yếu.
- Login trả lỗi chung `401 Invalid email or password` cho cả email không tồn tại và password sai.

### Test bắt buộc

- Access token hết hạn và token bị sửa bị từ chối.
- Refresh token không gọi được access-only endpoint.
- Access token không gọi được refresh endpoint.
- Refresh token cũ không dùng lại được sau rotation.
- Logout làm refresh token không còn sử dụng được.
- Token của user đã bị xóa bị từ chối.
- Login sai email và sai password có cùng status/message công khai.

### Rollout

Thay đổi validation có thể làm token cũ mất hiệu lực. Ghi rõ đây là intentional session reset và triển khai cùng thay đổi frontend xử lý 401 ổn định.

## 8. Giai đoạn 4 — Correctness và API contract

### Vấn đề cần sửa

- Không thể cập nhật `completed` từ `true` về `false`.
- Update title có thể vô tình xóa description.
- Pagination không có giới hạn tối đa.
- Error/status code chưa nhất quán.

### Cách xử lý

- Dùng `model_dump(exclude_unset=True)` cho partial update.
- Áp dụng field nếu field được gửi, không dùng truthiness để quyết định cập nhật boolean.
- Chọn đúng HTTP verb/semantics: nếu endpoint là partial update, ưu tiên `PATCH`; nếu giữ `PUT` để tương thích thì tài liệu hóa rõ behavior.
- Giới hạn `size`, ví dụ `1 <= size <= 100`.
- Không trả dữ liệu thừa như `user_email` nếu client không cần.
- Map lỗi constraint/concurrency thành response ổn định; không trả stack trace hoặc chi tiết nội bộ.

### Test bắt buộc

- `completed: false` được lưu sau reload.
- Update title không xóa description.
- Explicit `description: null` xóa description nếu contract cho phép.
- Request rỗng và page size vượt giới hạn có response đã xác định.

## 9. Giai đoạn 5 — Frontend auth và query-state isolation

### Cách xử lý

- Query key Todo phải chứa user và toàn bộ pagination/filter/sort input.
- Khi logout, token hết hạn hoặc chuyển tài khoản:
  - cancel request đang chạy;
  - xóa toàn bộ user-scoped query data;
  - xóa credential local;
  - điều hướng về login.
- Không redirect cứng cho mọi `401` từ login/register endpoint; để form hiển thị lỗi authentication.
- Optimistic update phải rollback snapshot trong `onError`, sau đó refetch trong `onSettled`.
- Dùng `todo.id` làm React key.
- Không tải mặc định 10.000 Todo; triển khai pagination phù hợp giới hạn backend.
- Ngắn hạn có thể giữ bearer token trong `localStorage` để tránh mở rộng scope, nhưng phải thừa nhận rủi ro XSS. Hướng production nên cân nhắc refresh token trong `HttpOnly`, `Secure`, `SameSite` cookie và access token ngắn hạn trong memory; nếu dùng cookie phải thiết kế CSRF protection.

### Test bắt buộc

- User B không nhìn thấy cache/render tạm thời của user A sau logout/login.
- Query key thay đổi theo page/filter/user.
- Mutation thất bại rollback UI về trạng thái trước đó.
- Login sai hiển thị lỗi mà không reload trang.
- E2E hai browser context xác nhận cross-user isolation.

## 10. Giai đoạn 6 — Database integrity và migration safety

### Cách xử lý

- Chuẩn hóa email nhất quán trước khi lưu và truy vấn.
- Thêm unique constraint/index ở database cho email hoặc `lower(email)`; application-level pre-check không đủ chống race condition.
- Trước migration, kiểm tra và xử lý dữ liệu trùng. Không thêm unique constraint mù quáng trên dữ liệu production.
- Bắt `IntegrityError` khi hai request đăng ký đồng thời và trả response ổn định.
- Xác định cascade behavior cho user → todos; không để phụ thuộc vào default không rõ ràng.
- Đảm bảo model, migration và Pydantic contract đồng bộ về nullable/default/timezone.

### Test bắt buộc

- Đăng ký đồng thời cùng email chỉ tạo một user.
- Email normalization có behavior nhất quán.
- Migration upgrade/downgrade chạy trên PostgreSQL sạch và trên snapshot dữ liệu đại diện.
- Xóa user có behavior Todo được tài liệu hóa và kiểm thử.

## 11. Giai đoạn 7 — Query performance và pagination

### Cách xử lý

- Thêm deterministic ordering: `created_at DESC, id DESC`.
- Đo query hiện tại bằng `EXPLAIN (ANALYZE, BUFFERS)` trên PostgreSQL trước khi chọn index.
- Xem xét index theo query thật:
  - `(user_id, created_at DESC, id DESC)` cho list cơ bản;
  - `(user_id, completed, created_at DESC, id DESC)` nếu filter completed là đường truy vấn thường xuyên.
- Không thêm cả hai index nếu benchmark không chứng minh lợi ích; cân nhắc write amplification và dung lượng.
- Loại N+1 user query bằng join/eager loading hoặc bỏ `user_email` khỏi response nếu không cần.
- Cân nhắc cursor pagination cho dữ liệu lớn; nếu giữ offset pagination để tương thích, ghi rõ giới hạn và tradeoff.
- Với bảng lớn, thiết kế online/concurrent index migration phù hợp PostgreSQL và lưu ý Alembic transaction boundary.

### Bằng chứng bắt buộc

- Dataset size, hardware/container allocation và câu SQL chính xác.
- Query plan và thời gian trước/sau.
- Kích thước index và ảnh hưởng tới tốc độ insert/update.
- Test xác nhận pagination không trùng hoặc bỏ sót bản ghi khi nhiều row có cùng timestamp.

## 12. Giai đoạn 8 — Docker và production hardening

### Cách xử lý

- Thêm healthcheck PostgreSQL và Redis; backend chỉ start sau khi dependency healthy.
- Thêm retry/backoff có giới hạn cho startup thay vì dựa hoàn toàn vào startup order.
- Tạo `.dockerignore` riêng cho backend/frontend.
- Dùng `npm ci` và khóa version runtime package; không cài global `serve` không pin.
- Dùng multi-stage build, loại compiler/build dependency khỏi final image và chạy non-root.
- Tách cấu hình development và production.
- Không publish PostgreSQL/Redis port trong production nếu không cần.
- Đưa secret qua secret manager/runtime injection; không hard-code trong Compose.
- Giới hạn CORS bằng allowlist theo môi trường và chỉ bật credentials khi cần.
- Tắt SQL echo mặc định ngoài local development.
- Xử lý `VITE_API_URL` ở build time hoặc dùng runtime config endpoint/file; environment của container static server không tự thay đổi bundle đã build.

### Test bắt buộc

- Cold start lặp lại nhiều lần không làm backend crash vì database chưa sẵn sàng.
- Healthcheck phản ánh dependency thực, không chỉ kiểm tra process tồn tại.
- Build chạy tái lập từ clean checkout.
- Container final không chạy root và không chứa `.env`, source cache hoặc dev-only tool không cần thiết.
- Production config không expose database/cache port và không chứa secret mặc định.

## 13. Giai đoạn 9 — Hoàn thiện test và deliverable bắt buộc

### Backend

- Giữ test nhanh bằng SQLite cho logic không phụ thuộc dialect.
- Thêm integration suite PostgreSQL/Redis cho migration, constraint, transaction và cache.
- Dùng clock có thể kiểm soát cho token-expiration tests.
- Dùng Redis mock dùng chung khi test nhiều request liên tiếp; mock mới cho từng dependency call không mô phỏng cache thật.
- Đảm bảo có ít nhất ba scenario mà README yêu cầu, nhưng mục tiêu là cover cả năm: JWT, cross-user authorization, boolean false, partial update và cache invalidation.

### Frontend và E2E

- Thiết lập Playwright rõ ràng, có headless/headed command và script trong package manifest.
- Dùng test user riêng hoặc API fixture; test phải chạy lặp lại được và tự cleanup.
- Bắt buộc có full user journey và hai browser context cho cross-user isolation.
- Bổ sung flow token hết hạn/logout, cache clear và Tier 4 nếu đã triển khai.
- Bổ sung test cho query key, cache clear và optimistic rollback ở mức unit/component phù hợp.
- Lưu trace/video/screenshot cho failure; không commit artefact dung lượng lớn nếu không cần.

### Tài liệu

- Hoàn thiện `docs/TEST_PLAN.md` theo `templates/TEST_PLAN_TEMPLATE.md`, bao gồm cả Actual Result và trạng thái Pass/Fail sau khi chạy.
- Hoàn thiện `docs/TODO_SHARING_SPEC.md` theo `templates/SPEC_TEMPLATE.md`; Task 3A chỉ yêu cầu spec, không triển khai Todo Sharing.
- Hoàn thiện `docs/BUG_REPORT.md`, `docs/PERFORMANCE_REPORT.md` và `docs/AI_USAGE.md`.
- Cập nhật `README.md`/`GUIDE.md` nếu setup, test command, API hoặc cấu hình đã thay đổi.
- PR description phải ghi findings, severity, reproduction, fix, test evidence, tradeoff, known limitation và AI disclosure.

### Cổng hoàn thành 100 điểm bắt buộc

- Tier 1 đạt đủ số lượng fix và phân bố backend/frontend.
- Tier 2A, 2B và 2C đều có artefact thực thi được.
- Cả Task 3A, 3B và 3C đều hoàn thành; không coi Tier 3 là tùy chọn.
- Git workflow/submission evidence đã được cập nhật liên tục.
- Toàn bộ lệnh validation bắt buộc chạy xanh hoặc có blocker khách quan được mô tả; blocker không được dùng để tuyên bố đã đạt điểm.

## 14. Giai đoạn 10 — Tier 4 để đạt đủ 15 điểm bonus (đã hoàn thành)

Tier 4 đã được thực hiện sau các gate bắt buộc như một vertical slice hoàn
chỉnh, không chỉ dựng UI hoặc schema rời rạc. Các mục bên dưới là checklist đã
được đáp ứng và là chuẩn cho các thay đổi Tier 4 tiếp theo.

### Database và migration

- Tạo bảng `tags` với `id`, `user_id`, `name`, `color`, `created_at`, `updated_at` đúng kiểu và nullability README yêu cầu.
- Tạo bảng nối `todo_tags` với composite primary key `(todo_id, tag_id)`.
- Khai báo foreign key và cascade behavior rõ ràng.
- Đảm bảo tên tag unique không phân biệt hoa/thường theo từng user bằng database constraint/index phù hợp PostgreSQL.
- Thêm index trên `tags(user_id)`, `todo_tags(tag_id)`, `todo_tags(todo_id)` và index Todo dựa trên benchmark/query thực.
- Migration phải có upgrade/downgrade test và kiểm tra dữ liệu hiện hữu.

### Backend/API

- Implement đầy đủ `GET/POST/PATCH/DELETE /tags`.
- Implement attach/detach tag cho Todo và `PATCH /todos/bulk-status`.
- Mở rộng `GET /todos` với status, tag, keyword, date range và pagination.
- Mọi lookup tag/Todo phải owner-scoped; không cho gắn tag của user khác vào Todo.
- Bulk update chạy trong một transaction và không partial success.
- Pagination order cố định `created_at DESC, id DESC`.
- Cache key bao gồm user và toàn bộ filter; create/update/delete/tag mapping/bulk update đều invalid cache sau commit.

### Frontend

- Thêm filter bar cho keyword, status, tag, date range và clear filters.
- Hiển thị tag trên Todo và có UI quản lý create/rename/delete tag.
- Có selection và bulk complete/active action với loading/error state rõ ràng.
- React Query key chứa toàn bộ filter/page/user; mutation invalid đúng namespace.
- Form dùng react-hook-form và Zod, đồng bộ validation backend.
- Logout/account switch xóa mọi Todo/tag cache theo user.

### Test bắt buộc

- Tag creation và duplicate casing.
- Cross-user tag access và attach tag của user khác bị từ chối.
- Filter theo tag/status/keyword/date và pagination ổn định.
- Bulk update kiểm ownership, atomicity và cả `completed=false`.
- Cache invalidation cho tag mapping và bulk update.
- Frontend validation, query-key behavior, success/error/rollback của bulk action.
- E2E quản lý tag, filter và bulk action trên dữ liệu thật.

### Điều kiện hoàn thành bonus

- Không làm regression các gate 100 điểm bắt buộc.
- API contract, migration, UI, cache và test được merge cùng một feature set có thể chạy end to end.
- Tất cả rule Tier 4 tại README đều có dòng tương ứng trong traceability matrix.

## 15. Quality gate áp dụng cho mọi Pull Request

Mỗi PR chỉ được merge khi đáp ứng đầy đủ:

1. Issue/requirement IDs được ghi trong title hoặc description.
2. Có reproduction hoặc test đỏ trước fix đối với bug.
3. Có implementation nhỏ nhất giải quyết root cause, không chỉ che symptom.
4. Có test success, failure và authorization/concurrency path nếu liên quan.
5. Backend `pytest`, Black/Flake8 liên quan; frontend lint/build/test liên quan đã chạy.
6. Migration chạy upgrade/downgrade trên PostgreSQL nếu PR đổi schema.
7. Cache/auth change có integration evidence, không chỉ mock evidence.
8. API/config thay đổi đã cập nhật docs và E2E fixture nếu cần.
9. `git diff` không chứa secret, generated artefact hoặc unrelated change.
10. Commit atomic và theo Conventional Commits.
11. PR ghi rõ risk, compatibility, rollout, rollback và commands đã chạy.
12. Traceability matrix và issue register được cập nhật trước khi merge.

## 16. Kế hoạch chia Pull Request

Không nên đưa toàn bộ assessment vào một PR lớn. Thứ tự đề xuất:

1. `docs/assessment-governance`: `.gitignore`, issue register, test plan skeleton, traceability và AI disclosure skeleton.
2. `test/security-baseline`: test tái hiện JWT, ownership và cache leak.
3. `fix/todo-authorization`: owner-scoped CRUD và test cross-user.
4. `fix/todo-cache-consistency`: scoped/versioned cache và invalidation sau commit.
5. `fix/auth-token-lifecycle`: JWT validation, rotation, revocation và generic login error.
6. `fix/todo-update-contract`: boolean false, partial update và pagination limit.
7. `fix/frontend-session-isolation`: query keys, cache clear, rollback và 401 handling.
8. `fix/database-integrity`: email constraint, race handling và migration tests.
9. `perf/todo-query-indexes`: ordering, N+1 removal, index và benchmark evidence.
10. `build/container-hardening`: hoàn thành ít nhất ba, mục tiêu là toàn bộ hạng mục Tier 3B.
11. `docs/todo-sharing-spec`: hoàn thiện riêng Task 3A để review rõ ràng.
12. `test/e2e-and-manual-plan`: Playwright, manual execution và required evidence.
13. `feat/todo-tags-domain`: schema, models, service và tag CRUD.
14. `feat/todo-filtering-and-mapping`: filters, attach/detach và cache behavior.
15. `feat/todo-bulk-actions-ui`: bulk backend/frontend và E2E bonus.
16. `docs/final-assessment-report`: cập nhật benchmark, bug report, README/GUIDE, AI disclosure và final score audit.

Nếu submission chỉ cho phép một PR cuối, vẫn giữ commit sequence trên trong cùng branch để lịch sử atomic và dễ review. Không để một commit “test sau” chịu trách nhiệm chứng minh nhiều bản sửa đã có trước đó.

## 17. Final score audit và submission gate

Trước khi mở hoặc cập nhật PR cuối, thực hiện một vòng audit độc lập theo README từ đầu đến cuối.

### Audit chức năng và bảo mật

- Mọi issue trong `docs/BUG_REPORT.md` đã ở trạng thái `fixed` hoặc `verified`; không còn Critical/High deferred.
- Đếm thực tế số fix Tier 1 và xác nhận quota backend/frontend.
- Chạy toàn bộ backend unit/integration, frontend checks và Playwright trên clean environment.
- Chạy manual test plan và điền Actual Result/Pass-Fail, không để placeholder.
- Chạy dependency/secret/config scan phù hợp và review diff thủ công.

### Audit Tier 3

- Task 3A có spec đầy đủ user story, schema, API, authorization, edge case, cache và out-of-scope.
- Task 3B chứng minh ít nhất ba cải tiến bằng behavior, không chỉ bằng sự tồn tại của file.
- Task 3C có raw before/after evidence, Alembic migration và giải thích tradeoff.

### Audit Git và PR

- Branch đúng `assessment/<name>` hoặc `feature/<topic>`.
- Commit history atomic, conventional và không có generic commit lớn.
- PR description có bảng findings theo đúng bốn trường README yêu cầu.
- PR có test commands, results, reproduction, benchmark, tradeoff và limitation.
- AI usage và prompt/config logs được công bố nhưng đã loại bỏ secret/private data.

### Audit bonus

- Tất cả backend/frontend rules Tier 4 có implementation và test tương ứng.
- Bonus E2E chạy sau toàn bộ mandatory suites để chứng minh không regression.

Chỉ đánh dấu “sẵn sàng submission” khi mọi dòng trong ma trận điểm có owner, artefact, evidence link và trạng thái `verified`.

## 18. Rollout và rollback

- Dùng migration theo chiến lược expand/contract nếu thay đổi schema hoặc API nhiều bước.
- Backup và kiểm tra dữ liệu trùng trước unique migration.
- Có thể deploy owner-scoped query trước cache mới; trong thời gian chuyển tiếp nên disable cache thay vì giữ cache không an toàn.
- JWT hardening có thể buộc tất cả user đăng nhập lại; thông báo rõ và rotate secret có kiểm soát.
- Theo dõi tối thiểu: tỷ lệ 401/403/404, cache hit/miss/error, database latency, refresh-token reuse và startup failure.
- Nếu cache release gây lỗi, tắt cache bằng config/feature flag; không rollback authorization fix.
- Nếu index gây write latency hoặc lock ngoài dự kiến, rollback riêng migration/index mà không rollback security fixes.
- Tier 4 nên có feature flag hoặc migration-compatible deploy order nếu rollout trên môi trường đang có dữ liệu.

## 19. Definition of Done

Một hạng mục chỉ được coi là hoàn tất khi:

- Có test chứng minh lỗi cũ và hành vi mới.
- Security boundary được enforce ở backend/database.
- Test happy path, failure path và cross-user path liên quan đều chạy qua.
- Không có secret mới hoặc file sinh tự động bị commit.
- Migration/lockfile/documentation được cập nhật nếu cần.
- Lint, build, unit test và integration test phù hợp đã chạy; phần không chạy được phải được ghi rõ.
- Có đánh giá compatibility, rollout, monitoring và rollback tương xứng với rủi ro.
- `git diff` chỉ chứa thay đổi trong scope và không làm mất thay đổi của người khác.
- Issue register và README traceability đã chuyển sang `verified` với evidence cụ thể.

Assessment bắt buộc được coi là hoàn tất khi đạt toàn bộ gate tương ứng 100
điểm và final score audit không còn ô trống hoặc bằng chứng chưa kiểm chứng.
Tier 4 đã được yêu cầu và được đưa vào điều kiện hoàn tất: Tags, filtering và
bulk actions có implementation, migration, cache invalidation và test end to
end tương ứng.

## 20. Kết quả mong đợi sau cùng

Sau khi hoàn thành theo thứ tự trên, dự án phải đạt được các tính chất sau:

- User chỉ truy cập được dữ liệu mình có quyền sử dụng.
- Token hết hạn, sai loại, bị revoke hoặc bị sửa đều bị từ chối.
- Cache backend và cache frontend không bao giờ làm lộ dữ liệu qua account boundary.
- Partial update không làm mất dữ liệu và boolean `false` được xử lý đúng.
- Database bảo vệ uniqueness/integrity kể cả dưới concurrency.
- Query có thứ tự ổn định, index được chứng minh bằng benchmark.
- Container khởi động ổn định, chạy với quyền tối thiểu và không chứa secret mặc định.
- Tags, filtering và bulk actions hoạt động end to end theo toàn bộ rule Tier 4.
- Bộ test và tài liệu đủ để ngăn các lỗi quan trọng tái xuất hiện.
- Submission có bằng chứng truy vết cho toàn bộ 100 điểm bắt buộc và 15 điểm
  Tier 4 bonus đã triển khai.
