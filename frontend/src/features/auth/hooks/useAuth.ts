import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useLogout, fetchCurrentUser } from "../api/auth";
import { queryClient } from "@/lib/queryClient";

export function useAuth() {
  const navigate = useNavigate();
  const logoutMutation = useLogout();

  const token = localStorage.getItem("access_token");

  const {
    data: user,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["currentUser"],
    queryFn: fetchCurrentUser,
    enabled: !!token,
    retry: false,
  });

  // Bug #11 fix: derive isAuthenticated from the actual server response rather
  // than mere token existence in localStorage. A stored token may be expired,
  // tampered, or blacklisted — only a successful /me response confirms validity.
  const isAuthenticated = !!user && !error;

  const logout = () => {
    logoutMutation.mutate(undefined, {
      onSuccess: () => {
        // Clear all cached user data on logout
        queryClient.removeQueries({ queryKey: ["currentUser"] });
        queryClient.removeQueries({ queryKey: ["todos"] });
        navigate("/login");
      },
      onError: () => {
        // Even on error, clear local tokens and cached data then redirect
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        queryClient.removeQueries({ queryKey: ["currentUser"] });
        queryClient.removeQueries({ queryKey: ["todos"] });
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
