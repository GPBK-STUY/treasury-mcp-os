"""
TreasuryOS — Web Dashboard
Financial intelligence for commercial banking and business owners.
Run:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from tools.aggregator import get_cash_position
from tools.idle_cash import scan_idle_balances
from tools.forecaster import forecast_cash_position
from tools.working_capital import analyze_working_capital
from tools.payment_optimizer import optimize_payment_timing
from tools.fx_scanner import scan_fx_exposure
from tools.covenant_monitor import monitor_debt_covenants
from tools.credit_parser import parse_credit_report
from tools.credit_assessor import assess_credit_position

# ─── Config ─────────────────────────────────────────────────
st.set_page_config(page_title="TreasuryOS", page_icon="T", layout="wide", initial_sidebar_state="expanded")

# ─── Design System ──────────────────────────────────────────
NAVY = "#0B1426"
DARK_NAVY = "#060E1A"
CARD_BG = "#111D32"
CARD_BORDER = "#1E3050"
ACCENT = "#3B82F6"
ACCENT_LIGHT = "#60A5FA"
TEXT_PRIMARY = "#F1F5F9"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED = "#64748B"
GREEN = "#10B981"
YELLOW = "#F59E0B"
RED = "#EF4444"
SURFACE = "#0F1A2E"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global ── */
    .stApp {{ background: {NAVY}; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }}
    .main .block-container {{ padding: 1.5rem 2rem 2rem; max-width: 1400px; }}
    #MainMenu, footer {{ visibility: hidden; }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background: {DARK_NAVY};
        border-right: 1px solid {CARD_BORDER};
    }}
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {{ color: {TEXT_SECONDARY}; font-size: 0.875rem; }}
    section[data-testid="stSidebar"] h1 {{ color: {TEXT_PRIMARY}; font-size: 1.25rem; font-weight: 600; letter-spacing: -0.01em; }}
    section[data-testid="stSidebar"] h3 {{ color: {TEXT_MUTED}; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; }}
    section[data-testid="stSidebar"] hr {{ border-color: {CARD_BORDER}; margin: 0.75rem 0; }}

    /* ── Typography ── */
    h1 {{ color: {TEXT_PRIMARY} !important; font-weight: 700 !important; font-size: 1.75rem !important; letter-spacing: -0.02em !important; margin-bottom: 0.25rem !important; }}
    h2 {{ color: {TEXT_PRIMARY} !important; font-weight: 600 !important; font-size: 1.25rem !important; letter-spacing: -0.01em !important; }}
    h3 {{ color: {TEXT_SECONDARY} !important; font-weight: 500 !important; font-size: 1rem !important; }}
    p, li {{ color: {TEXT_SECONDARY}; }}
    .stCaption p {{ color: {TEXT_MUTED} !important; font-size: 0.8rem !important; }}

    /* ── Metric Cards ── */
    div[data-testid="stMetric"] {{
        background: {CARD_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 10px;
        padding: 1.25rem;
    }}
    div[data-testid="stMetric"] label {{ color: {TEXT_MUTED} !important; font-size: 0.75rem !important; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{ color: {TEXT_PRIMARY} !important; font-size: 1.5rem !important; font-weight: 700; }}
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {{ font-size: 0.8rem !important; }}

    /* ── Data Tables ── */
    .stDataFrame {{ border-radius: 10px; overflow: hidden; }}
    .stDataFrame [data-testid="stDataFrameResizable"] {{ background: {CARD_BG}; border: 1px solid {CARD_BORDER}; border-radius: 10px; }}

    /* ── Expanders ── */
    .streamlit-expanderHeader {{
        background: {CARD_BG} !important;
        border: 1px solid {CARD_BORDER} !important;
        border-radius: 8px !important;
        color: {TEXT_PRIMARY} !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }}
    .streamlit-expanderContent {{
        background: {SURFACE} !important;
        border: 1px solid {CARD_BORDER} !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }}

    /* ── Buttons ── */
    .stButton > button {{
        background: {ACCENT} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.2s !important;
    }}
    .stButton > button:hover {{ background: {ACCENT_LIGHT} !important; }}

    /* ── Inputs ── */
    .stSlider label, .stNumberInput label, .stRadio label, .stFileUploader label {{ color: {TEXT_SECONDARY} !important; font-size: 0.85rem !important; }}
    .stRadio [data-testid="stMarkdownContainer"] p {{ color: {TEXT_SECONDARY} !important; }}

    /* ── Alerts ── */
    .stAlert {{ border-radius: 8px; }}

    /* ── Charts ── */
    .stPlotlyChart, [data-testid="stArrowVegaLiteChart"] {{ background: {CARD_BG}; border-radius: 10px; padding: 0.5rem; border: 1px solid {CARD_BORDER}; }}

    /* ── Custom Classes ── */
    .page-header {{ margin-bottom: 1.5rem; }}
    .section-divider {{ border: none; border-top: 1px solid {CARD_BORDER}; margin: 1.5rem 0; }}
    .card {{ background: {CARD_BG}; border: 1px solid {CARD_BORDER}; border-radius: 10px; padding: 1.25rem; margin-bottom: 1rem; }}
    .card-header {{ color: {TEXT_MUTED}; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.75rem; }}
    .card-value {{ color: {TEXT_PRIMARY}; font-size: 1.75rem; font-weight: 700; line-height: 1.2; }}
    .card-subtitle {{ color: {TEXT_SECONDARY}; font-size: 0.8rem; margin-top: 0.25rem; }}
    .dot-green {{ color: {GREEN}; }}
    .dot-yellow {{ color: {YELLOW}; }}
    .dot-red {{ color: {RED}; }}
    .status-row {{ display: flex; align-items: center; gap: 0.5rem; padding: 0.625rem 0; border-bottom: 1px solid {CARD_BORDER}; }}
    .status-row:last-child {{ border-bottom: none; }}
    .status-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex-shrink: 0; }}
    .status-dot.green {{ background: {GREEN}; box-shadow: 0 0 6px {GREEN}40; }}
    .status-dot.yellow {{ background: {YELLOW}; box-shadow: 0 0 6px {YELLOW}40; }}
    .status-dot.red {{ background: {RED}; box-shadow: 0 0 6px {RED}40; }}
    .status-label {{ color: {TEXT_PRIMARY}; font-size: 0.875rem; font-weight: 500; }}
    .status-detail {{ color: {TEXT_MUTED}; font-size: 0.8rem; margin-left: auto; }}
    .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }}
    .stat-item {{ padding: 0.5rem 0; }}
    .stat-label {{ color: {TEXT_MUTED}; font-size: 0.75rem; }}
    .stat-value {{ color: {TEXT_PRIMARY}; font-size: 0.9rem; font-weight: 500; }}
    .tag {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }}
    .tag-green {{ background: {GREEN}20; color: {GREEN}; }}
    .tag-yellow {{ background: {YELLOW}20; color: {YELLOW}; }}
    .tag-red {{ background: {RED}20; color: {RED}; }}
    .top-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }}
    .top-bar-title {{ color: {TEXT_PRIMARY}; font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; }}
    .top-bar-sub {{ color: {TEXT_MUTED}; font-size: 0.85rem; }}
</style>
""", unsafe_allow_html=True)


# ─── Session State ──────────────────────────────────────────
if "data_dir" not in st.session_state:
    st.session_state.data_dir = str(_DIR / "sample_data")
    st.session_state.using_sample = True
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}


# ─── Helpers ────────────────────────────────────────────────
def fmt(value, decimals=0):
    if value is None: return "—"
    if abs(value) >= 1_000_000: return f"${value/1_000_000:,.{decimals}f}M"
    if abs(value) >= 1_000: return f"${value/1_000:,.{decimals}f}K"
    return f"${value:,.{decimals}f}"

def dot_color(status):
    s = status.lower()
    if s in ("compliant","strong","healthy","excellent","good","positive","low_risk"): return "green"
    if s in ("warning","watch","adequate","fair","moderate_risk","neutral","marginal"): return "yellow"
    return "red"

def status_html(status, label=None, detail=None):
    c = dot_color(status)
    lbl = label or status.replace("_"," ").title()
    d = f'<span class="status-detail">{detail}</span>' if detail else ""
    return f'<div class="status-row"><span class="status-dot {c}"></span><span class="status-label">{lbl}</span>{d}</div>'

def tag_html(status, text=None):
    c = dot_color(status)
    t = text or status.replace("_"," ").title()
    return f'<span class="tag tag-{c}">{t}</span>'

def metric_card(label, value, subtitle=""):
    sub = f'<div class="card-subtitle">{subtitle}</div>' if subtitle else ""
    return f'<div class="card"><div class="card-header">{label}</div><div class="card-value">{value}</div>{sub}</div>'

def run_safe(fn, *a, **kw):
    try: return fn(*a, **kw), None
    except FileNotFoundError as e: return None, f"Missing: {e}"
    except Exception as e: return None, str(e)

def save_uploads(files):
    d = tempfile.mkdtemp(prefix="treasuryos_")
    for name, f in files.items():
        with open(os.path.join(d, name), "wb") as out:
            out.write(f.getbuffer())
    return d


# ─── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# T  TreasuryOS")
    st.markdown("---")

    st.markdown("### Data Source")
    src = st.radio("src", ["Demo Data", "Upload Files"], label_visibility="collapsed")

    if src == "Upload Files":
        st.session_state.using_sample = False
        uploaded_accounts = st.file_uploader("accounts.csv", type="csv", key="accounts")
        uploaded_transactions = st.file_uploader("transactions.csv", type="csv", key="transactions")
        uploaded_vendors = st.file_uploader("vendors.csv", type="csv", key="vendors")
        uploaded_covenants = st.file_uploader("covenants.csv", type="csv", key="covenants")
        uploaded_fx = st.file_uploader("fx_rates.csv", type="csv", key="fx")
        uploaded_pcredit = st.file_uploader("personal_credit.csv", type="csv", key="pcredit")
        uploaded_bcredit = st.file_uploader("business_credit.csv", type="csv", key="bcredit")
        fmap = {"accounts.csv": uploaded_accounts, "transactions.csv": uploaded_transactions,
                "vendors.csv": uploaded_vendors, "covenants.csv": uploaded_covenants,
                "fx_rates.csv": uploaded_fx, "personal_credit.csv": uploaded_pcredit,
                "business_credit.csv": uploaded_bcredit}
        uploaded = {k: v for k, v in fmap.items() if v}
        if uploaded:
            st.session_state.data_dir = save_uploads(uploaded)
            st.session_state.uploaded_files = uploaded
    else:
        st.session_state.using_sample = True
        st.session_state.data_dir = str(_DIR / "sample_data")

    st.markdown("---")
    st.markdown("### Navigation")
    page = st.radio("nav", [
        "Overview", "Cash Position", "Idle Cash", "Cash Forecast",
        "Payments", "FX Exposure", "Covenants",
        "Credit Report", "Credit Assessment", "Working Capital"
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f'<p style="color:{TEXT_MUTED}; font-size:0.7rem; text-align:center;">TreasuryOS v0.1 &middot; <a href="https://github.com/GPBK-STUY/treasury-mcp-os" style="color:{TEXT_MUTED};">GitHub</a></p>', unsafe_allow_html=True)


# ─── Main ───────────────────────────────────────────────────
DATA = st.session_state.data_dir
NOW = datetime.now().strftime("%b %d, %Y &middot; %I:%M %p")


# ═══════════════════════════════════════════════════════════
#  OVERVIEW
# ═══════════════════════════════════════════════════════════
if page == "Overview":
    st.markdown(f"""<div class="top-bar">
        <div><div class="top-bar-title">Financial Overview</div>
        <div class="top-bar-sub">{"Demo: Apex Manufacturing Corp" if st.session_state.using_sample else "Your Data"} &middot; {NOW}</div></div>
    </div>""", unsafe_allow_html=True)

    # Fetch all data
    cash, cash_e = run_safe(get_cash_position, DATA)
    idle, idle_e = run_safe(scan_idle_balances, DATA)
    cov, cov_e = run_safe(monitor_debt_covenants, DATA)
    credit, credit_e = run_safe(assess_credit_position, DATA)

    # ── Top Metrics ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        val = fmt(cash["total_balance"]) if cash else "—"
        sub = f'{len(cash["accounts"])} accounts' if cash else ""
        st.markdown(metric_card("Total Cash", val, sub), unsafe_allow_html=True)
    with c2:
        val = fmt(idle["total_idle_cash"]) if idle else "—"
        sub = f'{fmt(idle["total_annual_opportunity_cost"])}/yr lost' if idle else ""
        st.markdown(metric_card("Idle Cash", val, sub), unsafe_allow_html=True)
    with c3:
        if cov:
            color = dot_color(cov["overall_status"])
            val = tag_html(cov["overall_status"])
            sub = f'{cov.get("warnings",0)} warnings &middot; {cov.get("breaches",0)} breaches'
        else:
            val, sub = "—", ""
        st.markdown(metric_card("Covenants", val, sub), unsafe_allow_html=True)
    with c4:
        if credit:
            val = tag_html(credit["overall_credit_rating"])
            sub = f'Capacity: {credit.get("lending_capacity_estimate","—")}'
        else:
            val, sub = "—", ""
        st.markdown(metric_card("Credit Rating", val, sub), unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Two Column Detail ──
    left, right = st.columns(2)

    with left:
        st.markdown("### Cash by Account Type")
        if cash and cash.get("by_account_type"):
            df = pd.DataFrame([{"Type": k.replace("_"," ").title(), "Balance": v}
                               for k, v in cash["by_account_type"].items()])
            st.bar_chart(df.set_index("Type"), color=ACCENT)

        st.markdown("### Payment Opportunities")
        pay, _ = run_safe(optimize_payment_timing, DATA)
        if pay and pay.get("recommendations"):
            html = ""
            for r in pay["recommendations"][:4]:
                if r["recommendation"] == "pay_early":
                    html += status_html("strong", r["vendor_name"],
                                        f'Save {fmt(r["discount_amount"])} ({r["annualized_return_pct"]:.0f}% ann.)')
            if html:
                st.markdown(f'<div class="card">{html}</div>', unsafe_allow_html=True)
            else:
                st.caption("No early-pay opportunities right now.")
        else:
            st.caption("No vendor data loaded.")

    with right:
        st.markdown("### Covenant Health")
        if cov and cov.get("covenants"):
            html = ""
            for c in cov["covenants"]:
                html += status_html(c["status"], c["covenant_name"], f'{c["headroom_pct"]:.1f}% headroom')
            st.markdown(f'<div class="card">{html}</div>', unsafe_allow_html=True)
        else:
            st.caption("No covenant data loaded.")

        st.markdown("### Credit Snapshot")
        if credit and credit.get("risk_factors"):
            html = ""
            for rf in credit["risk_factors"][:6]:
                html += status_html(rf["severity"], rf["finding"][:60])
            st.markdown(f'<div class="card">{html}</div>', unsafe_allow_html=True)
        else:
            st.caption("No credit data loaded.")


# ═══════════════════════════════════════════════════════════
#  CASH POSITION
# ═══════════════════════════════════════════════════════════
elif page == "Cash Position":
    st.markdown(f'<div class="top-bar"><div><div class="top-bar-title">Cash Position</div><div class="top-bar-sub">Balances across all accounts &middot; {NOW}</div></div></div>', unsafe_allow_html=True)

    data, err = run_safe(get_cash_position, DATA)
    if err:
        st.error(err)
    elif data:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Cash", fmt(data["total_balance"]))
        c2.metric("Accounts", len(data["accounts"]))
        currencies = list(data.get("by_currency", {}).keys())
        c3.metric("Currencies", ", ".join(currencies) if currencies else "USD")

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        if data.get("by_currency") and len(data["by_currency"]) > 1:
            st.markdown("### By Currency")
            df = pd.DataFrame([{"Currency": k, "Balance": v} for k, v in data["by_currency"].items()])
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("### All Accounts")
        if data.get("accounts"):
            df = pd.DataFrame(data["accounts"])
            cols = [c for c in ["bank_name","account_type","currency","balance","yield_rate_bps"] if c in df.columns]
            df = df[cols].copy()
            if "balance" in df.columns:
                df["balance"] = df["balance"].apply(lambda x: f"${x:,.2f}")
            if "yield_rate_bps" in df.columns:
                df["yield_rate_bps"] = df["yield_rate_bps"].apply(lambda x: f"{x/100:.2f}%")
                df = df.rename(columns={"yield_rate_bps": "yield"})
            df.columns = [c.replace("_"," ").title() for c in df.columns]
            st.dataframe(df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════
#  IDLE CASH
# ═══════════════════════════════════════════════════════════
elif page == "Idle Cash":
    st.markdown(f'<div class="top-bar"><div><div class="top-bar-title">Idle Cash Scanner</div><div class="top-bar-sub">Money sitting in low-yield accounts &middot; {NOW}</div></div></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    reserve = c1.slider("Operating Reserve %", 5, 50, 20, 5) / 100
    target = c2.slider("Target Yield (bps)", 100, 600, 450, 50)

    data, err = run_safe(scan_idle_balances, DATA, reserve, target)
    if err:
        st.error(err)
    elif data:
        c1, c2 = st.columns(2)
        c1.metric("Idle Cash", fmt(data["total_idle_cash"]))
        c2.metric("Annual Opportunity Cost", fmt(data["total_annual_opportunity_cost"]))

        if data.get("opportunities"):
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            for opp in data["opportunities"]:
                with st.expander(f'{opp["bank_name"]} — {fmt(opp["idle_amount"])} idle'):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Current Balance", fmt(opp["current_balance"]))
                    c2.metric("Idle Amount", fmt(opp["idle_amount"]))
                    c3.metric("Cost/Year", fmt(opp["annual_opportunity_cost"]))
                    st.markdown(f'**Current Yield:** {opp["current_yield_bps"]/100:.2f}% &rarr; **Target:** {opp["recommended_yield_bps"]/100:.2f}%')
                    st.markdown(f'**Action:** {opp["recommended_action"]}')


# ═══════════════════════════════════════════════════════════
#  CASH FORECAST
# ═══════════════════════════════════════════════════════════
elif page == "Cash Forecast":
    st.markdown(f'<div class="top-bar"><div><div class="top-bar-title">Cash Forecast</div><div class="top-bar-sub">Projected cash position &middot; {NOW}</div></div></div>', unsafe_allow_html=True)

    horizon = st.slider("Forecast Horizon (days)", 30, 365, 90, 30)
    data, err = run_safe(forecast_cash_position, DATA, horizon)
    if err:
        st.error(err)
    elif data and data.get("projections"):
        df = pd.DataFrame(data["projections"])
        if "ending_balance" in df.columns and "period" in df.columns:
            chart_df = df.set_index("period")[["ending_balance"]]
            chart_df.columns = ["Projected Balance"]
            st.line_chart(chart_df, color=ACCENT)

        if data.get("deficit_periods"):
            st.warning(f'Potential shortfalls in: {", ".join(data["deficit_periods"])}')
        if data.get("recommendation"):
            st.info(data["recommendation"])

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("### Weekly Detail")
        display = df.copy()
        for col in ["starting_balance","expected_inflows","expected_outflows","net_flow","ending_balance"]:
            if col in display.columns:
                display[col] = display[col].apply(lambda x: f"${x:,.0f}")
        display.columns = [c.replace("_"," ").title() for c in display.columns]
        st.dataframe(display, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════
#  PAYMENTS
# ═══════════════════════════════════════════════════════════
elif page == "Payments":
    st.markdown(f'<div class="top-bar"><div><div class="top-bar-title">Payment Optimizer</div><div class="top-bar-sub">Early-pay discount analysis &middot; {NOW}</div></div></div>', unsafe_allow_html=True)

    budget = st.number_input("Available cash for early payments ($)", min_value=0, value=0, step=10000)
    data, err = run_safe(optimize_payment_timing, DATA, float(budget))
    if err:
        st.error(err)
    elif data:
        c1, c2, c3 = st.columns(3)
        c1.metric("Discounts Available", fmt(data.get("total_discount_available", 0)))
        c2.metric("Annualized Savings", fmt(data.get("total_annualized_savings", 0)))
        c3.metric("Cash Required", fmt(data.get("cash_required_for_early_payments", 0)))

        if data.get("recommendations"):
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            for r in data["recommendations"]:
                action_tag = tag_html("strong", "Pay Early") if r["recommendation"] == "pay_early" else tag_html("watch", "Hold")
                with st.expander(f'{r["vendor_name"]} — {r["discount_terms"]} ({r["annualized_return_pct"]:.0f}% ann.)'):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Invoice", fmt(r["invoice_amount"]))
                    c2.metric("Discount", fmt(r["discount_amount"]))
                    c3.metric("Return", f'{r["annualized_return_pct"]:.1f}%')
                    st.markdown(f'{action_tag} &nbsp; Due: {r["due_date"]}', unsafe_allow_html=True)
                    st.markdown(f'*{r["reasoning"]}*')


# ═══════════════════════════════════════════════════════════
#  FX EXPOSURE
# ═══════════════════════════════════════════════════════════
elif page == "FX Exposure":
    st.markdown(f'<div class="top-bar"><div><div class="top-bar-title">FX Exposure</div><div class="top-bar-sub">Unhedged currency risk &middot; {NOW}</div></div></div>', unsafe_allow_html=True)

    data, err = run_safe(scan_fx_exposure, DATA)
    if err:
        st.error(err)
    elif data:
        c1, c2, c3 = st.columns(3)
        c1.metric("Unhedged (USD)", fmt(data.get("total_unhedged_usd", 0)))
        c2.metric("Value at Risk", fmt(data.get("total_var_usd", 0)))
        c3.metric("Largest Exposure", data.get("largest_single_exposure_currency", "—"))

        if data.get("exposures"):
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            df = pd.DataFrame(data["exposures"])
            for col in ["notional_amount","usd_equivalent","estimated_var_usd"]:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: f"${x:,.2f}")
            df.columns = [c.replace("_"," ").title() for c in df.columns]
            st.dataframe(df, use_container_width=True, hide_index=True)

        if data.get("recommendation"):
            st.info(data["recommendation"])


# ═══════════════════════════════════════════════════════════
#  COVENANTS
# ═══════════════════════════════════════════════════════════
elif page == "Covenants":
    st.markdown(f'<div class="top-bar"><div><div class="top-bar-title">Debt Covenants</div><div class="top-bar-sub">Compliance monitoring &middot; {NOW}</div></div></div>', unsafe_allow_html=True)

    data, err = run_safe(monitor_debt_covenants, DATA)
    if err:
        st.error(err)
    elif data:
        overall_tag = tag_html(data.get("overall_status", "unknown"))
        st.markdown(f'Overall: {overall_tag}', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        c1.metric("Warnings", data.get("warnings", 0))
        c2.metric("Breaches", data.get("breaches", 0))

        if data.get("covenants"):
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            for cov in data["covenants"]:
                c = dot_color(cov["status"])
                with st.expander(f'{cov["covenant_name"]} — {cov["headroom_pct"]:.1f}% headroom'):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Required", cov["required_threshold"])
                    c2.metric("Current", cov["current_value"])
                    c3.metric("Headroom", f'{cov["headroom_pct"]:.1f}%')
                    st.markdown(f'Status: {tag_html(cov["status"])} &nbsp;&nbsp; Type: {cov["covenant_type"]}', unsafe_allow_html=True)
                    if cov.get("next_test_date"):
                        st.caption(f'Next test: {cov["next_test_date"]}')

        if data.get("recommendation"):
            st.info(data["recommendation"])


# ═══════════════════════════════════════════════════════════
#  CREDIT REPORT
# ═══════════════════════════════════════════════════════════
elif page == "Credit Report":
    st.markdown(f'<div class="top-bar"><div><div class="top-bar-title">Credit Report</div><div class="top-bar-sub">What lenders see &middot; {NOW}</div></div></div>', unsafe_allow_html=True)

    data, err = run_safe(parse_credit_report, DATA)
    if err:
        st.error(err)
    elif data:
        if data.get("personal_profiles"):
            st.markdown("### Personal Credit")
            for p in data["personal_profiles"]:
                tier_tag = tag_html(p.get("score_tier","unknown"))
                with st.expander(f'{p["borrower_name"]} — FICO {p["credit_score"]}'):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Score", p["credit_score"])
                    c2.metric("Utilization", f'{p.get("revolving_utilization_pct",0):.1f}%')
                    c3.metric("Payment History", f'{p.get("payment_history_pct",0):.1f}%')
                    c4.metric("Derogatory", p.get("derogatory_marks",0))
                    st.markdown(f'Tier: {tier_tag}', unsafe_allow_html=True)

                    st.markdown(f"""<div class="stat-grid">
                        <div class="stat-item"><div class="stat-label">Open Tradelines</div><div class="stat-value">{p.get("open_tradelines","—")}</div></div>
                        <div class="stat-item"><div class="stat-label">Late 30d / 60d / 90d</div><div class="stat-value">{p.get("late_payments_30d",0)} / {p.get("late_payments_60d",0)} / {p.get("late_payments_90d",0)}</div></div>
                        <div class="stat-item"><div class="stat-label">Revolving Balance</div><div class="stat-value">{fmt(p.get("total_revolving_balance",0))}</div></div>
                        <div class="stat-item"><div class="stat-label">Collections</div><div class="stat-value">{p.get("collections",0)}</div></div>
                        <div class="stat-item"><div class="stat-label">Revolving Limit</div><div class="stat-value">{fmt(p.get("total_revolving_limit",0))}</div></div>
                        <div class="stat-item"><div class="stat-label">Bankruptcies</div><div class="stat-value">{p.get("bankruptcies",0)}</div></div>
                        <div class="stat-item"><div class="stat-label">Oldest Account</div><div class="stat-value">{p.get("oldest_account_years","—")} yrs</div></div>
                        <div class="stat-item"><div class="stat-label">Recent Inquiries</div><div class="stat-value">{p.get("recent_inquiries_6mo",0)}</div></div>
                    </div>""", unsafe_allow_html=True)

        if data.get("business_profile"):
            bp = data["business_profile"]
            st.markdown("### Business Credit")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Paydex", bp.get("paydex_score","—"))
            c2.metric("Years in Business", bp.get("years_in_business","—"))
            c3.metric("Current %", f'{bp.get("current_pct",0):.0f}%')
            c4.metric("Payment Trend", (bp.get("payment_trend","—") or "—").title())

            st.markdown(f"""<div class="card"><div class="stat-grid">
                <div class="stat-item"><div class="stat-label">Business</div><div class="stat-value">{bp.get("business_name","—")}</div></div>
                <div class="stat-item"><div class="stat-label">D&B Rating</div><div class="stat-value">{bp.get("d_and_b_rating","—")}</div></div>
                <div class="stat-item"><div class="stat-label">Industry</div><div class="stat-value">{bp.get("industry","—")}</div></div>
                <div class="stat-item"><div class="stat-label">Avg Days Beyond</div><div class="stat-value">{bp.get("days_beyond_terms_avg","—")}</div></div>
                <div class="stat-item"><div class="stat-label">Trade Experiences</div><div class="stat-value">{bp.get("total_trade_experiences","—")}</div></div>
                <div class="stat-item"><div class="stat-label">Liens / Judgments</div><div class="stat-value">{bp.get("liens",0)} / {bp.get("judgments",0)}</div></div>
                <div class="stat-item"><div class="stat-label">Derogatory</div><div class="stat-value">{bp.get("derogatory_count",0)}</div></div>
                <div class="stat-item"><div class="stat-label">UCC Filings</div><div class="stat-value">{bp.get("ucc_filings",0)}</div></div>
            </div></div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  CREDIT ASSESSMENT
# ═══════════════════════════════════════════════════════════
elif page == "Credit Assessment":
    st.markdown(f'<div class="top-bar"><div><div class="top-bar-title">Credit Assessment</div><div class="top-bar-sub">Full underwriting picture &middot; {NOW}</div></div></div>', unsafe_allow_html=True)

    income = st.number_input("Combined annual gross income ($)", min_value=0, value=0, step=25000,
                              help="For DTI calculation. Leave at 0 to skip.")

    data, err = run_safe(assess_credit_position, DATA, float(income))
    if err:
        st.error(err)
    elif data:
        rating_tag = tag_html(data.get("overall_credit_rating","unknown"))
        st.markdown(f'### Overall: {rating_tag}', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg FICO", f'{data.get("personal_score_avg",0):.0f}')
        c2.metric("Lowest FICO", f'{data.get("personal_score_lowest",0):.0f}')
        c3.metric("Business Paydex", data.get("business_paydex") or "—")
        guaranty = (data.get("personal_guaranty_strength","—") or "—").replace("_"," ").title()
        c4.metric("Guaranty", guaranty)

        if data.get("combined_debt_to_income") and data["combined_debt_to_income"] > 0:
            st.metric("DTI Ratio", f'{data["combined_debt_to_income"]:.1f}%')

        capacity = data.get("lending_capacity_estimate","—")
        st.markdown(f'<div class="card"><div class="card-header">Lending Capacity</div><div class="card-value">{capacity}</div></div>', unsafe_allow_html=True)

        if data.get("risk_factors"):
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.markdown("### Risk Factors")
            for rf in data["risk_factors"]:
                sev_tag = tag_html(rf["severity"])
                with st.expander(f'{rf["category"].replace("_"," ").title()} — {rf["finding"][:70]}'):
                    st.markdown(f'Severity: {sev_tag}', unsafe_allow_html=True)
                    st.markdown(f'**Impact:** {rf["impact"]}')
                    st.markdown(f'**Action:** {rf["recommendation"]}')

        if data.get("cross_sell_opportunities"):
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.markdown("### Opportunities")
            html = ""
            for opp in data["cross_sell_opportunities"]:
                html += f'<div class="status-row"><span class="status-dot green"></span><span class="status-label">{opp}</span></div>'
            st.markdown(f'<div class="card">{html}</div>', unsafe_allow_html=True)

        if data.get("recommendation"):
            st.info(data["recommendation"])


# ═══════════════════════════════════════════════════════════
#  WORKING CAPITAL
# ═══════════════════════════════════════════════════════════
elif page == "Working Capital":
    st.markdown(f'<div class="top-bar"><div><div class="top-bar-title">Working Capital</div><div class="top-bar-sub">Liquidity and efficiency analysis &middot; {NOW}</div></div></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        current_assets = st.number_input("Current Assets ($)", min_value=0, value=5_000_000, step=100_000)
        accounts_receivable = st.number_input("Accounts Receivable ($)", min_value=0, value=2_000_000, step=100_000)
        annual_revenue = st.number_input("Annual Revenue ($)", min_value=0, value=25_000_000, step=1_000_000)
    with c2:
        current_liabilities = st.number_input("Current Liabilities ($)", min_value=0, value=3_000_000, step=100_000)
        accounts_payable = st.number_input("Accounts Payable ($)", min_value=0, value=1_500_000, step=100_000)
        annual_cogs = st.number_input("Annual COGS ($)", min_value=0, value=18_000_000, step=1_000_000)

    if st.button("Analyze", type="primary"):
        data, err = run_safe(analyze_working_capital,
                             float(current_assets), float(current_liabilities),
                             float(annual_revenue), float(accounts_receivable),
                             float(accounts_payable), float(annual_cogs))
        if err:
            st.error(err)
        elif data:
            assessment_tag = tag_html(data.get("assessment","—"))
            st.markdown(f'Assessment: {assessment_tag}', unsafe_allow_html=True)

            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("Net Working Capital", fmt(data.get("net_working_capital",0)))
            c2.metric("Current Ratio", f'{data.get("current_ratio",0):.2f}x')
            c3.metric("Runway", f'{data.get("runway_days",0):.0f} days')

            c4, c5, c6 = st.columns(3)
            c4.metric("DSO", f'{data.get("days_sales_outstanding",0):.0f} days')
            c5.metric("DPO", f'{data.get("days_payable_outstanding",0):.0f} days')
            c6.metric("Cash Conversion", f'{data.get("cash_conversion_cycle_days",0):.0f} days')

            if data.get("runway_days", 999) < 90:
                st.warning(f'Runway is only {data["runway_days"]:.0f} days. Consider accelerating collections.')
