import { BrainCircuit, RefreshCw, ShieldAlert, Target, UserCheck } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Panel } from "../components/Panel";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { api, errorMessage } from "../lib/api";
import type { FraudAlert } from "../types";

interface ModelInfo {
  status?: string;
  version?: string;
  algorithm?: string;
  metrics?: Record<string, number>;
  threshold?: string | number;
  trained_at?: string;
  human_review_required?: boolean;
}

export function FraudPage() {
  const [alerts, setAlerts] = useState<FraudAlert[]>([]);
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [selected, setSelected] = useState<FraudAlert | null>(null);
  const [decision, setDecision] = useState("LEGITIMATE");
  const [notes, setNotes] = useState("Customer identity and transaction context verified.");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [training, setTraining] = useState(false);

  async function load() {
    setError("");
    try {
      const [alertRes, modelRes] = await Promise.all([
        api.get("/fraud/alerts"),
        api.get("/fraud/model/latest")
      ]);
      setAlerts(alertRes.data);
      setModel(modelRes.data);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  useEffect(() => { load(); }, []);

  async function train() {
    setTraining(true);
    setError("");
    setMessage("");
    try {
      const { data } = await api.post("/fraud/train");
      setMessage(`Model ${data.version} trained. Human review remains mandatory.`);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setTraining(false);
    }
  }

  async function review(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    setError("");
    setMessage("");
    try {
      const { data } = await api.post(`/fraud/alerts/${selected.id}/review`, { decision, notes });
      setMessage(`Alert ${data.alert_id.slice(0, 8)} reviewed as ${data.decision}.`);
      setSelected(null);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  const high = alerts.filter((x) => x.risk_band === "HIGH").length;
  const open = alerts.filter((x) => x.status === "OPEN").length;
  const average = alerts.length ? alerts.reduce((sum, x) => sum + Number(x.risk_score), 0) / alerts.length : 0;

  return (
    <>
      <div className="page-title-row">
        <div><p className="eyebrow">Module 3</p><h2>AI-Assisted Fraud Detection</h2><p>Lightweight supervised classification, explainable signals and mandatory analyst review.</p></div>
        <div className="button-row">
          <button className="secondary-button" onClick={load}><RefreshCw size={16} /> Refresh</button>
          <button className="primary-button" onClick={train} disabled={training}><BrainCircuit size={16} /> {training ? "Training…" : "Train model"}</button>
        </div>
      </div>
      {error && <div className="form-error">{error}</div>}
      {message && <div className="form-success">{message}</div>}

      <div className="stats-grid four">
        <StatCard label="Open alerts" value={open} detail="Requires human decision" icon={ShieldAlert} tone="red" />
        <StatCard label="High risk" value={high} detail="Score greater than 0.70" icon={Target} tone="amber" />
        <StatCard label="Average risk" value={average.toFixed(2)} detail="Current alert set" icon={BrainCircuit} tone="violet" />
        <StatCard label="Decision mode" value="Human review" detail="No automatic blocking" icon={UserCheck} tone="teal" />
      </div>

      <div className="two-column">
        <Panel title="Active model" subtitle="ISO 42001 and NIST AI RMF evidence">
          {model?.version ? (
            <div className="profile-list">
              <div><span>Version</span><strong>{model.version}</strong></div>
              <div><span>Algorithm</span><strong>{model.algorithm}</strong></div>
              <div><span>Threshold</span><strong>{Number(model.threshold).toFixed(2)}</strong></div>
              <div><span>F1 score</span><strong>{model.metrics?.f1?.toFixed(3) || "—"}</strong></div>
              <div><span>Human oversight</span><StatusBadge value="REQUIRED" /></div>
            </div>
          ) : (
            <div className="empty-card">The model is not trained yet. Select “Train model” to import the simulated dataset, engineer features and register a version.</div>
          )}
        </Panel>
        <Panel title="Feature signals" subtitle="Examples used by the classifier and fallback rule engine">
          <div className="signal-cloud">
            <span>Unusual amount</span><span>2 AM activity</span><span>High velocity</span><span>New device</span><span>Merchant risk</span><span>Customer history</span>
          </div>
          <p className="muted-copy">The model supports analysts; a high score generates an alert but does not automatically block a payment.</p>
        </Panel>
      </div>

      <Panel title="Fraud alert queue" subtitle="Select an alert to record an investigation decision">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Transaction</th><th>Risk</th><th>Confidence</th><th>Band</th><th>Reasons</th><th>Status</th><th>Action</th></tr></thead>
            <tbody>
              {alerts.length ? alerts.map((alert) => (
                <tr key={alert.id}>
                  <td className="mono">{alert.transaction_reference}</td>
                  <td>{Number(alert.risk_score).toFixed(2)}</td>
                  <td>{Number(alert.confidence).toFixed(2)}</td>
                  <td><StatusBadge value={alert.risk_band} /></td>
                  <td>{alert.reasons.join(", ")}</td>
                  <td><StatusBadge value={alert.status} /></td>
                  <td><button className="table-button" onClick={() => setSelected(alert)} disabled={alert.status === "CLOSED"}>Review</button></td>
                </tr>
              )) : <tr><td colSpan={7} className="empty-state">No fraud alerts yet. A high-risk simulated payment will appear here.</td></tr>}
            </tbody>
          </table>
        </div>
      </Panel>

      {selected && (
        <div className="modal-backdrop" onClick={() => setSelected(null)}>
          <form className="modal-card" onSubmit={review} onClick={(e) => e.stopPropagation()}>
            <p className="eyebrow">Human review</p>
            <h3>Review {selected.transaction_reference}</h3>
            <p>Risk {Number(selected.risk_score).toFixed(2)} · {selected.reasons.join(", ")}</p>
            <label>Decision
              <select value={decision} onChange={(e) => setDecision(e.target.value)}>
                <option value="LEGITIMATE">Legitimate</option>
                <option value="CONFIRMED_FRAUD">Confirmed fraud</option>
                <option value="ESCALATE">Escalate</option>
              </select>
            </label>
            <label>Analyst notes<textarea value={notes} onChange={(e) => setNotes(e.target.value)} required rows={4} /></label>
            <div className="button-row"><button type="button" className="secondary-button" onClick={() => setSelected(null)}>Cancel</button><button className="primary-button">Record decision</button></div>
          </form>
        </div>
      )}
    </>
  );
}
