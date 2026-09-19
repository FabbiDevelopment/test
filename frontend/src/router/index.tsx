import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ProtectedRoute } from "./ProtectedRoute";

const LoginPage = lazy(() =>
  import("@/pages/LoginPage").then(({ LoginPage }) => ({ default: LoginPage })),
);
const RegisterPage = lazy(() =>
  import("@/pages/RegisterPage").then(({ RegisterPage }) => ({
    default: RegisterPage,
  })),
);
const DashboardPage = lazy(() =>
  import("@/pages/DashboardPage").then(({ DashboardPage }) => ({
    default: DashboardPage,
  })),
);

export function AppRouter() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div role="status">Loading page...</div>}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
