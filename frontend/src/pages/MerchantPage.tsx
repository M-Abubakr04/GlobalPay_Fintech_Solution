import { Building2, Download, ReceiptText, RefreshCw, WalletCards } from "lucide-react";
import { useEffect, useState } from "react";
import { Panel } from "../components/Panel";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { api, errorMessage } from "../lib/api";

interface MerchantPayment {
  id: string;
  reference: string;
  amount: string | number;
  currency: string;
  status: string;
  channel: string;
  description?: string | null;
  created_at: string;
}

interface MerchantReport {
  merchant_id: string;
  business_name: string;
  status: string;
  settlement_cycle: string;
  wallet_id: string;
  wallet_status: string;
  balance: string | number;
  currency: string;
  completed_payment_count: number;
  completed_payment_volume: string | number;
  payments: MerchantPayment[];
}

function csvCell(value: unknown) {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

export function MerchantPage() {
  const [report, setReport] = useState<MerchantReport | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/customers/merchant/me/report");
      setReport(data);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  function exportCsv() {
    if (!report) return;
    const rows = [
      ["Reference", "Date", "Amount", "Currency", "Status", "Channel", "Description"],
      ...report.payments.map((payment) => [payment.reference, payment.created_at, payment.amount, payment.currency, payment.status, payment.channel, payment.description || ""])
    ];
    const blob = new Blob([rows.map((row) => row.map(csvCell).join(",")).join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `globalpay-merchant-payments-${new Date().toISOString().slice(0, 10)}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <>
      <div className="page-title-row">
        <div><p className="eyebrow">Module 1 · Merchant</p><h2>Merchant Settlement Portal</h2><p>Read-only visibility into the simulated settlement wallet and payments received.</p></div>
        <div className="button-row">
          <button className="secondary-button" onClick={load} disabled={loading}><RefreshCw size={16} /> {loading ? "Loading…" : "Refresh"}</button>
          <button className="primary-button" onClick={exportCsv} disabled={!report}><Download size={16} /> Export CSV</button>
        </div>
      </div>
      {error && <div className="form-error">Unable to load merchant settlement data: {error}</div>}

      <div className="stats-grid four">
        <StatCard label="Settlement balance" value={report ? `${Number(report.balance).toLocaleString()} ${report.currency}` : "—"} detail="PostgreSQL source of truth" icon={WalletCards} tone="teal" />
        <StatCard label="Payments received" value={report?.completed_payment_count ?? "—"} detail="Completed merchant payments" icon={ReceiptText} tone="blue" />
        <StatCard label="Received volume" value={report ? `${Number(report.completed_payment_volume).toLocaleString()} ${report.currency}` : "—"} detail="Completed payments" icon={Download} tone="violet" />
        <StatCard label="Settlement cycle" value={report?.settlement_cycle ?? "—"} detail="Simulated configuration" icon={Building2} tone="amber" />
      </div>

      <div className="two-column">
        <Panel title="Merchant profile" subtitle="Account and settlement configuration">
          <div className="profile-list">
            <div><span>Business name</span><strong>{report?.business_name || "Loading…"}</strong></div>
            <div><span>Merchant status</span>{report && <StatusBadge value={report.status} />}</div>
            <div><span>Settlement wallet</span><strong className="mono">{report?.wallet_id || "—"}</strong></div>
            <div><span>Wallet status</span>{report && <StatusBadge value={report.wallet_status} />}</div>
          </div>
        </Panel>
        <Panel title="Settlement scope" subtitle="Purposefully limited for the assessment proof of concept">
          <ul className="evidence-list">
            <li><WalletCards /><div><strong>Read-only access</strong><span>Merchants cannot alter balances or transaction status.</span></div></li>
            <li><ReceiptText /><div><strong>Traceable receipts</strong><span>Every payment has a reference, channel, status and timestamp.</span></div></li>
            <li><Building2 /><div><strong>Simulated settlement</strong><span>No payout, acquiring bank or card network is connected.</span></div></li>
          </ul>
        </Panel>
      </div>

      <Panel title="Payments received" subtitle="Latest 100 credits to the merchant settlement wallet">
        <div className="table-wrap"><table>
          <thead><tr><th>Reference</th><th>Date</th><th>Description</th><th>Channel</th><th>Amount</th><th>Status</th></tr></thead>
          <tbody>{report?.payments.length ? report.payments.map((payment) => (
            <tr key={payment.id}><td className="mono">{payment.reference}</td><td>{new Date(payment.created_at).toLocaleString()}</td><td>{payment.description || "Merchant payment"}</td><td>{payment.channel.replaceAll("_", " ")}</td><td>{Number(payment.amount).toLocaleString()} {payment.currency}</td><td><StatusBadge value={payment.status} /></td></tr>
          )) : <tr><td colSpan={6} className="empty-state">{loading ? "Loading payments…" : "No payments received yet."}</td></tr>}</tbody>
        </table></div>
      </Panel>
    </>
  );
}
