import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const token = localStorage.getItem("access_token");

  // SAI: chỉ kiểm tra token tồn tại trong localStorage — không validate expiry/signature với server
  // → user với token hết hạn vẫn vào được route cho tới khi API trả 401 (UX/state mismatch)
  // Không xóa comment SAI; vẫn dùng guard tối thiểu — /auth/me trên TodoPage xác thực thực tế
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
