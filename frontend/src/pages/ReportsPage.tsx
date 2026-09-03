import { Download, FileBarChart, RefreshCw, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Panel } from "../components/Panel";
import { StatCard } from "../components/StatCard";
import { api, errorMessage } from "../lib/api";
import type { ExecutiveDashboard } from "../types";

interface FinancialReport {
  currency: string;
  breakdown: Array<{ transaction_type: string; count: number; volume: string | number }>;
}

function download(name: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function ReportsPage() {
  const [executive, setExecutive] = useState<ExecutiveDashboard | null>(null);
  const [financial, setFinancial] = useState<FinancialReport | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [executiveResponse, financialResponse] = await Promise.all([
        api.get("/dashboard/executive"),
        api.get("/payments/reports/financial")
      ]);
      setExecutive(executiveResponse.data);
      setFinancial(financialResponse.data);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const totalReportVolume = useMemo(
    () => financial?.breakdown.reduce((sum, row) => sum + Number(row.volume), 0) || 0,
    [financial]
  );

  function exportFinancialCsv() {
    if (!financial) return;
    const rows = [
      ["Transaction type", "Completed count", `Volume (${financial.currency})`],
      ...financial.breakdown.map((row) => [row.transaction_type, row.count, row.volume])
    ];
    const csv = rows.map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(",")).join("\n");
    download(`globalpay-financial-report-${new Date().toISOString().slice(0, 10)}.csv`, csv, "text/csv;charset=utf-8");
  }

  function exportExecutiveJson() {
    if (!executive) return;
    const report = {
      report: "GlobalPay Executive Financial Operations Report",
      generated_at: new Date().toISOString(),
      data_classification: "SIMULATED DATA ONLY",
      ...executive
    };
    download(`globalpay-executive-report-${new Date().toISOString().slice(0, 10)}.json`, JSON.stringify(report, null, 2), "application/json");
  }

  return (
    <>
      <div className="page-title-row">
        <div><p className="eyebrow">Reporting evidence</p><h2>Financial & Compliance Reports</h2><p>Live, read-only reporting across payments, fraud, Open Banking and CBDC operations.</p></div>
        <button className="secondary-button" onClick={load} disabled={loading}><RefreshCw size={16} /> {loading ? "Loading…" : "Refresh"}</button>
      </div>
      {error && <div className="form-error">Unable to load reports: {error}</div>}

      <div className="stats-grid four">
        <StatCard label="Completed payments" value={executive?.payment_count ?? "—"} detail={`${executive?.payment_success_rate ?? "—"}% success`} icon={FileBarChart} tone="blue" />
        <StatCard label="Reported volume" value={financial ? `${totalReportVolume.toLocaleString()} ${financial.currency}` : "—"} detail="Completed transactions" icon={Download} tone="teal" />
        <StatCard label="Open fraud alerts" value={executive?.open_fraud_alerts ?? "—"} detail={`${executive?.high_risk_alerts ?? "—"} high risk`} icon={ShieldCheck} tone="red" />
        <StatCard label="Open Banking calls" value={executive?.api_calls ?? "—"} detail={`${executive?.cbdc_wallets ?? "—"} CBDC wallets`} icon={FileBarChart} tone="violet" />
      </div>

      <div className="two-column">
        <Panel title="Financial report" subtitle="Completed count and volume by transaction type">
          <div className="button-row report-actions"><button className="primary-button" onClick={exportFinancialCsv} disabled={!financial}><Download size={16} /> Export CSV</button></div>
          <div className="table-wrap"><table><thead><tr><th>Transaction type</th><th>Count</th><th>Volume</th></tr></thead><tbody>
            {financial?.breakdown.length ? financial.breakdown.map((row) => <tr key={row.transaction_type}><td>{row.transaction_type.replaceAll("_", " ")}</td><td>{row.count}</td><td>{Number(row.volume).toLocaleString()} {financial.currency}</td></tr>) : <tr><td colSpan={3}>{loading ? "Loading report…" : "No completed transactions yet"}</td></tr>}
          </tbody></table></div>
        </Panel>

        <Panel title="Executive report" subtitle="Cross-module snapshot with seven-day trend">
          <div className="button-row report-actions"><button className="primary-button" onClick={exportExecutiveJson} disabled={!executive}><Download size={16} /> Export JSON</button></div>
          <div className="table-wrap"><table><thead><tr><th>Date</th><th>Payments</th><th>Volume</th></tr></thead><tbody>
            {executive?.trends.map((row) => <tr key={row.date}><td>{row.date}</td><td>{row.payments}</td><td>{Number(row.volume).toLocaleString()} PKR</td></tr>)}
          </tbody></table></div>
        </Panel>
      </div>

      <Panel title="Compliance reporting scope" subtitle="Implementation evidence; not a claim of formal certification">
        <div className="report-control-grid">
          <div><strong>Payment controls</strong><span>ISO 20022-style fields, Decimal amounts, idempotency, ledger and audit trail.</span></div>
          <div><strong>Security controls</strong><span>JWT, role-based access, encrypted PII, rate limits and OWASP-aligned validation.</span></div>
          <div><strong>AI governance</strong><span>Versioned metrics, explainable risk reasons and mandatory human review.</span></div>
          <div><strong>Reporting governance</strong><span>Read-only executive access, simulated data labels and exportable evidence.</span></div>
        </div>
      </Panel>
    </>
  );
}
