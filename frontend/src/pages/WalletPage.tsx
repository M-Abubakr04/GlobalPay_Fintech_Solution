import { Building2, FileText, RefreshCw, UserRound, WalletCards } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Panel } from "../components/Panel";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { useAuth } from "../context/AuthContext";
import { api, errorMessage } from "../lib/api";
import type { Wallet } from "../types";

interface Profile {
  id: string;
  email: string;
  full_name: string;
  phone_masked?: string;
  national_id_masked?: string;
  kyc_status: string;
  is_active: boolean;
  created_at: string;
}

interface Activity {
  ledger_entry_id: string;
  reference: string;
  entry_type: string;
  amount: string | number;
  balance_after: string | number;
  status: string;
  transaction_type: string;
  description?: string;
  created_at: string;
}

interface CustomerReport {
  transaction_count: number;
  total_sent: string | number;
  total_received: string | number;
  merchant_status?: string | null;
}

export function WalletPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [profile, setProfile] = useState<Profile | null>(null);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [report, setReport] = useState<CustomerReport | null>(null);
  const [merchantName, setMerchantName] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [adminCustomers, setAdminCustomers] = useState<any[]>([]);
  const [adminWallets, setAdminWallets] = useState<any[]>([]);

  async function load() {
    setError("");
    try {
      if (isAdmin) {
        const [customersRes, walletsRes] = await Promise.all([
          api.get("/customers/admin/list"),
          api.get("/wallets/admin/list")
        ]);
        setAdminCustomers(customersRes.data);
        setAdminWallets(walletsRes.data);
        return;
      }
      const [profileRes, walletRes, activityRes, reportRes] = await Promise.all([
        api.get("/customers/me"),
        api.get("/wallets/me"),
        api.get("/wallets/me/activity"),
        api.get("/customers/me/report")
      ]);
      setProfile(profileRes.data);
      setWallet(walletRes.data);
      setActivity(activityRes.data);
      setReport(reportRes.data);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  useEffect(() => { load(); }, [isAdmin]);

  async function applyMerchant(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    setError("");
    try {
      const { data } = await api.post("/customers/merchant-application", { business_name: merchantName });
      setMessage(`Merchant application ${data.status}. Settlement wallet: ${data.wallet_id || "already created"}`);
      setMerchantName("");
      await load();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  if (isAdmin) {
    const totalBalance = adminWallets.reduce((sum, item) => sum + Number(item.balance), 0);
    return (
      <>
        <div className="page-title-row">
          <div><p className="eyebrow">Module 1</p><h2>Customer & Digital Wallet Administration</h2><p>Read-only operational view of registered customers and simulated wallets.</p></div>
          <button className="secondary-button" onClick={load}><RefreshCw size={16} /> Refresh</button>
        </div>
        {error && <div className="form-error">{error}</div>}
        <div className="stats-grid four">
          <StatCard label="Customers" value={adminCustomers.length} detail="Registered profiles" icon={UserRound} tone="blue" />
          <StatCard label="Wallets" value={adminWallets.length} detail="Customer and merchant" icon={WalletCards} tone="teal" />
          <StatCard label="Total simulated balance" value={`${totalBalance.toLocaleString()} PKR`} detail="Operational total" icon={FileText} tone="violet" />
          <StatCard label="Active accounts" value={adminCustomers.filter((x) => x.active).length} detail="Current customers" icon={Building2} tone="amber" />
        </div>
        <Panel title="Registered customers" subtitle="PII-minimised administration view">
          <div className="table-wrap"><table>
            <thead><tr><th>Name</th><th>Email</th><th>KYC</th><th>Status</th><th>Created</th></tr></thead>
            <tbody>{adminCustomers.map((item) => <tr key={item.customer_id}><td>{item.name}</td><td>{item.email}</td><td><StatusBadge value={item.kyc_status} /></td><td><StatusBadge value={item.active ? "ACTIVE" : "INACTIVE"} /></td><td>{new Date(item.created_at).toLocaleString()}</td></tr>)}</tbody>
          </table></div>
        </Panel>
        <Panel title="Wallet register" subtitle="Balances remain authoritative in PostgreSQL">
          <div className="table-wrap"><table>
            <thead><tr><th>Wallet ID</th><th>Owner</th><th>Type</th><th>Balance</th><th>Status</th></tr></thead>
            <tbody>{adminWallets.map((item) => <tr key={item.id}><td className="mono">{item.id}</td><td>{item.owner_name}</td><td>{item.owner_type}</td><td>{Number(item.balance).toLocaleString()} {item.currency}</td><td><StatusBadge value={item.status} /></td></tr>)}</tbody>
          </table></div>
        </Panel>
      </>
    );
  }

  return (
    <>
      <div className="page-title-row">
        <div><p className="eyebrow">Module 1</p><h2>Customer & Digital Wallet Management</h2><p>Identity, wallet balance, activity, merchant onboarding and customer reporting.</p></div>
        <button className="secondary-button" onClick={load}><RefreshCw size={16} /> Refresh</button>
      </div>
      {error && <div className="form-error">{error}</div>}
      {message && <div className="form-success">{message}</div>}

      <div className="stats-grid four">
        <StatCard label="Wallet balance" value={`${Number(wallet?.balance || 0).toLocaleString()} ${wallet?.currency || "PKR"}`} detail="PostgreSQL source of truth" icon={WalletCards} tone="teal" />
        <StatCard label="KYC status" value={profile?.kyc_status || "—"} detail="NIST 800-63 aligned lifecycle" icon={UserRound} tone="blue" />
        <StatCard label="Transactions" value={report?.transaction_count ?? "—"} detail="Complete wallet activity" icon={FileText} tone="violet" />
        <StatCard label="Merchant status" value={report?.merchant_status || "Not applied"} detail="Optional merchant account" icon={Building2} tone="amber" />
      </div>

      <div className="two-column">
        <Panel title="Customer profile" subtitle="Sensitive values are encrypted and only masked values are returned">
          <div className="profile-list">
            <div><span>Full name</span><strong>{profile?.full_name || "Loading…"}</strong></div>
            <div><span>Email</span><strong>{profile?.email || "—"}</strong></div>
            <div><span>Phone</span><strong>{profile?.phone_masked || "Not provided"}</strong></div>
            <div><span>National ID</span><strong>{profile?.national_id_masked || "Not provided"}</strong></div>
            <div><span>Account</span>{profile && <StatusBadge value={profile.is_active ? "ACTIVE" : "INACTIVE"} />}</div>
          </div>
        </Panel>

        <Panel title="Customer financial report" subtitle="Transaction summary generated from the ledger">
          <div className="mini-stats">
            <div><span>Total sent</span><strong>{Number(report?.total_sent || 0).toLocaleString()} PKR</strong></div>
            <div><span>Total received</span><strong>{Number(report?.total_received || 0).toLocaleString()} PKR</strong></div>
            <div><span>Current balance</span><strong>{Number(wallet?.balance || 0).toLocaleString()} PKR</strong></div>
          </div>
        </Panel>
      </div>

      <Panel title="Wallet activity" subtitle="Every debit and credit is linked to an immutable transaction reference">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Reference</th><th>Type</th><th>Direction</th><th>Amount</th><th>Balance after</th><th>Status</th><th>Time</th></tr></thead>
            <tbody>
              {activity.length ? activity.map((item) => (
                <tr key={item.ledger_entry_id}>
                  <td className="mono">{item.reference}</td>
                  <td>{item.transaction_type.replaceAll("_", " ")}</td>
                  <td><StatusBadge value={item.entry_type} /></td>
                  <td>{Number(item.amount).toLocaleString()} PKR</td>
                  <td>{Number(item.balance_after).toLocaleString()} PKR</td>
                  <td><StatusBadge value={item.status} /></td>
                  <td>{new Date(item.created_at).toLocaleString()}</td>
                </tr>
              )) : <tr><td colSpan={7} className="empty-state">No wallet activity yet. Make your first simulated payment.</td></tr>}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Merchant account application" subtitle="Create a simulated merchant profile and settlement wallet">
        <form className="inline-form" onSubmit={applyMerchant}>
          <label>Business name<input value={merchantName} onChange={(e) => setMerchantName(e.target.value)} required minLength={2} placeholder="Example Store" /></label>
          <button className="primary-button">Submit application</button>
        </form>
      </Panel>
    </>
  );
}
