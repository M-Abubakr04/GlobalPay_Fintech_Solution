import { Activity, KeyRound, Landmark, RefreshCw, WalletCards } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Panel } from "../components/Panel";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { useAuth } from "../context/AuthContext";
import { api, errorMessage } from "../lib/api";
import type { Wallet } from "../types";

interface Consent {
  id: string;
  client_name: string;
  scopes: string[];
  status: string;
  expires_at: string;
}
interface CbdcWallet {
  id: string;
  owner_label: string;
  balance: string | number;
  currency: string;
  status: string;
}
interface CbdcDirectoryItem {
  id: string;
  owner_label: string;
  currency: string;
  status: string;
}

interface Analytics {
  endpoint: string;
  calls: number;
  average_latency_ms: number;
}

export function OpenBankingPage() {
  const { user } = useAuth();
  const isCustomer = user?.role === "customer";
  const [consents, setConsents] = useState<Consent[]>([]);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [cbdc, setCbdc] = useState<CbdcWallet[]>([]);
  const [cbdcDirectory, setCbdcDirectory] = useState<CbdcDirectoryItem[]>([]);
  const [analytics, setAnalytics] = useState<Analytics[]>([]);
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [accountInfo, setAccountInfo] = useState<Record<string, unknown> | null>(null);
  const [clientName, setClientName] = useState("Demo Budgeting App");
  const [cbdcLabel, setCbdcLabel] = useState("My ePKR Wallet");
  const [pisForm, setPisForm] = useState({ consent_id: "", receiver_email: "receiver@globalpay.example.com", amount: "1200", description: "Open Banking PIS demo" });
  const [cbdcTransfer, setCbdcTransfer] = useState({ source_wallet_id: "", destination_wallet_id: "", amount: "250" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const common = [api.get("/cbdc/wallets"), api.get("/open-banking/health"), api.get("/cbdc/directory")];
      if (isCustomer) {
        const [cbdcRes, healthRes, directoryRes, consentRes, walletRes] = await Promise.all([
          ...common,
          api.get("/open-banking/consents"),
          api.get("/wallets/me")
        ]);
        setCbdc(cbdcRes.data); setHealth(healthRes.data); setCbdcDirectory(directoryRes.data); setConsents(consentRes.data); setWallet(walletRes.data);
        if (!pisForm.consent_id && consentRes.data.length) {
          setPisForm((current) => ({ ...current, consent_id: consentRes.data[0].id }));
        }
        if (cbdcRes.data.length && !cbdcTransfer.source_wallet_id) {
          const sourceId = cbdcRes.data[0].id;
          const destination = directoryRes.data.find((item: CbdcDirectoryItem) => item.id !== sourceId);
          setCbdcTransfer((current) => ({
            ...current,
            source_wallet_id: sourceId,
            destination_wallet_id: destination?.id || ""
          }));
        }
      } else {
        const [cbdcRes, healthRes, directoryRes, analyticsRes] = await Promise.all([
          ...common,
          api.get("/open-banking/analytics")
        ]);
        setCbdc(cbdcRes.data); setHealth(healthRes.data); setCbdcDirectory(directoryRes.data); setAnalytics(analyticsRes.data);
      }
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  useEffect(() => { load(); }, [isCustomer]);

  async function createConsent(event: FormEvent) {
    event.preventDefault(); setError(""); setMessage("");
    try {
      await api.post("/open-banking/consents", {
        client_name: clientName,
        scopes: ["accounts:read", "payments:write"],
        expires_in_hours: 720
      });
      setMessage("Scoped Open Banking consent created.");
      await load();
    } catch (err) { setError(errorMessage(err)); }
  }

  async function readAccount(consent: Consent) {
    if (!wallet) return;
    setError(""); setMessage("");
    try {
      const { data } = await api.get(`/open-banking/ais/accounts/${wallet.id}`, { params: { consent_id: consent.id } });
      setAccountInfo(data);
      setMessage("AIS account response received and API activity logged.");
    } catch (err) { setError(errorMessage(err)); }
  }

  async function createCbdc(event: FormEvent) {
    event.preventDefault(); setError(""); setMessage("");
    try {
      await api.post("/cbdc/wallets", { owner_label: cbdcLabel });
      setMessage("Simulated CBDC wallet created.");
      setCbdcLabel("");
      await load();
    } catch (err) { setError(errorMessage(err)); }
  }

  async function initiatePis(event: FormEvent) {
    event.preventDefault(); setError(""); setMessage("");
    try {
      const { data } = await api.post("/open-banking/pis/payments", pisForm);
      setMessage(`PIS payment ${data.reference} completed with status ${data.status}.`);
      await load();
    } catch (err) { setError(errorMessage(err)); }
  }

  async function transferCbdc(event: FormEvent) {
    event.preventDefault(); setError(""); setMessage("");
    try {
      const { data } = await api.post("/cbdc/transfer", cbdcTransfer);
      setMessage(`CBDC transfer ${data.reference} completed.`);
      await load();
    } catch (err) { setError(errorMessage(err)); }
  }

  const callCount = analytics.reduce((sum, item) => sum + item.calls, 0);

  return (
    <>
      <div className="page-title-row">
        <div><p className="eyebrow">Module 4</p><h2>Open Banking & CBDC Simulation</h2><p>Consent-based AIS/PIS APIs, ePKR wallet operations, API activity and health.</p></div>
        <button className="secondary-button" onClick={load}><RefreshCw size={16} /> Refresh</button>
      </div>
      {error && <div className="form-error">{error}</div>}
      {message && <div className="form-success">{message}</div>}

      <div className="stats-grid four">
        <StatCard label="API health" value={String(health?.status || "—")} detail={`${health?.success_rate ?? 100}% success rate`} icon={Activity} tone="teal" />
        <StatCard label="Consents" value={isCustomer ? consents.length : "Scoped"} detail="OAuth2/OIDC concepts" icon={KeyRound} tone="blue" />
        <StatCard label="CBDC wallets" value={cbdc.length} detail="Simulated ePKR" icon={WalletCards} tone="violet" />
        <StatCard label="API calls" value={isCustomer ? Number(health?.total_calls || 0) : callCount} detail="Activity and latency evidence" icon={Landmark} tone="amber" />
      </div>

      {isCustomer && (
        <div className="two-column">
          <Panel title="Open Banking consent" subtitle="Customer-authorised scopes with expiry and audit logging">
            <form className="form-stack compact" onSubmit={createConsent}>
              <label>Third-party application<input value={clientName} onChange={(e) => setClientName(e.target.value)} required /></label>
              <div className="scope-row"><span>accounts:read</span><span>payments:write</span></div>
              <button className="primary-button">Create consent</button>
            </form>
            <div className="consent-list">
              {consents.map((consent) => (
                <article key={consent.id}>
                  <div><strong>{consent.client_name}</strong><small>{consent.scopes.join(" · ")}</small></div>
                  <StatusBadge value={consent.status} />
                  <button className="table-button" onClick={() => readAccount(consent)}>Call AIS</button>
                </article>
              ))}
            </div>
          </Panel>

          <Panel title="CBDC wallet simulation" subtitle="No connection to a real central bank or production digital currency">
            <form className="inline-form" onSubmit={createCbdc}>
              <label>Wallet label<input value={cbdcLabel} onChange={(e) => setCbdcLabel(e.target.value)} required /></label>
              <button className="primary-button">Create ePKR wallet</button>
            </form>
            <div className="wallet-list">
              {cbdc.map((item) => (
                <article key={item.id}><div><strong>{item.owner_label}</strong><small className="mono">{item.id.slice(0, 12)}…</small></div><b>{Number(item.balance).toLocaleString()} {item.currency}</b></article>
              ))}
            </div>
          </Panel>
        </div>
      )}

      {isCustomer && (
        <div className="two-column">
          <Panel title="Payment Initiation Service (PIS)" subtitle="A scoped consent triggers a simulated wallet transfer">
            <form className="form-stack compact" onSubmit={initiatePis}>
              <label>Consent
                <select value={pisForm.consent_id} onChange={(e) => setPisForm({ ...pisForm, consent_id: e.target.value })} required>
                  <option value="">Select consent</option>
                  {consents.filter((item) => item.scopes.includes("payments:write")).map((item) => <option key={item.id} value={item.id}>{item.client_name}</option>)}
                </select>
              </label>
              <label>Receiver email<input type="email" value={pisForm.receiver_email} onChange={(e) => setPisForm({ ...pisForm, receiver_email: e.target.value })} required /></label>
              <label>Amount (PKR)<input type="number" min="1" step="0.01" value={pisForm.amount} onChange={(e) => setPisForm({ ...pisForm, amount: e.target.value })} required /></label>
              <label>Description<input value={pisForm.description} onChange={(e) => setPisForm({ ...pisForm, description: e.target.value })} /></label>
              <button className="primary-button" disabled={!pisForm.consent_id}>Initiate PIS payment</button>
            </form>
          </Panel>

          <Panel title="CBDC transfer" subtitle="Move simulated ePKR between active CBDC wallets">
            <form className="form-stack compact" onSubmit={transferCbdc}>
              <label>Source wallet
                <select value={cbdcTransfer.source_wallet_id} onChange={(e) => setCbdcTransfer({ ...cbdcTransfer, source_wallet_id: e.target.value })} required>
                  <option value="">Select your wallet</option>
                  {cbdc.map((item) => <option key={item.id} value={item.id}>{item.owner_label} · {Number(item.balance).toLocaleString()} {item.currency}</option>)}
                </select>
              </label>
              <label>Destination wallet
                <select value={cbdcTransfer.destination_wallet_id} onChange={(e) => setCbdcTransfer({ ...cbdcTransfer, destination_wallet_id: e.target.value })} required>
                  <option value="">Select destination</option>
                  {cbdcDirectory.filter((item) => item.id !== cbdcTransfer.source_wallet_id).map((item) => <option key={item.id} value={item.id}>{item.owner_label}</option>)}
                </select>
              </label>
              <label>Amount (ePKR)<input type="number" min="1" step="0.01" value={cbdcTransfer.amount} onChange={(e) => setCbdcTransfer({ ...cbdcTransfer, amount: e.target.value })} required /></label>
              <button className="primary-button">Transfer ePKR</button>
            </form>
          </Panel>
        </div>
      )}

      {!isCustomer && (
        <Panel title="API operations analytics" subtitle="Management view of endpoint usage and response latency">
          <div className="table-wrap">
            <table><thead><tr><th>Endpoint</th><th>Calls</th><th>Average latency</th></tr></thead>
              <tbody>{analytics.length ? analytics.map((item) => <tr key={item.endpoint}><td className="mono">{item.endpoint}</td><td>{item.calls}</td><td>{item.average_latency_ms} ms</td></tr>) : <tr><td colSpan={3} className="empty-state">No API activity yet.</td></tr>}</tbody>
            </table>
          </div>
        </Panel>
      )}

      {accountInfo && (
        <Panel title="AIS response" subtitle="ISO 20022-inspired field naming for the simulation">
          <pre className="json-view">{JSON.stringify(accountInfo, null, 2)}</pre>
        </Panel>
      )}

      <div className="control-note">
        <KeyRound />
        <div><strong>Open finance control evidence</strong><span>TLS, scoped consent, token expiry, ownership checks, rate-limit-ready cache, request audit logs and OWASP API controls.</span></div>
      </div>
    </>
  );
}
