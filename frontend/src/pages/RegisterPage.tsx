import { ArrowLeft, ArrowRight, ShieldCheck } from "lucide-react";
import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { errorMessage } from "../lib/api";

export function RegisterPage() {
  const { register, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    national_id: "",
    password: ""
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function update(field: string, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register(form);
      await login(form.email, form.password);
      navigate("/wallet");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="registration-page">
      <div className="registration-shell">
        <Link className="back-link" to="/login"><ArrowLeft size={17} /> Back to sign in</Link>
        <div className="registration-grid">
          <section className="registration-info">
            <p className="eyebrow light">Module 1 · Digital onboarding</p>
            <h1>Create your GlobalPay customer profile and wallet.</h1>
            <p>The backend validates your request, hashes your password, encrypts sensitive identity fields and automatically creates a PKR wallet with a zero opening balance.</p>
            <div className="control-list">
              <span><ShieldCheck /> NIST SP 800-63 identity lifecycle alignment</span>
              <span><ShieldCheck /> ISO 27018 PII protection controls</span>
              <span><ShieldCheck /> OWASP input validation and secure authentication</span>
            </div>
          </section>

          <section className="registration-card">
            <div>
              <p className="eyebrow">Customer registration</p>
              <h2>Open a simulated wallet</h2>
            </div>
            <form className="form-grid" onSubmit={submit}>
              <label className="full">
                Full name
                <input value={form.full_name} onChange={(e) => update("full_name", e.target.value)} required minLength={2} />
              </label>
              <label>
                Email
                <input type="email" value={form.email} onChange={(e) => update("email", e.target.value)} required />
              </label>
              <label>
                Phone
                <input value={form.phone} onChange={(e) => update("phone", e.target.value)} placeholder="0300 1234567" />
              </label>
              <label>
                National ID
                <input value={form.national_id} onChange={(e) => update("national_id", e.target.value)} placeholder="Simulated only" />
              </label>
              <label>
                Password
                <input type="password" value={form.password} onChange={(e) => update("password", e.target.value)} minLength={10} required />
              </label>
              {error && <div className="form-error full">{error}</div>}
              <button className="primary-button full" disabled={busy}>
                {busy ? "Creating account…" : "Create customer & wallet"} <ArrowRight size={17} />
              </button>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
