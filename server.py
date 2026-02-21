"""TreasuryOS MCP Server — Composable Financial Intelligence for Commercial Banking."""
import os, sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

_DIR = Path(__file__).resolve().parent
DATA_DIR = os.environ.get("TREASURY_DATA_DIR", str(_DIR / "sample_data"))
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

mcp = FastMCP("TreasuryOS")


@mcp.tool()
def get_cash_position() -> dict:
    """Get aggregated cash position across all bank accounts.
    Returns balances by currency and account type."""
    return _get_cash_position(data_dir=DATA_DIR)


@mcp.tool()
def scan_idle_balances(operating_reserve_pct: float = 0.20,
                       target_yield_bps: int = 450) -> dict:
    """Scan for idle cash that could earn higher yields.
    Args: operating_reserve_pct (default 0.20), target_yield_bps (default 450)."""
    return _scan_idle_balances(DATA_DIR, operating_reserve_pct, target_yield_bps)


@mcp.tool()
def forecast_cash_position(horizon_days: int = 90) -> dict:
    """Forecast cash position using historical transaction patterns.
    Args: horizon_days (default 90, max 365)."""
    return _forecast_cash_position(DATA_DIR, min(max(horizon_days, 7), 365))


@mcp.tool()
def analyze_working_capital(current_assets: float, current_liabilities: float,
                            annual_revenue: float, accounts_receivable: float,
                            accounts_payable: float, annual_cogs: float) -> dict:
    """Analyze working capital health. All values in same currency (USD)."""
    return _analyze_working_capital(current_assets, current_liabilities,
                                    annual_revenue, accounts_receivable,
                                    accounts_payable, annual_cogs)


@mcp.tool()
def optimize_payment_timing(available_cash: float = 0.0) -> dict:
    """Find early-payment discounts that beat cost of capital.
    Args: available_cash budget (0 = show all opportunities)."""
    return _optimize_payment_timing(DATA_DIR, available_cash)


@mcp.tool()
def scan_fx_exposure() -> dict:
    """Scan for unhedged FX exposures in vendor payables.
    Calculates Value at Risk and recommends hedging strategies."""
    return _scan_fx_exposure(DATA_DIR)


@mcp.tool()
def monitor_debt_covenants() -> dict:
    """Monitor debt covenant compliance across credit facilities.
    Flags breaches and warnings (within 10% of threshold)."""
    return _monitor_debt_covenants(DATA_DIR)


@mcp.tool()
def parse_credit_report() -> dict:
    """Parse personal and business credit reports already on file.
    Extracts FICO scores, Paydex, utilization, payment history, derogatories,
    and public records from credit data pulled during the application process."""
    return _parse_credit_report(data_dir=DATA_DIR)


@mcp.tool()
def assess_credit_position(annual_gross_income: float = 0.0) -> dict:
    """Assess combined credit + cash flow lending readiness.
    Integrates credit reports with cash position and covenant data to produce
    an overall credit rating, risk factors, lending capacity estimate, and
    cross-sell opportunities.
    Args: annual_gross_income (combined guarantor income for DTI calc, 0 to skip)."""
    return _assess_credit_position(data_dir=DATA_DIR,
                                   annual_gross_income=annual_gross_income)


def main():
    mcp.run()

if __name__ == "__main__":
    main()
