import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import type { UserRole } from "../types/domain";

interface ProtectedRouteProps {
  allowedRole: UserRole;
}

export function ProtectedRoute({ allowedRole }: ProtectedRouteProps) {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role !== allowedRole) {
    const fallbackPath = user.role === "ADMIN" ? "/admin" : "/courier";
    return <Navigate to={fallbackPath} replace />;
  }

  return <Outlet />;
}
