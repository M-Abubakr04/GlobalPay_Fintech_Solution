import type { ReactElement } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext";
import { ExecutivePage } from "./pages/ExecutivePage";
import { FraudPage } from "./pages/FraudPage";
import { LoginPage } from "./pages/LoginPage";
import { MerchantPage } from "./pages/MerchantPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { OpenBankingPage } from "./pages/OpenBankingPage";
import { OverviewPage } from "./pages/OverviewPage";
import { PaymentsPage } from "./pages/PaymentsPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ReportsPage } from "./pages/ReportsPage";
import { WalletPage } from "./pages/WalletPage";

function RoleRoute({
  roles,
  children
}: {
  roles: string[];
  children: ReactElement;
}) {
  const { user } = useAuth();
  return user && roles.includes(user.role) ? children : <Navigate to="/" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<OverviewPage />} />
        <Route path="/wallet" element={<RoleRoute roles={["customer", "admin"]}><WalletPage /></RoleRoute>} />
        <Route path="/merchant" element={<RoleRoute roles={["merchant"]}><MerchantPage /></RoleRoute>} />
        <Route path="/payments" element={<RoleRoute roles={["customer", "analyst", "executive", "admin"]}><PaymentsPage /></RoleRoute>} />
        <Route path="/fraud" element={<RoleRoute roles={["analyst", "executive", "admin"]}><FraudPage /></RoleRoute>} />
        <Route path="/open-banking" element={<RoleRoute roles={["customer", "analyst", "executive", "admin"]}><OpenBankingPage /></RoleRoute>} />
        <Route path="/executive" element={<RoleRoute roles={["analyst", "executive", "admin"]}><ExecutivePage /></RoleRoute>} />
        <Route path="/reports" element={<RoleRoute roles={["executive", "admin"]}><ReportsPage /></RoleRoute>} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
