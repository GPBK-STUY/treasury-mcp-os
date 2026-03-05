"""Working Capital Gap Analyzer — evaluates liquidity and operational efficiency."""
from models import WorkingCapitalMetrics

# Guardrail thresholds (per CLAUDE.md)
_MIN_CURRENT_RATIO = 1.20    # flag below this; < 1.0 = negative working capital
_MAX_CCC_DAYS = 60           # cash conversion cycle stress threshold
_RUNWAY_URGENT_DAYS = 90     # escalate urgency
_RUNWAY_CRITICAL_DAYS = 30   # immediate action


def analyze_working_capital(current_assets: float, current_liabilities: float,
                            annual_revenue: float, accounts_receivable: float,
                            accounts_payable: float, annual_cogs: float) -> dict:
    """Calculate working capital metrics and health assessment."""
    nwc = current_assets - current_liabilities
    ratio = current_assets / current_liabilities if current_liabilities > 0 else float("inf")
    dso = (accounts_receivable / annual_revenue) * 365 if annual_revenue > 0 else 0
    dpo = (accounts_payable / annual_cogs) * 365 if annual_cogs > 0 else 0
    ccc = dso - dpo
    # Daily burn: COGS + estimated non-COGS opex (assumed 15% of revenue as proxy)
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

    # ── Guardrail checks (per CLAUDE.md) ──────────────────────────
    warnings = []

    if ratio < 1.0:
        warnings.append(
            f"CRITICAL: Current ratio {ratio:.2f}x — negative working capital. Immediate action required."
        )
    elif ratio < _MIN_CURRENT_RATIO:
        warnings.append(
            f"FLAG: Current ratio {ratio:.2f}x is below the {_MIN_CURRENT_RATIO}x minimum threshold. Monitor closely."
        )

    if ccc > _MAX_CCC_DAYS:
        warnings.append(
            f"FLAG: Cash conversion cycle {ccc:.0f} days exceeds {_MAX_CCC_DAYS}-day threshold — working capital stress."
        )

    if runway != float("inf"):
        if runway < _RUNWAY_CRITICAL_DAYS:
            warnings.append(
                f"IMMEDIATE ACTION: Runway {runway:.0f} days — below {_RUNWAY_CRITICAL_DAYS}-day critical threshold."
            )
        elif runway < _RUNWAY_URGENT_DAYS:
            warnings.append(
                f"ESCALATE: Runway {runway:.0f} days — below {_RUNWAY_URGENT_DAYS}-day urgency threshold."
            )

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
        guardrail_warnings=warnings,
    ).model_dump()
