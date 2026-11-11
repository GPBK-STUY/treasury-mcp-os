"""TreasuryOS MCP Server — Composable Financial Intelligence for Commercial Banking."""
import io
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Optional, Union

import pandas as pd
from pydantic import Field
from mcp.server.fastmcp import FastMCP

_DIR = Path(__file__).resolve().parent
DATA_DIR = os.environ.get("TREASURY_DATA_DIR", str(_DIR / "sample_data"))
DEMO_MODE = "TREASURY_DATA_DIR" not in os.environ
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from tools.aggregator import get_cash_position as _get_cash_position
from tools.idle_cash import scan_idle_balances as _scan_idle_balances
from tools.forecaster import forecast_cash_position as _forecast_cash_position
from tools.working_capital import analyze_working_capital as _analyze_working_capital
from tools.payment_optimizer import optimize_payment_timing as _optimize_payment_timing
from tools.fx_scanner import scan_fx_exposure as _scan_fx_exposure
from tools.covenant_monitor import monitor_debt_covenants as _monitor_debt_covenants
from tools.credit_parser import parse_credit_report as _parse_credit_report
from tools.credit_assessor import assess_credit_position as _assess_credit_position


# ── Data format: what each input file contains ─────────────────────────────
DATA_FILES = {
    "accounts": {
        "description": "One row per bank account, with its current balance.",
        "required": ["account_id", "bank_name", "account_type", "currency", "balance"],
        "optional": ["yield_rate_bps", "last_updated"],
        "allowed_values": {"account_type": ["checking", "savings", "money_market", "cd"]},
        "notes": "Balances in the account's own currency. yield_rate_bps is the current yield in basis points (125 = 1.25%). The forecast starts from checking balances only.",
        "example": {"account_id": "ACCT-001", "bank_name": "Citizens Bank", "account_type": "checking",
                    "currency": "USD", "balance": 2847500.00, "yield_rate_bps": 0, "last_updated": "2026-02-07"},
    },
    "transactions": {
        "description": "Historical cash movements; drives the cash forecast. 8+ weeks of history works best.",
        "required": ["date", "amount", "category"],
        "optional": ["account_id", "description"],
        "allowed_values": {"category": ["ar_collection", "revenue", "ap_payment", "payroll",
                                        "operating_expense", "debt_service", "tax"]},
        "notes": "date is YYYY-MM-DD. Inflows (ar_collection, revenue) are positive; every other category is an outflow and is negative.",
        "example": {"date": "2025-11-01", "account_id": "ACCT-001", "description": "AR Collection - Acme Corp",
                    "amount": 425000.00, "category": "ar_collection"},
    },
    "vendors": {
        "description": "Open payables. Drives early-payment discounts and FX exposure.",
        "required": ["vendor_name", "outstanding_amount", "due_date"],
        "optional": ["vendor_id", "currency", "payment_terms", "discount_terms"],
        "allowed_values": {},
        "notes": "due_date is YYYY-MM-DD. currency defaults to USD. discount_terms like '2/10 net 30' (2% off if paid within 10 days); leave blank if none.",
        "example": {"vendor_id": "V-001", "vendor_name": "Alcoa Raw Materials", "payment_terms": "net_30",
                    "discount_terms": "2/10 net 30", "outstanding_amount": 285000.00, "currency": "USD",
                    "due_date": "2026-02-25"},
    },
    "fx_rates": {
        "description": "Spot rates to convert foreign-currency payables to USD.",
        "required": ["currency_pair", "rate"],
        "optional": ["last_updated"],
        "allowed_values": {},
        "notes": "currency_pair like 'EUR/USD'; rate is USD per one unit of the foreign currency.",
        "example": {"currency_pair": "EUR/USD", "rate": 1.0845, "last_updated": "2026-02-07"},
    },
    "covenants": {
        "description": "Loan covenants and the latest tested values.",
        "required": ["covenant_name", "required_threshold", "current_value", "comparison"],
        "optional": ["covenant_type", "facility_name", "next_test_date"],
        "allowed_values": {"comparison": ["minimum", "maximum"],
                           "covenant_type": ["dscr", "leverage", "liquidity", "fixed_charge", "other"]},
        "notes": "comparison 'minimum' means current_value must stay at or above the threshold (e.g. DSCR); 'maximum' means at or below (e.g. leverage).",
        "example": {"covenant_name": "Debt Service Coverage Ratio", "covenant_type": "dscr",
                    "required_threshold": 1.25, "current_value": 1.42, "comparison": "minimum",
                    "facility_name": "Revolver", "next_test_date": "2026-03-31"},
    },
    "personal_credit": {
        "description": "Personal credit report summary, one row per owner/guarantor.",
        "required": ["borrower_name", "credit_score", "report_date", "total_tradelines", "open_tradelines",
                     "total_revolving_balance", "total_revolving_limit", "revolving_utilization_pct",
                     "total_installment_balance", "monthly_installment_payments"],
        "optional": ["score_model", "derogatory_marks", "collections", "public_records", "oldest_account_years",
                     "recent_inquiries_6mo", "late_payments_30d", "late_payments_60d", "late_payments_90d",
                     "payment_history_pct", "bankruptcies", "foreclosures", "tax_liens"],
        "allowed_values": {},
        "notes": "Omitted optional counts are treated as 0 (clean). Include late payments, derogatories, bankruptcies and liens whenever they are known. Never include full SSNs.",
        "example": {"borrower_name": "Jane Owner", "credit_score": 742, "score_model": "FICO 8",
                    "report_date": "2026-01-20", "total_tradelines": 14, "open_tradelines": 9,
                    "total_revolving_balance": 18500.00, "total_revolving_limit": 60000.00,
                    "revolving_utilization_pct": 30.8, "total_installment_balance": 42000.00,
                    "monthly_installment_payments": 1150.00, "late_payments_30d": 1,
                    "payment_history_pct": 98.0},
    },
    "business_credit": {
        "description": "Business credit report summary (D&B / Experian style), one row.",
        "required": ["business_name", "report_date", "paydex_score", "years_in_business",
                     "total_trade_experiences", "current_pct", "days_beyond_terms_avg", "high_credit",
                     "total_balance_outstanding"],
        "optional": ["duns_number", "intelliscore", "sic_code", "industry", "payment_trend", "derogatory_count",
                     "liens", "judgments", "ucc_filings", "bankruptcy_flag", "d_and_b_rating",
                     "annual_revenue", "employees", "trade_payment_index"],
        "allowed_values": {"payment_trend": ["improving", "stable", "declining"]},
        "notes": "current_pct is the % of trade experiences paid on time. Omitted counts (liens, judgments, ucc_filings) are treated as 0.",
        "example": {"business_name": "Apex Manufacturing Corp", "report_date": "2026-01-20", "paydex_score": 78,
                    "years_in_business": 12, "total_trade_experiences": 24, "current_pct": 82.0,
                    "days_beyond_terms_avg": 8.5, "high_credit": 500000.00,
                    "total_balance_outstanding": 385000.00, "payment_trend": "stable", "liens": 0},
    },
}

ClientData = Annotated[
    Optional[dict[str, Union[str, list[dict]]]],
    Field(description=(
        "The business's own data, to analyze it instead of the bundled demo company. "
        "Keys are data file names (accounts, transactions, vendors, fx_rates, covenants, "
        "personal_credit, business_credit). Each value is either CSV text with a header row, "
        "or a list of row objects. Call get_data_format for the columns. Data is used for this "
        "call only and not stored."
    )),
]
DataDir = Annotated[
    Optional[str],
    Field(description="Path to a local folder of CSVs named like accounts.csv, vendors.csv, etc. Ignored if `data` is given."),
]


def _to_frame(name: str, value) -> pd.DataFrame:
    if isinstance(value, str):
        return pd.read_csv(io.StringIO(value.strip()))
    if isinstance(value, list):
        return pd.DataFrame(value)
    raise ValueError(f"'{name}' must be CSV text or a list of row objects.")


@contextmanager
def _source(data, data_dir, needs: list[str], needs_any: Optional[list[str]] = None):
    """Yield (folder, label) for the tools to read from: provided data > folder > default."""
    if data:
        clean = {}
        for key, value in data.items():
            name = key.lower().removesuffix(".csv").strip()
            if name not in DATA_FILES:
                raise ValueError(f"Unknown data file '{key}'. Valid names: {', '.join(DATA_FILES)}.")
            df = _to_frame(name, value)
            df.columns = [str(c).strip() for c in df.columns]
            missing = [c for c in DATA_FILES[name]["required"] if c not in df.columns]
            if missing:
                raise ValueError(f"'{name}' is missing required columns: {', '.join(missing)}. "
                                 f"Call get_data_format for the full format.")
            if df.empty:
                raise ValueError(f"'{name}' has no rows.")
            clean[name] = df
        lacking = [n for n in needs if n not in clean]
        if lacking:
            raise ValueError(f"This tool needs: {', '.join(lacking)}. Provide them in `data` "
                             f"(see get_data_format).")
        if needs_any and not any(n in clean for n in needs_any):
            raise ValueError(f"This tool needs at least one of: {', '.join(needs_any)}.")
        with tempfile.TemporaryDirectory(prefix="treasuryos-") as tmp:
            for name, df in clean.items():
                df.to_csv(os.path.join(tmp, f"{name}.csv"), index=False)
            yield tmp, "provided"
    elif data_dir:
        folder = os.path.expanduser(data_dir)
        if not os.path.isdir(folder):
            raise ValueError(f"Folder not found: {folder}")
        yield folder, "folder"
    else:
        yield DATA_DIR, "demo (Apex Manufacturing sample data)" if DEMO_MODE else "configured folder"


def _tag(result: dict, label: str) -> dict:
    out = {"data_source": label}
    out.update(result)
    return out


INSTRUCTIONS = """TreasuryOS: treasury and credit analysis for small-business banking.
Act as a junior relationship manager: outputs are advisory, never lending decisions.

Data: with no data passed, tools analyze a bundled DEMO company (Apex Manufacturing).
To analyze a real business (for example, from statements, a balance sheet or a credit report
the user shares), call get_data_format, convert what you have into those columns, and pass it
in the `data` argument. Every result has a `data_source` field; always tell the user when
results come from demo data. Never invent numbers to fill required columns: ask the user.

Typical chains:
- Cash check: get_cash_position -> scan_idle_balances -> forecast_cash_position
- Company health: analyze_working_capital -> monitor_debt_covenants -> scan_fx_exposure
- Credit review: parse_credit_report -> assess_credit_position
Guardrails: flag DSCR < 1.25x, current ratio < 1.20x, leverage > 3.50x, covenant headroom < 10%.
Never recommend deploying cash below a 20% operating reserve. Format money as $1,250,000.00 and
show basis points as percentages (450 bps = 4.50%). Credit data is point-in-time; note the pull date."""

mcp = FastMCP("TreasuryOS", instructions=INSTRUCTIONS)


@mcp.tool()
def get_data_format() -> dict:
    """Describe the data each tool accepts: file names, required and optional columns, allowed values,
    and an example row. Call this before passing a business's own data in the `data` argument."""
    used_by = {
        "accounts": ["get_cash_position", "scan_idle_balances", "forecast_cash_position", "assess_credit_position (optional)"],
        "transactions": ["forecast_cash_position"],
        "vendors": ["optimize_payment_timing", "scan_fx_exposure"],
        "fx_rates": ["scan_fx_exposure (needed when any vendor is non-USD)"],
        "covenants": ["monitor_debt_covenants", "assess_credit_position (optional)"],
        "personal_credit": ["parse_credit_report", "assess_credit_position"],
        "business_credit": ["parse_credit_report", "assess_credit_position"],
    }
    return {
        "how_to_pass": ("Pass data={'accounts': <CSV text or list of row objects>, ...} to any tool. "
                        "Only include the files that tool needs. analyze_working_capital takes plain numbers instead."),
        "files": {name: {**spec, "used_by": used_by[name]} for name, spec in DATA_FILES.items()},
    }


@mcp.tool()
def get_cash_position(data: ClientData = None, data_dir: DataDir = None) -> dict:
    """Get aggregated cash position across all bank accounts.
    Returns balances by currency and account type. Needs: accounts."""
    with _source(data, data_dir, ["accounts"]) as (d, label):
        return _tag(_get_cash_position(data_dir=d), label)


@mcp.tool()
def scan_idle_balances(operating_reserve_pct: float = 0.20,
                       target_yield_bps: int = 450,
                       data: ClientData = None, data_dir: DataDir = None) -> dict:
    """Scan checking and savings for idle cash that could earn higher yields.
    Args: operating_reserve_pct (default 0.20), target_yield_bps (default 450). Needs: accounts."""
    with _source(data, data_dir, ["accounts"]) as (d, label):
        return _tag(_scan_idle_balances(d, operating_reserve_pct, target_yield_bps), label)


@mcp.tool()
def forecast_cash_position(horizon_days: int = 90,
                           data: ClientData = None, data_dir: DataDir = None) -> dict:
    """Forecast cash position using historical transaction patterns.
    Args: horizon_days (default 90, 7-365). Needs: accounts, transactions."""
    with _source(data, data_dir, ["accounts", "transactions"]) as (d, label):
        return _tag(_forecast_cash_position(d, min(max(horizon_days, 7), 365)), label)


@mcp.tool()
def analyze_working_capital(current_assets: float, current_liabilities: float,
                            annual_revenue: float, accounts_receivable: float,
                            accounts_payable: float, annual_cogs: float) -> dict:
    """Analyze working capital health from balance-sheet and income-statement figures.
    All values in the same currency (USD). Takes numbers directly; no data files needed."""
    return _analyze_working_capital(current_assets, current_liabilities,
                                    annual_revenue, accounts_receivable,
                                    accounts_payable, annual_cogs)


@mcp.tool()
def optimize_payment_timing(available_cash: float = 0.0,
                            data: ClientData = None, data_dir: DataDir = None) -> dict:
    """Find early-payment discounts that beat cost of capital.
    Args: available_cash budget (0 = show all opportunities). Needs: vendors."""
    with _source(data, data_dir, ["vendors"]) as (d, label):
        return _tag(_optimize_payment_timing(d, available_cash), label)


@mcp.tool()
def scan_fx_exposure(data: ClientData = None, data_dir: DataDir = None) -> dict:
    """Scan for unhedged FX exposures in vendor payables.
    Calculates Value at Risk and recommends hedging strategies. Needs: vendors, fx_rates."""
    with _source(data, data_dir, ["vendors", "fx_rates"]) as (d, label):
        return _tag(_scan_fx_exposure(d), label)


@mcp.tool()
def monitor_debt_covenants(data: ClientData = None, data_dir: DataDir = None) -> dict:
    """Monitor debt covenant compliance across credit facilities.
    Flags breaches and warnings (within 10% of threshold). Needs: covenants."""
    with _source(data, data_dir, ["covenants"]) as (d, label):
        return _tag(_monitor_debt_covenants(d), label)


@mcp.tool()
def parse_credit_report(data: ClientData = None, data_dir: DataDir = None) -> dict:
    """Parse personal and business credit report summaries.
    Extracts FICO scores, Paydex, utilization, payment history, derogatories,
    and public records. Needs: personal_credit and/or business_credit."""
    with _source(data, data_dir, [], ["personal_credit", "business_credit"]) as (d, label):
        return _tag(_parse_credit_report(data_dir=d), label)


@mcp.tool()
def assess_credit_position(annual_gross_income: float = 0.0,
                           data: ClientData = None, data_dir: DataDir = None) -> dict:
    """Assess combined credit + cash flow lending readiness.
    Integrates credit reports with cash position and covenant data to produce
    an overall credit rating, risk factors, lending capacity estimate, and
    cross-sell opportunities.
    Args: annual_gross_income (combined guarantor income for DTI calc, 0 to skip).
    Needs: personal_credit and/or business_credit; accounts and covenants improve the result."""
    with _source(data, data_dir, [], ["personal_credit", "business_credit"]) as (d, label):
        return _tag(_assess_credit_position(data_dir=d, annual_gross_income=annual_gross_income), label)


def main():
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport != "stdio":
        mcp.settings.host = os.environ.get("HOST", "0.0.0.0")
        mcp.settings.port = int(os.environ.get("PORT", "8000"))
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
