import { ArrowRight, CheckCircle2, LockKeyhole, ShieldCheck, WalletCards } from "lucide-react";
import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { errorMessage } from "../lib/api";

const demoAccounts = [
  ["Customer", "customer@globalpay.example.com", "Customer123!"],
  ["Fraud analyst", "analyst@globalpay.example.com", "Analyst123!"],
  ["Executive", "executive@globalpay.example.com", "Executive123!"],
  ["Administrator", "admin@globalpay.example.com", "Admin123!"]
];

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("customer@globalpay.example.com");
  const [password, setPassword] = useState("Customer123!");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-hero">
        <div className="auth-brand">
          <div className="brand-mark large"><WalletCards /></div>
          <div><strong>GlobalPay</strong><span>FinTech Solutions</span></div>
        </div>
        <div className="hero-copy">
          <p className="eyebrow light">Enterprise FinTech simulation</p>
          <h1>One secure platform for wallets, payments, fraud intelligence and open finance.</h1>
          <p>
            A modular FastAPI and React proof of concept built for clear operation,
            auditability and live demonstration.
          </p>
          <div className="hero-points">
            <span><CheckCircle2 /> Five connected functional modules</span>
            <span><ShieldCheck /> Standards-aligned security controls</span>
            <span><LockKeyhole /> Simulated financial data only</span>
          </div>
        </div>
        <div className="hero-orbit orbit-one" />
        <div className="hero-orbit orbit-two" />
      </section>

      <section className="auth-form-section">
        <div className="auth-card">
          <div className="auth-card-head">
            <p className="eyebrow">Welcome back</p>
            <h2>Sign in to GlobalPay</h2>
            <p>Use a demo role or your registered customer account.</p>
          </div>
          <form onSubmit={submit} className="form-stack">
            <label>
              Email address
              <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
            </label>
            <label>
              Password
              <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
            </label>
            {error && <div className="form-error">{error}</div>}
            <button className="primary-button wide" disabled={busy}>
              {busy ? "Signing in…" : "Sign in"} <ArrowRight size={17} />
            </button>
          </form>

          <div className="demo-accounts">
            <span>Demo access</span>
            {demoAccounts.map(([label, accountEmail, accountPassword]) => (
              <button
                key={accountEmail}
                type="button"
                onClick={() => { setEmail(accountEmail); setPassword(accountPassword); }}
              >
                <strong>{label}</strong>
                <small>{accountEmail}</small>
              </button>
            ))}
          </div>
          <p className="auth-switch">New customer? <Link to="/register">Create an account</Link></p>
        </div>
      </section>
    </div>
  );
}
