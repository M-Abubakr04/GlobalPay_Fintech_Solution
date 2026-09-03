import {
  Activity,
  BrainCircuit,
  Building2,
  CreditCard,
  Gauge,
  Landmark,
  LayoutDashboard,
  FileBarChart,
  LogOut,
  Menu,
  ShieldCheck,
  WalletCards,
  X
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import type { UserRole } from "../types";

type NavItem = {
  label: string;
  path: string;
  icon: typeof LayoutDashboard;
  roles: UserRole[];
  module: string;
};

const nav: NavItem[] = [
  { label: "Overview", path: "/", icon: LayoutDashboard, roles: ["customer", "merchant", "analyst", "executive", "admin"], module: "Platform" },
  { label: "Customer & Wallet", path: "/wallet", icon: WalletCards, roles: ["customer", "admin"], module: "Module 1" },
  { label: "Payments", path: "/payments", icon: CreditCard, roles: ["customer", "analyst", "executive", "admin"], module: "Module 2" },
  { label: "Fraud Operations", path: "/fraud", icon: BrainCircuit, roles: ["analyst", "executive", "admin"], module: "Module 3" },
  { label: "Open Banking / CBDC", path: "/open-banking", icon: Landmark, roles: ["customer", "analyst", "executive", "admin"], module: "Module 4" },
  { label: "Executive Dashboard", path: "/executive", icon: Gauge, roles: ["analyst", "executive", "admin"], module: "Module 5" },
  { label: "Reports", path: "/reports", icon: FileBarChart, roles: ["executive", "admin"], module: "Evidence" }
];

export function AppShell() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  const available = nav.filter((item) => user && item.roles.includes(user.role));

  return (
    <div className="app-shell">
      <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><Building2 size={24} /></div>
          <div>
            <strong>GlobalPay</strong>
            <span>FinTech Solutions</span>
          </div>
          <button className="mobile-close" onClick={() => setOpen(false)} aria-label="Close menu"><X /></button>
        </div>

        <div className="environment-pill">
          <Activity size={14} />
          <span>Simulation environment</span>
        </div>

        <nav>
          {available.map(({ label, path, icon: Icon, module }) => (
            <NavLink
              key={path}
              to={path}
              end={path === "/"}
              onClick={() => setOpen(false)}
              className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}
            >
              <Icon size={19} />
              <span>
                <small>{module}</small>
                {label}
              </span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="compliance-chip">
            <ShieldCheck size={17} />
            <span>Standards-aligned PoC</span>
          </div>
          <button className="logout-button" onClick={logout}>
            <LogOut size={17} /> Sign out
          </button>
        </div>
      </aside>

      {open && <button className="sidebar-backdrop" onClick={() => setOpen(false)} aria-label="Close navigation" />}

      <main className="main-area">
        <header className="topbar">
          <button className="menu-button" onClick={() => setOpen(true)} aria-label="Open menu"><Menu /></button>
          <div>
            <p className="eyebrow">Enterprise financial technology platform</p>
            <h1>Operational workspace</h1>
          </div>
          <div className="user-card">
            <div className="avatar">{user?.email.slice(0, 1).toUpperCase()}</div>
            <div>
              <strong>{user?.email}</strong>
              <span>{user?.role}</span>
            </div>
          </div>
        </header>
        <div className="content"><Outlet /></div>
      </main>
    </div>
  );
}
