"""Cash Position Aggregator — foundational tool for all treasury operations."""
import os
from datetime import datetime
import pandas as pd
from models import AccountPosition, CashPositionReport


def get_cash_position(data_dir: str) -> dict:
    """Aggregate cash positions across all bank accounts."""
    accounts_path = os.path.join(data_dir, "accounts.csv")
    if not os.path.exists(accounts_path):
        raise FileNotFoundError(f"accounts.csv not found at {accounts_path}")

    df = pd.read_csv(accounts_path)
    positions = []
    for _, row in df.iterrows():
        positions.append(AccountPosition(
            account_id=str(row["account_id"]),
            bank_name=str(row.get("bank_name", "Unknown")),
            account_type=str(row["account_type"]),
            currency=str(row["currency"]),
            balance=float(row["balance"]),
            yield_rate_bps=int(row.get("yield_rate_bps", 0)),
            last_updated=str(row.get("last_updated", "")),
        ))

    by_currency = df.groupby("currency")["balance"].sum().to_dict()
    by_account_type = df.groupby("account_type")["balance"].sum().to_dict()

    report = CashPositionReport(
        total_balance=df["balance"].sum(),
        by_currency=by_currency,
        by_account_type=by_account_type,
        accounts=positions,
        as_of=datetime.now().isoformat(),
    )
    return report.model_dump()
