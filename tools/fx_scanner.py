"""FX Exposure Scanner — identifies and quantifies foreign currency risk."""
import math
import os
from datetime import datetime
import pandas as pd
from models import FXExposure, FXExposureReport


def scan_fx_exposure(data_dir: str) -> dict:
    """Scan vendor payables for unhedged FX exposures."""
    vendors_df = pd.read_csv(os.path.join(data_dir, "vendors.csv"))
    fx_df = pd.read_csv(os.path.join(data_dir, "fx_rates.csv"))

    # Build rate lookup: currency -> USD multiplier
    fx_to_usd = {}
    for _, row in fx_df.iterrows():
        pair = str(row["currency_pair"]).strip()
        rate = float(row["rate"])
        if "/" not in pair:
            continue
        base, quote = pair.split("/")
        if quote == "USD":
            fx_to_usd[base] = rate      # EUR/USD=1.08 -> 1 EUR = 1.08 USD
        elif base == "USD":
            fx_to_usd[quote] = 1.0/rate  # USD/JPY=149 -> 1 JPY = 1/149 USD

    ref_date = datetime(2026, 2, 8)
    exposures = []
    total_unhedged = 0.0
    total_var = 0.0
    by_currency = {}

    for _, row in vendors_df.iterrows():
        ccy = str(row.get("currency", "USD")).upper().strip()
        if ccy == "USD":
            continue
        amount = float(row.get("outstanding_amount", 0))
        if amount <= 0 or ccy not in fx_to_usd:
            continue

        usd_eq = round(amount * fx_to_usd[ccy], 2)
        try:
            due = datetime.strptime(str(row["due_date"]), "%Y-%m-%d")
            days = max(1, (due - ref_date).days)
        except (ValueError, TypeError):
            days = 30

        var = round(usd_eq * 0.05 * math.sqrt(days / 365), 2)

        exposures.append(FXExposure(
            currency=ccy, exposure_type="payable", notional_amount=amount,
            usd_equivalent=usd_eq, hedge_status="unhedged",
            days_to_settlement=days, estimated_var_usd=var,
        ))
        total_unhedged += usd_eq
        total_var += var
        by_currency[ccy] = by_currency.get(ccy, 0) + usd_eq

    largest = max(by_currency, key=by_currency.get) if by_currency else ""

    if total_unhedged == 0:
        rec = "No foreign currency exposures detected."
    elif total_unhedged < 100000:
        rec = f"Minimal FX exposure (${total_unhedged:,.2f}). Natural hedging may suffice."
    else:
        rec = (f"Significant FX exposure (${total_unhedged:,.2f}, ${total_var:,.2f} VaR). "
               f"Recommend hedging program. Largest: {largest}.")

    return FXExposureReport(
        exposures=exposures, total_unhedged_usd=round(total_unhedged, 2),
        total_var_usd=round(total_var, 2),
        largest_single_exposure_currency=largest, recommendation=rec,
    ).model_dump()
