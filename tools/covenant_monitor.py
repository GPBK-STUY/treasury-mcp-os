"""Debt Covenant Monitor — tracks compliance and flags breach risks."""
import os
import pandas as pd
from models import CovenantStatus, CovenantReport


def monitor_debt_covenants(data_dir: str) -> dict:
    """Monitor debt covenant compliance across all credit facilities."""
    df = pd.read_csv(os.path.join(data_dir, "covenants.csv"))
    statuses = []
    breaches = warnings = 0

    for _, row in df.iterrows():
        name = str(row["covenant_name"])
        comp = str(row.get("comparison", "")).lower().strip()
        threshold = float(row["required_threshold"])
        current = float(row["current_value"])

        if comp == "minimum" and threshold != 0:
            headroom = ((current - threshold) / threshold) * 100
        elif comp == "maximum" and threshold != 0:
            headroom = ((threshold - current) / threshold) * 100
        else:
            headroom = 0.0

        if headroom < 0:
            status = "breach"
            breaches += 1
        elif headroom < 10:
            status = "warning"
            warnings += 1
        else:
            status = "compliant"

        statuses.append(CovenantStatus(
            covenant_name=name,
            covenant_type=str(row.get("covenant_type", comp)),
            required_threshold=round(threshold, 4),
            current_value=round(current, 4),
            headroom_pct=round(headroom, 2),
            status=status,
            next_test_date=str(row.get("next_test_date", "")),
        ))

    if breaches > 0:
        overall = "breach"
        rec = f"URGENT: {breaches} covenant breach(es). Contact lenders immediately."
    elif warnings > 0:
        overall = "warning"
        closest = min((s for s in statuses if s.status == "warning"), key=lambda x: x.headroom_pct)
        rec = (f"{closest.covenant_name} has {closest.headroom_pct}% headroom. "
               f"Monitor closely approaching {closest.required_threshold}x threshold.")
    else:
        overall = "compliant"
        rec = f"All {len(statuses)} covenants compliant with comfortable headroom."

    return CovenantReport(
        covenants=statuses, overall_status=overall,
        breaches=breaches, warnings=warnings, recommendation=rec,
    ).model_dump()
