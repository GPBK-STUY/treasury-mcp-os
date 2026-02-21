"""Credit Position Assessor — integrates credit report data with treasury tools
to produce a lending readiness assessment.

This is the bridge between credit and cash flow. It reads credit data already
on file from the application process and combines it with cash position,
covenant status, and working capital metrics to give the RM a complete picture."""
import os
from datetime import datetime
import pandas as pd
from models import (
    CreditRiskFactor,
    CreditPositionAssessment,
)
from tools.credit_parser import parse_credit_report
from tools.aggregator import get_cash_position
from tools.covenant_monitor import monitor_debt_covenants


def assess_credit_position(data_dir: str,
                           annual_gross_income: float = 0.0) -> dict:
    """Assess combined credit + cash flow position for lending decisions.

    Uses credit reports already on file plus live treasury data to produce
    an integrated risk and opportunity assessment.

    Args:
        data_dir: Path to client data directory.
        annual_gross_income: Combined guarantor annual gross income (for DTI calc).
                             Pass 0 to skip DTI calculation.
    """
    # ── Pull credit data ───────────────────────────────────────────
    credit = parse_credit_report(data_dir)
    personals = credit.get("personal_profiles", [])
    business = credit.get("business_profile", None)

    # ── Pull cash and covenant data (existing tools) ───────────────
    try:
        cash = get_cash_position(data_dir)
    except Exception:
        cash = None

    try:
        covenants = monitor_debt_covenants(data_dir)
    except Exception:
        covenants = None

    # ── Analyze personal credit ────────────────────────────────────
    risk_factors = []
    scores = [p["credit_score"] for p in personals]
    avg_score = round(sum(scores) / len(scores), 0) if scores else 0
    lowest_score = min(scores) if scores else 0

    for p in personals:
        name = p["borrower_name"]
        score = p["credit_score"]

        # Score assessment
        if score >= 750:
            risk_factors.append(CreditRiskFactor(
                category="credit_score",
                severity="positive",
                finding=f"{name}: FICO {score} ({p['score_tier']})",
                impact="Qualifies for best available rates and terms",
                recommendation="Leverage strong score in rate negotiations",
            ))
        elif score >= 700:
            risk_factors.append(CreditRiskFactor(
                category="credit_score",
                severity="positive",
                finding=f"{name}: FICO {score} ({p['score_tier']})",
                impact="Qualifies for standard commercial rates",
                recommendation="No action needed — solid credit profile",
            ))
        elif score >= 650:
            risk_factors.append(CreditRiskFactor(
                category="credit_score",
                severity="watch",
                finding=f"{name}: FICO {score} ({p['score_tier']})",
                impact="May require rate premium or additional collateral",
                recommendation="Review derogatory items for remediation opportunities",
            ))
        else:
            risk_factors.append(CreditRiskFactor(
                category="credit_score",
                severity="concern" if score >= 580 else "critical",
                finding=f"{name}: FICO {score} ({p['score_tier']})",
                impact="Significant underwriting challenge — may require co-signer or SBA guarantee",
                recommendation="Discuss credit remediation plan before proceeding with application",
            ))

        # Utilization assessment
        util = p["revolving_utilization_pct"]
        if util > 75:
            savings = round(p["total_revolving_balance"] * 0.30, 2)
            projected_boost = "20-40"
            risk_factors.append(CreditRiskFactor(
                category="utilization",
                severity="concern",
                finding=f"{name}: Revolving utilization at {util}% (${p['total_revolving_balance']:,.0f} / ${p['total_revolving_limit']:,.0f})",
                impact=f"High utilization drags score by an estimated {projected_boost} points",
                recommendation=f"Paying down ~${savings:,.0f} would drop utilization below 50% and likely boost score {projected_boost} points",
            ))
        elif util > 50:
            risk_factors.append(CreditRiskFactor(
                category="utilization",
                severity="watch",
                finding=f"{name}: Revolving utilization at {util}%",
                impact="Moderate utilization — not penalizing heavily but room to improve",
                recommendation="Target below 30% for optimal score impact",
            ))
        elif util <= 30:
            risk_factors.append(CreditRiskFactor(
                category="utilization",
                severity="positive",
                finding=f"{name}: Revolving utilization at {util}%",
                impact="Low utilization signals responsible credit management",
                recommendation="Maintain current utilization levels",
            ))

        # Payment history
        total_lates = p["late_payments_30d"] + p["late_payments_60d"] + p["late_payments_90d"]
        if total_lates > 0:
            severity = "critical" if p["late_payments_90d"] > 0 else ("concern" if p["late_payments_60d"] > 0 else "watch")
            risk_factors.append(CreditRiskFactor(
                category="payment_history",
                severity=severity,
                finding=f"{name}: {total_lates} late payment(s) — {p['late_payments_30d']}x30d, {p['late_payments_60d']}x60d, {p['late_payments_90d']}x90d",
                impact="Late payments remain on bureau for 7 years and signal repayment risk",
                recommendation="Document explanations for underwriting file — medical, dispute, or one-time events carry less weight",
            ))
        elif p["payment_history_pct"] >= 99:
            risk_factors.append(CreditRiskFactor(
                category="payment_history",
                severity="positive",
                finding=f"{name}: {p['payment_history_pct']}% on-time payment history",
                impact="Excellent payment behavior strengthens guaranty",
                recommendation="Highlight in credit memo as mitigating factor",
            ))

        # Derogatory items
        derogs = p["derogatory_marks"] + p["collections"] + p["public_records"]
        if p["bankruptcies"] > 0:
            risk_factors.append(CreditRiskFactor(
                category="derogatory",
                severity="critical",
                finding=f"{name}: Bankruptcy on file",
                impact="Major underwriting red flag — may disqualify from conventional lending",
                recommendation="Verify discharge date and time since filing. Most policies require 2-4 years post-discharge.",
            ))
        elif derogs > 0:
            risk_factors.append(CreditRiskFactor(
                category="derogatory",
                severity="concern",
                finding=f"{name}: {derogs} derogatory item(s) on file",
                impact="Each derogatory item requires explanation in credit memo",
                recommendation="Request written explanations from borrower for underwriting package",
            ))

    # ── DTI calculation ────────────────────────────────────────────
    combined_dti = None
    if annual_gross_income > 0 and personals:
        total_monthly_debt = sum(p["monthly_installment_payments"] for p in personals)
        # Add minimum revolving payments (2% of balance is standard estimate)
        total_monthly_debt += sum(p["total_revolving_balance"] * 0.02 for p in personals)
        monthly_income = annual_gross_income / 12
        combined_dti = round((total_monthly_debt / monthly_income) * 100, 1) if monthly_income > 0 else 0

        if combined_dti > 50:
            risk_factors.append(CreditRiskFactor(
                category="debt_to_income",
                severity="critical",
                finding=f"Combined DTI: {combined_dti}% (${total_monthly_debt:,.0f}/mo debt vs ${monthly_income:,.0f}/mo income)",
                impact="DTI above 50% typically disqualifies for conventional lending",
                recommendation="Explore debt consolidation or require business cash flow as primary repayment source",
            ))
        elif combined_dti > 43:
            risk_factors.append(CreditRiskFactor(
                category="debt_to_income",
                severity="concern",
                finding=f"Combined DTI: {combined_dti}%",
                impact="DTI above 43% limits lending options — may need exception approval",
                recommendation="Document strong business cash flow as compensating factor",
            ))
        elif combined_dti > 36:
            risk_factors.append(CreditRiskFactor(
                category="debt_to_income",
                severity="watch",
                finding=f"Combined DTI: {combined_dti}%",
                impact="DTI is manageable but leaves limited personal capacity for additional debt",
                recommendation="Focus lending structure on business entity rather than personal guaranty",
            ))
        else:
            risk_factors.append(CreditRiskFactor(
                category="debt_to_income",
                severity="positive",
                finding=f"Combined DTI: {combined_dti}%",
                impact="Healthy DTI — strong personal capacity to support guaranty",
                recommendation="Personal guaranty strengthens the credit request",
            ))

    # ── Analyze business credit ────────────────────────────────────
    biz_paydex = None
    if business:
        biz_paydex = business["paydex_score"]

        if biz_paydex >= 80:
            risk_factors.append(CreditRiskFactor(
                category="business_credit",
                severity="positive",
                finding=f"Paydex {biz_paydex} ({business['paydex_tier']}) — {business['current_pct']}% of trades paid current",
                impact="Strong business payment history supports credit request",
                recommendation="Reference in credit memo as primary positive factor",
            ))
        elif biz_paydex >= 50:
            risk_factors.append(CreditRiskFactor(
                category="business_credit",
                severity="watch",
                finding=f"Paydex {biz_paydex} ({business['paydex_tier']}) — averaging {business['days_beyond_terms_avg']} days beyond terms",
                impact="Moderate business payment history — not a red flag but not a strength",
                recommendation="Monitor trade payment trends quarterly",
            ))
        else:
            risk_factors.append(CreditRiskFactor(
                category="business_credit",
                severity="concern",
                finding=f"Paydex {biz_paydex} ({business['paydex_tier']}) — significant payment delays",
                impact="Weak business payment history signals cash flow stress",
                recommendation="Cross-reference with cash flow forecast — is this a timing issue or structural problem?",
            ))

        if business["payment_trend"] == "declining":
            risk_factors.append(CreditRiskFactor(
                category="business_credit",
                severity="concern",
                finding="Business payment trend: DECLINING",
                impact="Deteriorating vendor payments often precede covenant issues",
                recommendation="Review cash flow forecast and working capital position immediately",
            ))

        if business["bankruptcy_flag"]:
            risk_factors.append(CreditRiskFactor(
                category="business_credit",
                severity="critical",
                finding="Business bankruptcy on file",
                impact="Major underwriting obstacle — most institutions require 5+ years post-discharge",
                recommendation="Verify discharge date, review post-bankruptcy financial performance",
            ))

        if business["liens"] > 0 or business["judgments"] > 0:
            risk_factors.append(CreditRiskFactor(
                category="business_credit",
                severity="concern",
                finding=f"Public records: {business['liens']} lien(s), {business['judgments']} judgment(s)",
                impact="Liens and judgments affect collateral priority and signal financial distress",
                recommendation="Verify if liens are satisfied; UCC filings from existing lenders are normal, tax liens are not",
            ))

    # ── Integrate with cash position ───────────────────────────────
    if cash:
        total_cash = cash.get("total_balance", 0)
        if total_cash > 500000:
            risk_factors.append(CreditRiskFactor(
                category="liquidity",
                severity="positive",
                finding=f"Current cash position: ${total_cash:,.0f} across {len(cash.get('accounts', []))} accounts",
                impact="Strong liquidity supports debt service capacity",
                recommendation="Highlight cash reserves as compensating factor in credit memo",
            ))
        elif total_cash > 100000:
            risk_factors.append(CreditRiskFactor(
                category="liquidity",
                severity="neutral",
                finding=f"Current cash position: ${total_cash:,.0f}",
                impact="Adequate liquidity for current operations",
                recommendation="Monitor cash trajectory — ensure reserves don't erode",
            ))
        else:
            risk_factors.append(CreditRiskFactor(
                category="liquidity",
                severity="concern",
                finding=f"Current cash position: ${total_cash:,.0f}",
                impact="Low cash reserves increase repayment risk",
                recommendation="Require minimum cash covenant or cash reserve account",
            ))

    # ── Integrate with covenant status ─────────────────────────────
    if covenants:
        cov_status = covenants.get("overall_status", "")
        warnings = covenants.get("warnings", 0)
        breaches = covenants.get("breaches", 0)

        if breaches > 0:
            risk_factors.append(CreditRiskFactor(
                category="covenant_compliance",
                severity="critical",
                finding=f"Active covenant breach(es): {breaches}",
                impact="Covenant breach may trigger cross-default — new lending is extremely difficult",
                recommendation="Resolve breach before proceeding with any new credit request",
            ))
        elif warnings > 0:
            risk_factors.append(CreditRiskFactor(
                category="covenant_compliance",
                severity="watch",
                finding=f"Covenant warning(s): {warnings} covenant(s) within 10% of threshold",
                impact="Approaching covenant limits constrains additional borrowing capacity",
                recommendation="Structure new facility to avoid pushing covenants into breach",
            ))
        elif cov_status == "compliant":
            risk_factors.append(CreditRiskFactor(
                category="covenant_compliance",
                severity="positive",
                finding="All covenants compliant with comfortable headroom",
                impact="Covenant compliance supports additional lending capacity",
                recommendation="Reference clean covenant history in credit memo",
            ))

    # ── Determine overall rating ───────────────────────────────────
    severity_scores = {"positive": 0, "neutral": 1, "watch": 2, "concern": 3, "critical": 5}
    total_severity = sum(severity_scores.get(rf.severity, 1) for rf in risk_factors)
    num_factors = len(risk_factors) if risk_factors else 1
    avg_severity = total_severity / num_factors

    criticals = sum(1 for rf in risk_factors if rf.severity == "critical")
    concerns = sum(1 for rf in risk_factors if rf.severity == "concern")
    positives = sum(1 for rf in risk_factors if rf.severity == "positive")

    if criticals >= 2 or avg_severity > 3.0:
        overall = "adverse"
    elif criticals >= 1 or avg_severity > 2.5:
        overall = "weak"
    elif concerns >= 2 or avg_severity > 1.8:
        overall = "marginal"
    elif avg_severity > 1.0:
        overall = "acceptable"
    else:
        overall = "strong"

    # ── Personal guaranty strength ─────────────────────────────────
    if lowest_score >= 700 and combined_dti is not None and combined_dti < 36:
        guaranty = "strong"
    elif lowest_score >= 650 and (combined_dti is None or combined_dti < 43):
        guaranty = "adequate"
    elif lowest_score >= 580:
        guaranty = "weak"
    else:
        guaranty = "insufficient"

    # ── Lending capacity estimate ──────────────────────────────────
    if overall == "strong":
        capacity = "$500K-$2M+ depending on collateral and structure"
    elif overall == "acceptable":
        capacity = "$250K-$750K with standard terms and conditions"
    elif overall == "marginal":
        capacity = "$100K-$400K — may require SBA guarantee or additional collateral"
    elif overall == "weak":
        capacity = "Under $150K — limited to secured or SBA-backed structures"
    else:
        capacity = "Not recommended for new credit at this time"

    # ── Cross-sell opportunities ───────────────────────────────────
    cross_sell = []
    if overall in ("strong", "acceptable"):
        if cash and cash.get("total_balance", 0) > 500000:
            cross_sell.append("Treasury management / sweep account (idle cash optimization)")
        if biz_paydex and biz_paydex >= 70:
            cross_sell.append("Revolving line of credit (working capital)")
        if lowest_score >= 700:
            cross_sell.append("Equipment financing (fixed-rate term loan)")
            cross_sell.append("Commercial real estate (owner-occupied)")
        cross_sell.append("Business credit card (build trade references)")
    elif overall == "marginal":
        cross_sell.append("SBA 7(a) loan (government-backed, lower rates)")
        cross_sell.append("Secured business credit card (credit building)")
    else:
        cross_sell.append("Credit remediation advisory")
        cross_sell.append("Secured savings / CD-backed credit builder")

    # ── Build recommendation ───────────────────────────────────────
    if overall == "strong":
        rec = (f"Strong credit profile across personal and business dimensions. "
               f"Average guarantor FICO {avg_score:.0f}, "
               f"{'Paydex ' + str(biz_paydex) + ', ' if biz_paydex else ''}"
               f"clean covenant history. Proceed with standard underwriting. "
               f"Explore cross-sell opportunities to deepen the relationship.")
    elif overall == "acceptable":
        watch_items = [rf.finding for rf in risk_factors if rf.severity == "watch"]
        rec = (f"Acceptable credit profile with minor watch items. "
               f"Average guarantor FICO {avg_score:.0f}. "
               f"Monitor: {'; '.join(watch_items[:2])}. "
               f"Standard pricing with possible risk premium of 25-50 bps.")
    elif overall == "marginal":
        concern_items = [rf.finding for rf in risk_factors if rf.severity == "concern"]
        rec = (f"Marginal credit profile — proceed with caution. "
               f"Key concerns: {'; '.join(concern_items[:2])}. "
               f"Consider SBA guarantee, additional collateral, or shorter term to mitigate risk. "
               f"Pricing should reflect elevated risk (+75-150 bps).")
    elif overall == "weak":
        rec = (f"Weak credit profile with {criticals} critical finding(s). "
               f"Recommend credit remediation plan before new lending. "
               f"If proceeding, require full collateralization and personal guaranty "
               f"with monitoring covenants.")
    else:
        rec = (f"Adverse credit profile — not recommended for new credit. "
               f"{criticals} critical finding(s) must be resolved. "
               f"Offer credit remediation advisory and revisit in 6-12 months.")

    assessment = CreditPositionAssessment(
        business_name=business["business_name"] if business else personals[0]["borrower_name"] if personals else "Unknown",
        assessment_date=datetime.now().isoformat(),
        overall_credit_rating=overall,
        personal_score_avg=avg_score,
        personal_score_lowest=lowest_score,
        business_paydex=biz_paydex,
        combined_debt_to_income=combined_dti,
        personal_guaranty_strength=guaranty,
        risk_factors=risk_factors,
        lending_capacity_estimate=capacity,
        cross_sell_opportunities=cross_sell,
        recommendation=rec,
    )
    return assessment.model_dump()
