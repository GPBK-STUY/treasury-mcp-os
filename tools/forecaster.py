"""Cash Flow Forecaster — projects future cash position from historical patterns."""
import os
from datetime import datetime
import pandas as pd
from models import CashFlowProjection, CashFlowForecast

# Guardrail thresholds (per CLAUDE.md)
_RUNWAY_URGENT_DAYS = 90   # escalate urgency
_RUNWAY_CRITICAL_DAYS = 30  # immediate action


def forecast_cash_position(data_dir: str, horizon_days: int = 90) -> dict:
    """Forecast cash position using historical transaction patterns."""
    txn_df = pd.read_csv(os.path.join(data_dir, "transactions.csv"))
    acct_df = pd.read_csv(os.path.join(data_dir, "accounts.csv"))

    # Current balance from checking accounts (operating accounts)
    checking = acct_df[acct_df["account_type"] == "checking"]
    current_balance = checking["balance"].sum()

    # Parse dates and calculate historical period
    txn_df["date"] = pd.to_datetime(txn_df["date"])
    date_range = (txn_df["date"].max() - txn_df["date"].min()).days
    num_weeks = max(1, date_range / 7)

    # Calculate weekly averages.
    # Sign convention: inflow categories carry positive amounts in the data;
    # outflow categories (payroll, ap_payment, etc.) carry negative amounts.
    inflow_cats = ["ar_collection", "revenue"]
    inflows = txn_df[txn_df["category"].isin(inflow_cats)]["amount"].sum()
    avg_weekly_in = inflows / num_weeks  # positive by convention

    outflows = txn_df[~txn_df["category"].isin(inflow_cats)]["amount"].sum()
    avg_weekly_out = abs(outflows) / num_weeks  # abs() converts negative sign to positive magnitude

    # Project forward
    num_periods = max(1, horizon_days // 7)
    projections = []
    balance = current_balance

    for week in range(1, num_periods + 1):
        starting = balance
        net = avg_weekly_in - avg_weekly_out
        ending = round(starting + net, 2)

        if week <= 4:
            confidence = "high"
        elif week <= 8:
            confidence = "medium"
        else:
            confidence = "low"

        projections.append(CashFlowProjection(
            period=f"Week {week}",
            starting_balance=round(starting, 2),
            expected_inflows=round(avg_weekly_in, 2),
            expected_outflows=round(avg_weekly_out, 2),
            net_flow=round(net, 2),
            ending_balance=ending,
            confidence=confidence,
        ))
        balance = ending

    surplus_thresh = current_balance * 1.20
    deficit_thresh = current_balance * 0.80
    surplus = [p.period for p in projections if p.ending_balance > surplus_thresh]
    deficit = [p.period for p in projections if p.ending_balance < deficit_thresh]

    # Runway detection: find first week where ending balance goes to zero or negative.
    # Flag per CLAUDE.md guardrails (< 30d = immediate action, < 90d = escalate).
    first_zero_week = next(
        (p for p in projections if p.ending_balance <= 0), None
    )
    days_to_zero = (projections.index(first_zero_week) + 1) * 7 if first_zero_week else None

    if days_to_zero is not None and days_to_zero <= _RUNWAY_CRITICAL_DAYS:
        rec = (f"IMMEDIATE ACTION REQUIRED: Balance projected to reach zero in "
               f"~{days_to_zero} days ({first_zero_week.period}). "
               f"Activate credit facility or emergency cash measures now.")
    elif days_to_zero is not None and days_to_zero <= _RUNWAY_URGENT_DAYS:
        rec = (f"ESCALATE: Balance projected to reach zero in "
               f"~{days_to_zero} days ({first_zero_week.period}). "
               f"Engage credit facility within 30 days.")
    elif deficit:
        rec = f"Cash deficit expected in {deficit}. Consider credit facility or accelerate collections."
    elif surplus:
        rec = f"Cash surplus expected in {surplus}. Consider deploying to higher-yield instruments."
    else:
        rec = "Cash position stable. Continue normal treasury operations."

    return CashFlowForecast(
        forecast_horizon_days=horizon_days,
        projections=projections,
        surplus_periods=surplus,
        deficit_periods=deficit,
        recommendation=rec,
    ).model_dump()
