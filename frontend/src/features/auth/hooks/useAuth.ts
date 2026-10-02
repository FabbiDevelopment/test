import { useNavigate } from "react-router-dom";
import { useLogout, useCurrentUser } from "../api/auth";

export function useAuth() {
  const navigate = useNavigate();
  const logoutMutation = useLogout();

  const token = localStorage.getItem("access_token");
  const isAuthenticated = !!token;

  const {
    data: user,
    isLoading,
    error,
  } = useCurrentUser();

  const logout = () => {
    logoutMutation.mutate(undefined, {
      onSettled: () => {
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
