export type UserRole = "customer" | "merchant" | "analyst" | "executive" | "admin";

export interface User {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Wallet {
  id: string;
  balance: string | number;
  currency: string;
  status: string;
  owner_type: string;
  created_at: string;
}

export interface Transaction {
  id: string;
  reference: string;
  sender_wallet_id?: string | null;
  receiver_wallet_id?: string | null;
  amount: string | number;
  currency: string;
  transaction_type: string;
  channel: string;
  status: string;
  description?: string | null;
  risk_score?: string | number | null;
  created_at: string;
}

export interface FraudAlert {
  id: string;
  transaction_id: string;
  transaction_reference: string;
  risk_score: string | number;
  confidence: string | number;
  risk_band: string;
  status: string;
  reasons: string[];
  created_at: string;
}

export interface ExecutiveDashboard {
  active_customers: number;
  digital_wallets: number;
  active_merchants: number;
  payment_count: number;
  payment_volume: string | number;
  open_fraud_alerts: number;
  high_risk_alerts: number;
  api_calls: number;
  cbdc_wallets: number;
  cbdc_volume: string | number;
  payment_success_rate: number;
  trends: Array<{ date: string; payments: number; volume: string | number }>;
}
