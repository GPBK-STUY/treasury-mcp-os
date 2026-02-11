"""Payment Timing Optimizer — identifies early-payment discount opportunities."""
import os
import re
import pandas as pd
from models import PaymentRecommendation, PaymentOptimizationReport


def optimize_payment_timing(data_dir: str, available_cash: float = 0.0) -> dict:
    """Analyze vendor terms and recommend early-payment discounts."""
    df = pd.read_csv(os.path.join(data_dir, "vendors.csv"))
    recommendations = []
    total_discounts = 0.0
    total_early_spend = 0.0

    for _, row in df.iterrows():
        raw = row.get("discount_terms", "")
        if pd.isna(raw) or not str(raw).strip():
            continue
        terms = str(raw).strip()

        match = re.match(r"(\d+\.?\d*)/(\d+)\s+net\s+(\d+)", terms, re.IGNORECASE)
        if not match:
            continue

        disc_pct = float(match.group(1))
        disc_days = int(match.group(2))
        net_days = int(match.group(3))
        amount = float(row["outstanding_amount"])
        days_accel = net_days - disc_days

        if days_accel <= 0 or amount <= 0:
            continue

        discount_amt = round(amount * disc_pct / 100, 2)
        ann_return = round((disc_pct / (100 - disc_pct)) * (365 / days_accel) * 100, 2)
        rec_type = "pay_early" if ann_return > 10 else "hold"

        reasoning = (f"Taking {disc_pct}% discount by paying {days_accel} days early "
                     f"yields {ann_return:.1f}% annualized return, "
                     f"{'well above' if rec_type == 'pay_early' else 'below'} "
                     f"10% cost of capital threshold.")

        recommendations.append(PaymentRecommendation(
            vendor_name=str(row["vendor_name"]),
            invoice_amount=amount,
            due_date=str(row.get("due_date", "")),
            discount_terms=terms,
            discount_amount=discount_amt,
            annualized_return_pct=ann_return,
            recommendation=rec_type,
            reasoning=reasoning,
        ))
        total_discounts += discount_amt
        if rec_type == "pay_early":
            total_early_spend += amount

    recommendations.sort(key=lambda x: x.annualized_return_pct, reverse=True)

    return PaymentOptimizationReport(
        recommendations=recommendations,
        total_discount_available=round(total_discounts, 2),
        total_annualized_savings=round(total_discounts * 12, 2),
        cash_required_for_early_payments=round(total_early_spend, 2),
    ).model_dump()
