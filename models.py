"""Pydantic models for Treasury Management MCP Server."""
from __future__ import annotations
from typing import Dict, List, Optional
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


# ── Credit Report Models ──────────────────────────────────────────────

class PersonalCreditProfile(BaseModel):
    """Parsed personal credit report for a guarantor."""
    borrower_name: str = Field(..., description="Guarantor full name")
    credit_score: int = Field(..., description="FICO or VantageScore")
    score_model: str = Field(..., description="Score model (e.g. FICO 8)")
    report_date: str = Field(..., description="Date credit was pulled")
    total_tradelines: int = Field(..., description="Total trade lines on file")
    open_tradelines: int = Field(..., description="Currently open trade lines")
    revolving_utilization_pct: float = Field(..., description="Revolving utilization %")
    total_revolving_balance: float = Field(..., description="Total revolving balances")
    total_revolving_limit: float = Field(..., description="Total revolving limits")
    total_installment_balance: float = Field(..., description="Total installment balances")
    monthly_installment_payments: float = Field(..., description="Monthly installment payment total")
    derogatory_marks: int = Field(..., description="Derogatory marks count")
    collections: int = Field(..., description="Collections count")
    public_records: int = Field(..., description="Public records count")
    late_payments_30d: int = Field(..., description="30-day late payments")
    late_payments_60d: int = Field(..., description="60-day late payments")
    late_payments_90d: int = Field(..., description="90+ day late payments")
    payment_history_pct: float = Field(..., description="On-time payment percentage")
    oldest_account_years: float = Field(..., description="Age of oldest account in years")
    recent_inquiries_6mo: int = Field(..., description="Hard inquiries in last 6 months")
    bankruptcies: int = Field(..., description="Bankruptcy filings")
    foreclosures: int = Field(..., description="Foreclosures")
    tax_liens: int = Field(..., description="Tax liens")
    score_tier: str = Field(..., description="excellent, good, fair, poor, or very_poor")


class BusinessCreditProfile(BaseModel):
    """Parsed business credit report."""
    business_name: str = Field(..., description="Legal business name")
    report_date: str = Field(..., description="Date report was pulled")
    paydex_score: int = Field(..., description="D&B Paydex score (0-100)")
    intelliscore: Optional[int] = Field(None, description="Experian Intelliscore (1-100)")
    years_in_business: float = Field(..., description="Years in operation")
    industry: str = Field(..., description="Industry classification")
    total_trade_experiences: int = Field(..., description="Total trade references")
    current_pct: float = Field(..., description="Percent of trades paid current")
    days_beyond_terms_avg: float = Field(..., description="Avg days beyond payment terms")
    high_credit: float = Field(..., description="Highest credit extended")
    total_balance_outstanding: float = Field(..., description="Total outstanding balance")
    payment_trend: str = Field(..., description="improving, stable, or declining")
    derogatory_count: int = Field(..., description="Derogatory trade experiences")
    liens: int = Field(..., description="UCC liens or tax liens")
    judgments: int = Field(..., description="Judgments on file")
    ucc_filings: int = Field(..., description="UCC filings count")
    bankruptcy_flag: bool = Field(..., description="Bankruptcy on file")
    d_and_b_rating: str = Field(..., description="D&B credit rating (e.g. 3A2)")
    paydex_tier: str = Field(..., description="low_risk, moderate_risk, or high_risk")


class CreditReportSummary(BaseModel):
    """Combined personal + business credit report output."""
    personal_profiles: List[PersonalCreditProfile] = Field(..., description="Guarantor credit profiles")
    business_profile: Optional[BusinessCreditProfile] = Field(None, description="Business credit profile")
    report_date: str = Field(..., description="Analysis timestamp")


class CreditRiskFactor(BaseModel):
    """Individual risk or opportunity identified in credit analysis."""
    category: str = Field(..., description="credit_score, utilization, payment_history, etc.")
    severity: str = Field(..., description="positive, neutral, watch, concern, or critical")
    finding: str = Field(..., description="What was found")
    impact: str = Field(..., description="How this affects lending decisions")
    recommendation: str = Field(..., description="Specific action to take")


class CreditPositionAssessment(BaseModel):
    """Integrated credit + cash flow lending readiness assessment."""
    business_name: str = Field(..., description="Business name")
    assessment_date: str = Field(..., description="Assessment timestamp")
    overall_credit_rating: str = Field(..., description="strong, acceptable, marginal, weak, or adverse")
    personal_score_avg: float = Field(..., description="Average guarantor FICO score")
    personal_score_lowest: int = Field(..., description="Lowest guarantor score")
    business_paydex: Optional[int] = Field(None, description="Business Paydex score")
    combined_debt_to_income: Optional[float] = Field(None, description="Combined personal DTI ratio")
    personal_guaranty_strength: str = Field(..., description="strong, adequate, weak, or insufficient")
    risk_factors: List[CreditRiskFactor] = Field(..., description="Identified risks and opportunities")
    lending_capacity_estimate: str = Field(..., description="Estimated borrowing capacity range")
    cross_sell_opportunities: List[str] = Field(..., description="Product recommendations based on credit profile")
    recommendation: str = Field(..., description="Overall recommendation for the relationship")
