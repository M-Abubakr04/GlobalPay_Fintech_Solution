import type { ReactElement } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute({ children }: { children: ReactElement }) {
  const { token } = useAuth();
  return token ? children : <Navigate to="/login" replace />;
}
