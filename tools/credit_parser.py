"""Credit Report Parser — extracts and structures personal + business credit data
already on file from the loan application process."""
import os
from datetime import datetime
import pandas as pd
from models import (
    PersonalCreditProfile,
    BusinessCreditProfile,
    CreditReportSummary,
)


def _score_tier(score: int) -> str:
    """Map FICO score to tier label."""
    if score >= 750:
        return "excellent"
    elif score >= 700:
        return "good"
    elif score >= 650:
        return "fair"
    elif score >= 580:
        return "poor"
    return "very_poor"


def _paydex_tier(score: int) -> str:
    """Map D&B Paydex score to risk tier."""
    if score >= 80:
        return "low_risk"
    elif score >= 50:
        return "moderate_risk"
    return "high_risk"


def parse_credit_report(data_dir: str) -> dict:
    """Parse personal and business credit reports from institution files.

    Reads personal_credit.csv and business_credit.csv from the data directory.
    These represent credit reports already pulled during the application process.
    """
    personal_path = os.path.join(data_dir, "personal_credit.csv")
    business_path = os.path.join(data_dir, "business_credit.csv")

    # ── Parse Personal Credit ──────────────────────────────────────
    personal_profiles = []
    if os.path.exists(personal_path):
        df = pd.read_csv(personal_path)
        for _, row in df.iterrows():
            score = int(row["credit_score"])
            personal_profiles.append(PersonalCreditProfile(
                borrower_name=str(row["borrower_name"]),
                credit_score=score,
                score_model=str(row.get("score_model", "FICO 8")),
                report_date=str(row["report_date"]),
                total_tradelines=int(row["total_tradelines"]),
                open_tradelines=int(row["open_tradelines"]),
                revolving_utilization_pct=round(float(row["revolving_utilization_pct"]), 1),
                total_revolving_balance=float(row["total_revolving_balance"]),
                total_revolving_limit=float(row["total_revolving_limit"]),
                total_installment_balance=float(row["total_installment_balance"]),
                monthly_installment_payments=float(row["monthly_installment_payments"]),
                derogatory_marks=int(row.get("derogatory_marks", 0)),
                collections=int(row.get("collections", 0)),
                public_records=int(row.get("public_records", 0)),
                late_payments_30d=int(row.get("late_payments_30d", 0)),
                late_payments_60d=int(row.get("late_payments_60d", 0)),
                late_payments_90d=int(row.get("late_payments_90d", 0)),
                payment_history_pct=round(float(row.get("payment_history_pct", 100.0)), 1),
                oldest_account_years=round(float(row.get("oldest_account_years", 0)), 1),
                recent_inquiries_6mo=int(row.get("recent_inquiries_6mo", 0)),
                bankruptcies=int(row.get("bankruptcies", 0)),
                foreclosures=int(row.get("foreclosures", 0)),
                tax_liens=int(row.get("tax_liens", 0)),
                score_tier=_score_tier(score),
            ))

    # ── Parse Business Credit ──────────────────────────────────────
    business_profile = None
    if os.path.exists(business_path):
        df = pd.read_csv(business_path)
        if len(df) > 0:
            row = df.iloc[0]
            paydex = int(row["paydex_score"])
            intelliscore_raw = row.get("intelliscore", None)
            intelliscore = int(intelliscore_raw) if pd.notna(intelliscore_raw) else None

            business_profile = BusinessCreditProfile(
                business_name=str(row["business_name"]),
                report_date=str(row["report_date"]),
                paydex_score=paydex,
                intelliscore=intelliscore,
                years_in_business=float(row["years_in_business"]),
                industry=str(row.get("industry", "")),
                total_trade_experiences=int(row["total_trade_experiences"]),
                current_pct=round(float(row["current_pct"]), 1),
                days_beyond_terms_avg=round(float(row["days_beyond_terms_avg"]), 1),
                high_credit=float(row["high_credit"]),
                total_balance_outstanding=float(row["total_balance_outstanding"]),
                payment_trend=str(row.get("payment_trend", "stable")),
                derogatory_count=int(row.get("derogatory_count", 0)),
                liens=int(row.get("liens", 0)),
                judgments=int(row.get("judgments", 0)),
                ucc_filings=int(row.get("ucc_filings", 0)),
                bankruptcy_flag=str(row.get("bankruptcy_flag", "false")).lower() == "true",
                d_and_b_rating=str(row.get("d_and_b_rating", "")),
                paydex_tier=_paydex_tier(paydex),
            )

    if not personal_profiles and business_profile is None:
        raise FileNotFoundError(
            f"No credit report files found in {data_dir}. "
            "Expected personal_credit.csv and/or business_credit.csv."
        )

    report = CreditReportSummary(
        personal_profiles=personal_profiles,
        business_profile=business_profile,
        report_date=datetime.now().isoformat(),
    )
    return report.model_dump()
