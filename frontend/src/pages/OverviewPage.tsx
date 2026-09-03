import {
  ArrowUpRight,
  BrainCircuit,
  CreditCard,
  Database,
  Gauge,
  Landmark,
  ServerCog,
  ShieldCheck,
  WalletCards
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Panel } from "../components/Panel";
import { StatCard } from "../components/StatCard";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import type { ExecutiveDashboard, Wallet } from "../types";

const modules = [
  { number: "01", title: "Customer & Wallet", text: "Onboarding, profiles, balances, merchants and activity.", icon: WalletCards, path: "/wallet", color: "teal" },
  { number: "02", title: "Payment Processing", text: "Transfers, validation, ledger updates and status tracking.", icon: CreditCard, path: "/payments", color: "blue" },
  { number: "03", title: "Fraud AI", text: "Feature engineering, classification, scores and human review.", icon: BrainCircuit, path: "/fraud", color: "violet" },
  { number: "04", title: "Open Banking / CBDC", text: "Consent APIs, AIS/PIS and simulated ePKR operations.", icon: Landmark, path: "/open-banking", color: "amber" },
  { number: "05", title: "Executive Dashboard", text: "Read-only KPIs, trends, alerts and reporting.", icon: Gauge, path: "/executive", color: "red" }
];

export function OverviewPage() {
  const { user } = useAuth();
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [executive, setExecutive] = useState<ExecutiveDashboard | null>(null);

  useEffect(() => {
    if (user?.role === "customer") {
      api.get("/wallets/me").then((response) => setWallet(response.data)).catch(() => undefined);
    }
    if (user && ["admin", "executive", "analyst"].includes(user.role)) {
      api.get("/dashboard/executive").then((response) => setExecutive(response.data)).catch(() => undefined);
    }
  }, [user]);

  return (
    <>
      <section className="welcome-banner">
        <div>
          <p className="eyebrow light">GlobalPay modular monolith</p>
          <h2>Good day, {user?.email.split("@")[0]}.</h2>
          <p>Monitor the complete simulated financial journey through five connected business modules.</p>
        </div>
        <div className="architecture-badge">
          <ServerCog />
          <div><strong>6 containers</strong><span>1 modular backend</span></div>
        </div>
      </section>

      <div className="stats-grid">
        {user?.role === "customer" ? (
          <>
            <StatCard label="Available balance" value={`${Number(wallet?.balance || 0).toLocaleString()} ${wallet?.currency || "PKR"}`} detail="Authoritative PostgreSQL balance" icon={WalletCards} tone="teal" />
            <StatCard label="Wallet status" value={wallet?.status || "Loading"} detail="Protected by ownership checks" icon={ShieldCheck} tone="blue" />
            <StatCard label="Platform mode" value="Simulation" detail="No real bank or card data" icon={Database} tone="violet" />
          </>
        ) : (
          <>
            <StatCard label="Active customers" value={executive?.active_customers ?? "—"} detail="Module 1" icon={WalletCards} tone="teal" />
            <StatCard label="Payment volume" value={executive ? `${Number(executive.payment_volume).toLocaleString()} PKR` : "—"} detail="Module 2 completed payments" icon={CreditCard} tone="blue" />
            <StatCard label="Open fraud alerts" value={executive?.open_fraud_alerts ?? "—"} detail="Human review required" icon={BrainCircuit} tone="red" />
          </>
        )}
      </div>

      <Panel title="Connected functional modules" subtitle="Logical separation inside one FastAPI deployment unit">
        <div className="module-grid">
          {modules.map(({ number, title, text, icon: Icon, path, color }) => {
            const accessible =
              path === "/" ||
              user?.role === "admin" ||
              (path === "/wallet" && user?.role === "customer") ||
              (path === "/payments" && ["customer", "analyst", "executive"].includes(user?.role || "")) ||
              (path === "/fraud" && ["analyst", "executive"].includes(user?.role || "")) ||
              (path === "/open-banking" && ["customer", "analyst", "executive"].includes(user?.role || "")) ||
              (path === "/executive" && ["analyst", "executive"].includes(user?.role || ""));
            return (
              <article className={`module-card module-${color}`} key={number}>
                <div className="module-top"><span>{number}</span><Icon /></div>
                <h3>{title}</h3>
                <p>{text}</p>
                {accessible && <Link to={path}>Open module <ArrowUpRight size={16} /></Link>}
              </article>
            );
          })}
        </div>
      </Panel>

      <div className="two-column">
        <Panel title="Security architecture" subtitle="Control evidence built into the application">
          <ul className="evidence-list">
            <li><ShieldCheck /><div><strong>Identity and access</strong><span>Argon2 password hashing, JWT and role-based access control</span></div></li>
            <li><ShieldCheck /><div><strong>Financial integrity</strong><span>Decimal amounts, row locks, idempotency and double-entry ledger</span></div></li>
            <li><ShieldCheck /><div><strong>Privacy</strong><span>AES-GCM field encryption and no customer PII in audit metadata</span></div></li>
            <li><ShieldCheck /><div><strong>Observability</strong><span>Correlation IDs, Prometheus metrics and Grafana dashboards</span></div></li>
          </ul>
        </Panel>
        <Panel title="Runtime topology" subtitle="Laptop-optimised Docker Compose deployment">
          <div className="runtime-map">
            <div>React</div><span>→</span><div>FastAPI modules</div><span>→</span><div>PostgreSQL</div>
            <small>Redis cache · Prometheus · Grafana</small>
          </div>
        </Panel>
      </div>
    </>
  );
}
