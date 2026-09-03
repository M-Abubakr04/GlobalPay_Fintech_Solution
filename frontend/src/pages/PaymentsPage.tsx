import { CheckCircle2, Clock3, CreditCard, RefreshCw, ShieldAlert } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Panel } from "../components/Panel";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { useAuth } from "../context/AuthContext";
import { api, errorMessage } from "../lib/api";
import type { Transaction } from "../types";

interface MerchantOption {
  merchant_id: string;
  business_name: string;
  status: string;
  settlement_cycle: string;
}

interface FinancialReport {
  currency: string;
  breakdown: Array<{ transaction_type: string; count: number; volume: string | number }>;
}

interface PaymentDashboard {
  transaction_count: number;
  completed_count: number;
  failed_count: number;
  under_review_count: number;
  total_volume: string | number;
  recent_transactions: Transaction[];
}

export function PaymentsPage() {
  const { user } = useAuth();
  const isCustomer = user?.role === "customer";
  const [history, setHistory] = useState<Transaction[]>([]);
  const [dashboard, setDashboard] = useState<PaymentDashboard | null>(null);
  const [merchants, setMerchants] = useState<MerchantOption[]>([]);
  const [financialReport, setFinancialReport] = useState<FinancialReport | null>(null);
  const [merchantPayment, setMerchantPayment] = useState({ merchant_id: "", amount: "1500", description: "Demo merchant purchase" });
  const [form, setForm] = useState({
    receiver_email: "receiver@globalpay.example.com",
    amount: "2500",
    description: "Demo wallet transfer",
    new_device: false
  });
  const [result, setResult] = useState<Transaction | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setError("");
    try {
      if (isCustomer) {
        const [historyRes, merchantsRes] = await Promise.all([
          api.get("/payments/history"),
          api.get("/customers/merchants/active")
        ]);
        setHistory(historyRes.data);
        setMerchants(merchantsRes.data);
        if (!merchantPayment.merchant_id && merchantsRes.data.length) {
          setMerchantPayment((current) => ({ ...current, merchant_id: merchantsRes.data[0].merchant_id }));
        }
      } else {
        const dashboardRes = await api.get("/payments/dashboard");
        setDashboard(dashboardRes.data);
        setHistory(dashboardRes.data.recent_transactions);
        if (user?.role === "admin" || user?.role === "executive") {
          const reportRes = await api.get("/payments/reports/financial");
          setFinancialReport(reportRes.data);
        }
      }
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  useEffect(() => { load(); }, [isCustomer]);

  async function transfer(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const { data } = await api.post(
        "/payments/transfer",
        {
          receiver_email: form.receiver_email,
          amount: form.amount,
          description: form.description,
          new_device: form.new_device
        },
        { headers: { "Idempotency-Key": crypto.randomUUID() } }
      );
      setResult(data);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function chargeMerchant(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const { data } = await api.post(
        "/payments/merchant-charge",
        merchantPayment,
        { headers: { "Idempotency-Key": crypto.randomUUID() } }
      );
      setResult(data);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const completed = dashboard?.completed_count ?? history.filter((x) => x.status === "COMPLETED").length;
  const review = dashboard?.under_review_count ?? history.filter((x) => Number(x.risk_score || 0) >= 0.7).length;
  const volume = dashboard?.total_volume ?? history.filter((x) => x.status === "COMPLETED").reduce((sum, x) => sum + Number(x.amount), 0);

  return (
    <>
      <div className="page-title-row">
        <div><p className="eyebrow">Module 2</p><h2>Digital Payment Processing</h2><p>Secure simulated transfers with validation, atomic ledger entries, status and history.</p></div>
        <button className="secondary-button" onClick={load}><RefreshCw size={16} /> Refresh</button>
      </div>
      {error && <div className="form-error">{error}</div>}
      {result && <div className="form-success">Payment {result.reference} completed with risk score {Number(result.risk_score || 0).toFixed(2)}.</div>}

      <div className="stats-grid four">
        <StatCard label="Transactions" value={dashboard?.transaction_count ?? history.length} detail="All visible transactions" icon={CreditCard} tone="blue" />
        <StatCard label="Completed" value={completed} detail="Atomic debit and credit" icon={CheckCircle2} tone="teal" />
        <StatCard label="Under review" value={review} detail="AI score ≥ 0.70" icon={ShieldAlert} tone="red" />
        <StatCard label="Processed volume" value={`${Number(volume).toLocaleString()} PKR`} detail="Simulated only" icon={Clock3} tone="violet" />
      </div>

      {isCustomer && (
        <Panel title="Send a wallet payment" subtitle="The transaction engine validates ownership, balance and idempotency before posting ledger entries">
          <form className="payment-form" onSubmit={transfer}>
            <label>Receiver email<input type="email" value={form.receiver_email} onChange={(e) => setForm({ ...form, receiver_email: e.target.value })} required /></label>
            <label>Amount (PKR)<input type="number" min="1" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required /></label>
            <label className="wide-field">Description<input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} maxLength={255} /></label>
            <label className="checkbox-field"><input type="checkbox" checked={form.new_device} onChange={(e) => setForm({ ...form, new_device: e.target.checked })} /> Simulate a new device risk signal</label>
            <button className="primary-button" disabled={busy}>{busy ? "Processing…" : "Process payment"}</button>
          </form>
          <div className="flow-strip">
            <span>Authenticate</span><b>→</b><span>Validate balance</span><b>→</b><span>Fraud score</span><b>→</b><span>Debit + credit</span><b>→</b><span>Receipt</span>
          </div>
        </Panel>
      )}

      {isCustomer && (
        <Panel title="Simulated merchant payment" subtitle="Charge the customer wallet and credit the merchant settlement wallet">
          <form className="payment-form" onSubmit={chargeMerchant}>
            <label>Merchant
              <select value={merchantPayment.merchant_id} onChange={(e) => setMerchantPayment({ ...merchantPayment, merchant_id: e.target.value })} required>
                <option value="">Select merchant</option>
                {merchants.map((merchant) => <option key={merchant.merchant_id} value={merchant.merchant_id}>{merchant.business_name} · {merchant.settlement_cycle}</option>)}
              </select>
            </label>
            <label>Amount (PKR)<input type="number" min="1" step="0.01" value={merchantPayment.amount} onChange={(e) => setMerchantPayment({ ...merchantPayment, amount: e.target.value })} required /></label>
            <label className="wide-field">Description<input value={merchantPayment.description} onChange={(e) => setMerchantPayment({ ...merchantPayment, description: e.target.value })} /></label>
            <button className="primary-button" disabled={busy || !merchantPayment.merchant_id}>{busy ? "Processing…" : "Pay merchant"}</button>
          </form>
        </Panel>
      )}

      <Panel title={isCustomer ? "Transaction history" : "Payment operations dashboard"} subtitle="Financial status, channel and risk evidence">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Reference</th><th>Type</th><th>Channel</th><th>Amount</th><th>Risk score</th><th>Status</th><th>Time</th></tr></thead>
            <tbody>
              {history.length ? history.map((item) => (
                <tr key={item.id}>
                  <td className="mono">{item.reference}</td>
                  <td>{item.transaction_type.replaceAll("_", " ")}</td>
                  <td>{item.channel.replaceAll("_", " ")}</td>
                  <td>{Number(item.amount).toLocaleString()} {item.currency}</td>
                  <td>{item.risk_score == null ? "—" : Number(item.risk_score).toFixed(2)}</td>
                  <td><StatusBadge value={item.status} /></td>
                  <td>{new Date(item.created_at).toLocaleString()}</td>
                </tr>
              )) : <tr><td colSpan={7} className="empty-state">No payments recorded.</td></tr>}
            </tbody>
          </table>
        </div>
      </Panel>

      {!isCustomer && financialReport && (
        <Panel title="Financial report" subtitle="Completed payment count and volume by transaction type">
          <div className="table-wrap"><table>
            <thead><tr><th>Transaction type</th><th>Count</th><th>Volume</th></tr></thead>
            <tbody>{financialReport.breakdown.map((item) => <tr key={item.transaction_type}><td>{item.transaction_type.replaceAll("_", " ")}</td><td>{item.count}</td><td>{Number(item.volume).toLocaleString()} {financialReport.currency}</td></tr>)}</tbody>
          </table></div>
        </Panel>
      )}

      <div className="control-note">
        <ShieldAlert />
        <div><strong>Payment control evidence</strong><span>TLS transport, JWT/RBAC, Decimal amounts, idempotency keys, row locking, double-entry ledger, audit logs and PCI DSS conceptual scope.</span></div>
      </div>
    </>
  );
}
