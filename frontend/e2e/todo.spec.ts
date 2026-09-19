import { test, expect } from "@playwright/test";

test.describe("Tier 2B: End-to-End Todo & Auth Tests", () => {
  // Hàm tạo email ngẫu nhiên đảm bảo mỗi kịch bản test có tài khoản độc lập, không bị trùng trong DB
  const generateEmail = (prefix: string) =>
    `${prefix}_${Date.now()}_${Math.floor(Math.random() * 10000)}@example.com`;
  const password = "123456";

  // ============================================================================
  // KỊCH BẢN 1: Full User Journey (Hành trình hoàn chỉnh của người dùng)
  // Visit Login -> Go to Register -> Register -> Logout -> Login -> Create Todo -> Toggle -> Logout
  // ============================================================================
  test("Scenario 1: Full User Journey", async ({ page }) => {
    const userEmail = generateEmail("PhamAnh");

    // 1. Mở trang đăng nhập đầu tiên
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: /welcome back/i })).toBeVisible();

    // 2. Bấm vào liên kết "Sign up" để sang trang Đăng ký
    await page.click("a:has-text('Sign up')");
    await expect(page).toHaveURL("/register");
    await expect(page.getByRole("heading", { name: /create account/i })).toBeVisible();

    // 3. Điền thông tin đăng ký tài khoản mới với đuôi chuẩn @example.com
    await page.fill("#email", userEmail);
    await page.fill("#password", password);
    await page.fill("#confirmPassword", password);
    await page.click('button[type="submit"]:has-text("Create Account")');

    // 4. Sau khi đăng ký thành công, hệ thống vào trang chủ
    await expect(page).toHaveURL("/");
    await expect(page.getByText(userEmail)).toBeVisible();

    // 5. Đăng xuất để kiểm tra tính năng Đăng nhập (Login Form)
    await page.click("button:has-text('Logout')");
    await expect(page).toHaveURL("/login");

    // 6. Điền thông tin vừa tạo vào form Đăng nhập để test luồng Login thực tế
    await page.fill("#email", userEmail);
    await page.fill("#password", password);
    await page.click('button[type="submit"]:has-text("Sign In")');

    // 7. Xác nhận đăng nhập thành công vào Dashboard
    await expect(page).toHaveURL("/");
    await expect(page.getByText(userEmail)).toBeVisible();

    // 8. Bấm nút "Add Todo" để mở Modal tạo việc cần làm
    await page.click("button:has-text('Add Todo')");
    await expect(page.getByRole("heading", { name: "Create Todo" })).toBeVisible();

    // 9. Điền thông tin Todo mới
    const todoTitle = "E2E Automated Task 1";
    await page.fill("#title", todoTitle);
    await page.fill("#description", "Task created by Playwright automated test");
    await page.click('button[type="submit"]:has-text("Create")');

    // 10. Kiểm tra Todo đã hiển thị trên màn hình
    await expect(page.getByText(todoTitle)).toBeVisible();

    // 11. Click Checkbox để đánh dấu hoàn thành Todo
    const todoRow = page.locator(".group", { hasText: todoTitle });
    const checkbox = todoRow.getByRole("checkbox");
    await checkbox.click();

    // 12. Xác nhận chữ tiêu đề bị gạch ngang (line-through)
    await expect(page.locator(`label:has-text("${todoTitle}")`)).toHaveClass(/line-through/);

    // 13. Đăng xuất kết thúc phiên làm việc
    await page.click("button:has-text('Logout')");
    await expect(page).toHaveURL("/login");
  });

  // ============================================================================
  // KỊCH BẢN 2: Cross-User Data Isolation (Cô lập dữ liệu giữa 2 người dùng)
  // User A tạo Todo bí mật -> User B đăng nhập vào KHÔNG ĐƯỢC nhìn thấy!
  // ============================================================================
  test("Scenario 2: Cross-User Data Isolation", async ({ browser }) => {
    const userA_Email = generateEmail("NguyenPhuong");
    const userB_Email = generateEmail("TranMinh");
    const secretTitle = `Secret Todo of User A [${Date.now()}]`;

    // --- PHIÊN 1: User A tạo Todo ---
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();

    // Đăng ký User A
    await pageA.goto("/register");
    await pageA.fill("#email", userA_Email);
    await pageA.fill("#password", password);
    await pageA.fill("#confirmPassword", password);
    await pageA.click('button[type="submit"]:has-text("Create Account")');
    await expect(pageA).toHaveURL("/");

    // Tạo Todo bí mật
    await pageA.click("button:has-text('Add Todo')");
    await pageA.fill("#title", secretTitle);
    await pageA.click('button[type="submit"]:has-text("Create")');
    await expect(pageA.getByText(secretTitle)).toBeVisible();

    // --- PHIÊN 2: User B mở trình duyệt ở phiên ẩn danh độc lập ---
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();

    // Đăng ký User B
    await pageB.goto("/register");
    await pageB.fill("#email", userB_Email);
    await pageB.fill("#password", password);
    await pageB.fill("#confirmPassword", password);
    await pageB.click('button[type="submit"]:has-text("Create Account")');
    await expect(pageB).toHaveURL("/");

    // ĐẢM BẢO 100%: User B TUYỆT ĐỐI KHÔNG NHÌN THẤY Todo của User A!
    const secretItemForB = pageB.getByText(secretTitle);
    await expect(secretItemForB).not.toBeVisible();

    // Đóng cả 2 trình duyệt
    await contextA.close();
    await contextB.close();
  });
});
