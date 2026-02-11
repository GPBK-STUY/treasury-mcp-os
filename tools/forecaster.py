"""Cash Flow Forecaster — projects future cash position from historical patterns."""
import os
from datetime import datetime
import pandas as pd
from models import CashFlowProjection, CashFlowForecast


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

    # Calculate weekly averages by category
    inflow_cats = ["ar_collection", "revenue"]
    inflows = txn_df[txn_df["category"].isin(inflow_cats)]["amount"].sum()
    avg_weekly_in = abs(inflows) / num_weeks

    outflows = txn_df[~txn_df["category"].isin(inflow_cats)]["amount"].sum()
    avg_weekly_out = abs(outflows) / num_weeks

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

    if deficit:
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
