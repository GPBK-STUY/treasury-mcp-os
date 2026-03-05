"""Idle Cash Scanner — identifies yield optimization opportunities."""
import os
import pandas as pd
from models import IdleCashOpportunity, IdleCashReport


def scan_idle_balances(data_dir: str, operating_reserve_pct: float = 0.20,
                       target_yield_bps: int = 450) -> dict:
    """Scan accounts for idle cash that could earn higher yields."""
    # Guardrail: never deploy below 20% operating reserve (per CLAUDE.md)
    if operating_reserve_pct < 0.20:
        raise ValueError(
            f"operating_reserve_pct={operating_reserve_pct:.0%} violates the minimum 20% "
            f"operating reserve guardrail. Pass at least 0.20 to protect operating liquidity."
        )

    df = pd.read_csv(os.path.join(data_dir, "accounts.csv"))
    opportunities = []

    for _, row in df.iterrows():
        acct_type = str(row["account_type"]).lower()
        if acct_type not in ("checking", "savings"):
            continue

        balance = float(row["balance"])
        current_yield = int(row.get("yield_rate_bps", 0))
        reserve = round(balance * operating_reserve_pct, 2)
        idle = round(balance - reserve, 2)

        if idle <= 50000:
            continue

        cost = round(idle * (target_yield_bps - current_yield) / 10000, 2)
        action = ("Move to money market or high-yield sweep account"
                  if current_yield == 0
                  else "Consider moving to higher-yield instrument")

        opportunities.append(IdleCashOpportunity(
            account_id=str(row["account_id"]),
            bank_name=str(row["bank_name"]),
            current_balance=balance,
            operating_reserve_needed=reserve,
            idle_amount=idle,
            current_yield_bps=current_yield,
            recommended_yield_bps=target_yield_bps,
            annual_opportunity_cost=cost,
            recommended_action=action,
        ))

    report = IdleCashReport(
        total_idle_cash=round(sum(o.idle_amount for o in opportunities), 2),
        total_annual_opportunity_cost=round(sum(o.annual_opportunity_cost for o in opportunities), 2),
        opportunities=opportunities,
    )
    return report.model_dump()
