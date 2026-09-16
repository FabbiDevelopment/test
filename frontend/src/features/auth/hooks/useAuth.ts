import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { queryClient } from "@/lib/queryClient";
import { useLogout, fetchCurrentUser } from "../api/auth";

export function useAuth() {
  const navigate = useNavigate();
  const logoutMutation = useLogout();

  const token = localStorage.getItem("access_token");
   // SAI: isAuthenticated = !!token — chỉ kiểm tra token tồn tại, không xác thực với server
  // → token hết hạn/invalid vẫn coi là đã đăng nhập cho tới khi API fail
  const isAuthenticated = !!token;

  const {
    data: user,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["currentUser"],
    queryFn: fetchCurrentUser,
    enabled: isAuthenticated,
    retry: false,
  });

  const logout = () => {
    logoutMutation.mutate(undefined, {
      onSuccess: () => {
        // SAI: không xóa React Query cache — user tiếp theo có thể thấy todos/profile của user trước
        // THÊM: clear toàn bộ query cache khi logout
        queryClient.clear();
        navigate("/login");
      },
      onError: () => {
        // Even on error, clear local tokens and redirect
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        // THÊM: clear cache cả khi logout API lỗi để tránh rò rỉ dữ liệu session cũ
        queryClient.clear();
        navigate("/login");
      },
    });
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    logout,
  };
}
