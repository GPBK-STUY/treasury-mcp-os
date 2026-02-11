"""Working Capital Gap Analyzer — evaluates liquidity and operational efficiency."""
from models import WorkingCapitalMetrics


def analyze_working_capital(current_assets: float, current_liabilities: float,
                            annual_revenue: float, accounts_receivable: float,
                            accounts_payable: float, annual_cogs: float) -> dict:
    """Calculate working capital metrics and health assessment."""
    nwc = current_assets - current_liabilities
    ratio = current_assets / current_liabilities if current_liabilities > 0 else float("inf")
    dso = (accounts_receivable / annual_revenue) * 365 if annual_revenue > 0 else 0
    dpo = (accounts_payable / annual_cogs) * 365 if annual_cogs > 0 else 0
    ccc = dso - dpo
    daily_burn = (annual_cogs + (annual_revenue * 0.15)) / 365
    runway = nwc / daily_burn if daily_burn > 0 else float("inf")

    if ratio >= 2.0:
        assessment = "Strong - well capitalized with comfortable liquidity cushion"
    elif ratio >= 1.5:
        assessment = "Healthy - adequate working capital for operations"
    elif ratio >= 1.2:
        assessment = "Adequate - monitor closely, limited buffer"
    elif ratio >= 1.0:
        assessment = "Tight - working capital under pressure, consider credit facility"
    else:
        assessment = "Critical - negative working capital, immediate action required"

    return WorkingCapitalMetrics(
        current_assets=round(current_assets, 2),
        current_liabilities=round(current_liabilities, 2),
        net_working_capital=round(nwc, 2),
        current_ratio=round(ratio, 2),
        days_sales_outstanding=round(dso, 2),
        days_payable_outstanding=round(dpo, 2),
        cash_conversion_cycle_days=round(ccc, 2),
        daily_burn_rate=round(daily_burn, 2),
        runway_days=round(runway, 2),
        assessment=assessment,
    ).model_dump()
