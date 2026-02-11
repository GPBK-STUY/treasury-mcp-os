"""Pydantic models for Treasury Management MCP Server."""
from __future__ import annotations
from typing import Dict, List
from pydantic import BaseModel, Field


class AccountPosition(BaseModel):
    """Single account position."""
    account_id: str = Field(..., description="Unique account identifier")
    bank_name: str = Field(..., description="Financial institution name")
    account_type: str = Field(..., description="checking, savings, money_market, or cd")
    currency: str = Field(..., description="ISO currency code")
    balance: float = Field(..., description="Current balance")
    yield_rate_bps: int = Field(..., description="Annual yield in basis points")
    last_updated: str = Field(..., description="Last update timestamp")


class CashPositionReport(BaseModel):
    """Aggregated cash position across all accounts."""
    total_balance: float = Field(..., description="Total balance")
    by_currency: Dict[str, float] = Field(..., description="Balance by currency")
    by_account_type: Dict[str, float] = Field(..., description="Balance by account type")
    accounts: List[AccountPosition] = Field(..., description="Individual positions")
    as_of: str = Field(..., description="Report timestamp")


class IdleCashOpportunity(BaseModel):
    """Single idle cash optimization opportunity."""
    account_id: str = Field(..., description="Account identifier")
    bank_name: str = Field(..., description="Financial institution")
    current_balance: float = Field(..., description="Current balance")
    operating_reserve_needed: float = Field(..., description="Required reserve")
    idle_amount: float = Field(..., description="Deployable amount")
    current_yield_bps: int = Field(..., description="Current yield bps")
    recommended_yield_bps: int = Field(..., description="Target yield bps")
    annual_opportunity_cost: float = Field(..., description="Annual cost of inaction")
    recommended_action: str = Field(..., description="Suggested action")


class IdleCashReport(BaseModel):
    """Summary of idle cash opportunities."""
    total_idle_cash: float = Field(..., description="Total idle cash")
    total_annual_opportunity_cost: float = Field(..., description="Total annual cost")
    opportunities: List[IdleCashOpportunity] = Field(..., description="Opportunities")


class CashFlowProjection(BaseModel):
    """Single period cash flow projection."""
    period: str = Field(..., description="Period identifier")
    starting_balance: float = Field(..., description="Opening balance")
    expected_inflows: float = Field(..., description="Projected inflows")
    expected_outflows: float = Field(..., description="Projected outflows")
    net_flow: float = Field(..., description="Net cash flow")
    ending_balance: float = Field(..., description="Closing balance")
    confidence: str = Field(..., description="high, medium, or low")


class CashFlowForecast(BaseModel):
    """Complete cash flow forecast."""
    forecast_horizon_days: int = Field(..., description="Forecast horizon in days")
    projections: List[CashFlowProjection] = Field(..., description="Period projections")
    surplus_periods: List[str] = Field(..., description="Surplus periods")
    deficit_periods: List[str] = Field(..., description="Deficit periods")
    recommendation: str = Field(..., description="Recommended actions")


class WorkingCapitalMetrics(BaseModel):
    """Working capital and liquidity metrics."""
    current_assets: float = Field(..., description="Total current assets")
    current_liabilities: float = Field(..., description="Total current liabilities")
    net_working_capital: float = Field(..., description="Net working capital")
    current_ratio: float = Field(..., description="Current ratio")
    days_sales_outstanding: float = Field(..., description="DSO")
    days_payable_outstanding: float = Field(..., description="DPO")
    cash_conversion_cycle_days: float = Field(..., description="CCC in days")
    daily_burn_rate: float = Field(..., description="Daily cash burn")
    runway_days: float = Field(..., description="Days of runway")
    assessment: str = Field(..., description="Health assessment")


class PaymentRecommendation(BaseModel):
    """Single payment optimization recommendation."""
    vendor_name: str = Field(..., description="Vendor name")
    invoice_amount: float = Field(..., description="Invoice amount")
    due_date: str = Field(..., description="Due date")
    discount_terms: str = Field(..., description="e.g. 2/10 net 30")
    discount_amount: float = Field(..., description="Dollar discount")
    annualized_return_pct: float = Field(..., description="Annualized return %")
    recommendation: str = Field(..., description="pay_early or hold")
    reasoning: str = Field(..., description="Explanation")


class PaymentOptimizationReport(BaseModel):
    """Payment optimization summary."""
    recommendations: List[PaymentRecommendation] = Field(..., description="Recommendations")
    total_discount_available: float = Field(..., description="Total discounts")
    total_annualized_savings: float = Field(..., description="Total annualized savings")
    cash_required_for_early_payments: float = Field(..., description="Cash needed")


class FXExposure(BaseModel):
    """Single FX exposure."""
    currency: str = Field(..., description="ISO currency code")
    exposure_type: str = Field(..., description="receivable or payable")
    notional_amount: float = Field(..., description="Foreign currency amount")
    usd_equivalent: float = Field(..., description="USD equivalent")
    hedge_status: str = Field(..., description="hedged, unhedged, or partial")
    days_to_settlement: int = Field(..., description="Days to settlement")
    estimated_var_usd: float = Field(..., description="Value at Risk USD")


class FXExposureReport(BaseModel):
    """FX exposure summary."""
    exposures: List[FXExposure] = Field(..., description="Exposures")
    total_unhedged_usd: float = Field(..., description="Total unhedged USD")
    total_var_usd: float = Field(..., description="Total VaR USD")
    largest_single_exposure_currency: str = Field(..., description="Largest currency")
    recommendation: str = Field(..., description="Hedging recommendation")


class CovenantStatus(BaseModel):
    """Single covenant status."""
    covenant_name: str = Field(..., description="Covenant name")
    covenant_type: str = Field(..., description="Covenant type")
    required_threshold: float = Field(..., description="Required threshold")
    current_value: float = Field(..., description="Current value")
    headroom_pct: float = Field(..., description="Headroom percentage")
    status: str = Field(..., description="compliant, warning, or breach")
    next_test_date: str = Field(..., description="Next test date")


class CovenantReport(BaseModel):
    """Covenant compliance summary."""
    covenants: List[CovenantStatus] = Field(..., description="Covenant statuses")
    overall_status: str = Field(..., description="Overall status")
    breaches: int = Field(..., description="Number of breaches")
    warnings: int = Field(..., description="Number of warnings")
    recommendation: str = Field(..., description="Recommended actions")
