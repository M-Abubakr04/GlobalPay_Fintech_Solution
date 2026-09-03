from decimal import Decimal

from pydantic import BaseModel


class TrendPoint(BaseModel):
    date: str
    payments: int
    volume: Decimal


class ExecutiveDashboardOut(BaseModel):
    active_customers: int
    digital_wallets: int
    active_merchants: int
    payment_count: int
    payment_volume: Decimal
    open_fraud_alerts: int
    high_risk_alerts: int
    api_calls: int
    cbdc_wallets: int
    cbdc_volume: Decimal
    payment_success_rate: float
    trends: list[TrendPoint]
