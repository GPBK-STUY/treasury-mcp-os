"""
TreasuryOS — Relationship Manager Portfolio Dashboard
Financial intelligence for managing a portfolio of business clients.
Run:  streamlit run rm_dashboard.py
"""

import streamlit as st
import pandas as pd
import os
import sys
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
st.set_page_config(page_title="TreasuryOS RM", page_icon="T", layout="wide", initial_sidebar_state="expanded")

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
    .stSlider label, .stNumberInput label, .stRadio label, .stFileUploader label, .stTextInput label, .stSelectbox label {{ color: {TEXT_SECONDARY} !important; font-size: 0.85rem !important; }}
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
    .client-card {{ background: {CARD_BG}; border: 1px solid {CARD_BORDER}; border-radius: 10px; padding: 1.5rem; margin-bottom: 1rem; cursor: pointer; transition: all 0.2s; }}
    .client-card:hover {{ border-color: {ACCENT}; box-shadow: 0 0 12px {ACCENT}20; }}
    .client-card-title {{ color: {TEXT_PRIMARY}; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem; }}
    .client-card-meta {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }}
    .client-card-tag {{ display: inline-block; padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.7rem; font-weight: 600; }}
    .client-card-stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }}
    .client-card-stat {{ display: flex; flex-direction: column; }}
    .client-card-stat-label {{ color: {TEXT_MUTED}; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; }}
    .client-card-stat-value {{ color: {TEXT_PRIMARY}; font-size: 1.1rem; font-weight: 600; margin-top: 0.25rem; }}
    .search-container {{ margin-bottom: 2rem; }}
</style>
""", unsafe_allow_html=True)


# ─── Session State ──────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Portfolio"
if "selected_client" not in st.session_state:
    st.session_state.selected_client = None
if "search_filter" not in st.session_state:
    st.session_state.search_filter = ""

PORTFOLIO_DATA_DIR = str(_DIR / "portfolio_data")


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

def load_clients():
    """Load all clients from clients.csv"""
    try:
        csv_path = os.path.join(PORTFOLIO_DATA_DIR, "clients.csv")
        df = pd.read_csv(csv_path)
        return df.to_dict('records')
    except Exception:
        return []

def get_client_slug(business_name):
    """Convert business name to slug - matches portfolio_data folder names"""
    # Remove company suffixes and special characters
    slug = business_name.lower().strip()
    # Remove common suffixes
    for suffix in [" corp", " corporation", " inc", " llc", " group", " co", " ltd"]:
        if slug.endswith(suffix):
            slug = slug[:-len(suffix)].strip()
    # Replace spaces with hyphens and remove special chars
    slug = slug.replace(" ", "-").replace("&", "and").replace(",", "").strip()
    return slug

def get_client_data_dir(client_slug):
    """Get the data directory for a client"""
    return os.path.join(PORTFOLIO_DATA_DIR, client_slug)

def calculate_total_aum(clients):
    """Calculate total AUM across all clients"""
    total = 0
    for client in clients:
        client_slug = get_client_slug(client['business_name'])
        data_dir = get_client_data_dir(client_slug)
        cash, _ = run_safe(get_cash_position, data_dir)
        if cash:
            total += cash.get("total_balance", 0)
    return total

def count_watch_clients(clients):
    """Count clients on watch list"""
    return sum(1 for c in clients if c.get('status', '').lower() == 'watch')


# ─── Sidebar ────────────────────────────────────────────────
# Determine default index from session state so button clicks carry over
_nav_options = ["Portfolio", "Client Profile"]
_nav_default = _nav_options.index(st.session_state.page) if st.session_state.page in _nav_options else 0

with st.sidebar:
    st.markdown("# T  TreasuryOS RM")
    st.markdown("---")

    st.markdown("### Navigation")
    nav_page = st.radio("nav", _nav_options, index=_nav_default, label_visibility="collapsed")
    # Only update if user clicked the radio (not overriding button navigation)
    if nav_page != _nav_options[_nav_default]:
        st.session_state.page = nav_page

    if st.session_state.page == "Client Profile":
        st.markdown("---")
        clients = load_clients()
        client_names = [c['business_name'] for c in clients]
        default_idx = client_names.index(st.session_state.selected_client) if st.session_state.selected_client in client_names else 0
        selected_name = st.selectbox("Select Client", client_names, index=default_idx, label_visibility="collapsed")
        st.session_state.selected_client = selected_name

    st.markdown("---")
    st.markdown(f'<p style="color:{TEXT_MUTED}; font-size:0.7rem; text-align:center;">TreasuryOS RM v0.1 &middot; <a href="https://github.com/GPBK-STUY/treasury-mcp-os" style="color:{TEXT_MUTED};">GitHub</a></p>', unsafe_allow_html=True)


# ─── Main ───────────────────────────────────────────────────
NOW = datetime.now().strftime("%b %d, %Y &middot; %I:%M %p")


# ═══════════════════════════════════════════════════════════
#  PORTFOLIO PAGE
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "Portfolio":
    st.markdown(f"""<div class="top-bar">
        <div><div class="top-bar-title">Portfolio Overview</div>
        <div class="top-bar-sub">Manage your client portfolio &middot; {NOW}</div></div>
    </div>""", unsafe_allow_html=True)

    clients = load_clients()

    # ── Search Bar ──
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    search = st.text_input("🔍 Search by business name, industry, or city", placeholder="Type to filter...", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    # Filter clients based on search
    filtered_clients = clients
    if search.strip():
        search_lower = search.lower()
        filtered_clients = [c for c in clients if (
            search_lower in c.get('business_name', '').lower() or
            search_lower in c.get('industry', '').lower() or
            search_lower in c.get('city', '').lower()
        )]

    # ── Top Metrics ──
    total_aum = calculate_total_aum(clients)
    watch_count = count_watch_clients(clients)

    # Calculate average credit rating from all clients
    ratings = []
    for client in clients:
        client_slug = get_client_slug(client['business_name'])
        data_dir = get_client_data_dir(client_slug)
        credit, _ = run_safe(assess_credit_position, data_dir)
        if credit and credit.get('overall_credit_rating'):
            ratings.append(credit['overall_credit_rating'])
    avg_rating = ratings[0] if ratings else "—"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card("Total Clients", len(clients), f"{len(filtered_clients)} shown"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("Total AUM", fmt(total_aum), f"{len(clients)} clients"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Clients on Watch", watch_count, f"{watch_count/len(clients)*100:.0f}% of portfolio"), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card("Avg Credit Rating", avg_rating if isinstance(avg_rating, str) else tag_html(avg_rating)), unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Client Cards Grid ──
    st.markdown("### Clients")

    for client in filtered_clients:
        client_slug = get_client_slug(client['business_name'])
        data_dir = get_client_data_dir(client_slug)

        # Fetch client-specific data
        cash, _ = run_safe(get_cash_position, data_dir)
        cov, _ = run_safe(monitor_debt_covenants, data_dir)
        credit, _ = run_safe(assess_credit_position, data_dir)

        client_aum = cash.get("total_balance", 0) if cash else 0
        covenant_status = cov.get("overall_status", "unknown") if cov else "unknown"
        credit_rating = credit.get("overall_credit_rating", "unknown") if credit else "unknown"

        # Use native Streamlit container for reliable rendering
        with st.container():
            st.markdown(f"""<div class="card" style="margin-bottom:0.5rem;">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">
<span style="color:{TEXT_PRIMARY};font-size:1.1rem;font-weight:600;">{client['business_name']}</span>
{tag_html(client.get('status','active'))}
</div></div>""", unsafe_allow_html=True)

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.caption("INDUSTRY")
            c1.markdown(f"**{client.get('industry','—')}**")
            c2.caption("LOCATION")
            c2.markdown(f"**{client.get('city','—')}, {client.get('state','—')}**")
            c3.caption("TOTAL CASH")
            c3.markdown(f"**{fmt(client_aum)}**")
            c4.caption("COVENANTS")
            c4.markdown(f"{status_html(covenant_status)}", unsafe_allow_html=True)
            c5.caption("CREDIT")
            c5.markdown(f"{status_html(credit_rating)}", unsafe_allow_html=True)

            btn_col1, btn_col2, btn_col3 = st.columns([3, 1, 1])
            with btn_col2:
                if st.button("View Profile", key=f"btn_{client_slug}", use_container_width=True):
                    st.session_state.page = "Client Profile"
                    st.session_state.selected_client = client['business_name']
                    st.rerun()

            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  CLIENT PROFILE PAGE
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "Client Profile":
    if st.session_state.selected_client:
        clients = load_clients()
        client = next((c for c in clients if c['business_name'] == st.session_state.selected_client), None)

        if client:
            client_slug = get_client_slug(client['business_name'])
            DATA = get_client_data_dir(client_slug)

            # ── Header ──
            st.markdown(f"# {client['business_name']}")
            hc1, hc2, hc3, hc4 = st.columns(4)
            hc1.markdown(f"**Industry:** {client.get('industry', '—')}")
            hc2.markdown(f"**Status:** {client.get('status', 'active').title()}")
            hc3.markdown(f"**Location:** {client.get('city', '—')}, {client.get('state', '—')}")
            hc4.markdown(f"**Last Review:** {client.get('last_review', '—')}")
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            # ── Tab Navigation ──
            tabs = st.tabs([
                "Overview", "Cash Position", "Idle Cash", "Cash Forecast",
                "Payments", "FX Exposure", "Covenants",
                "Credit Report", "Credit Assessment", "Working Capital",
                "Financing Readiness"
            ])

            # ════════════════════════════════════════════════════════════════
            # OVERVIEW TAB
            # ════════════════════════════════════════════════════════════════
            with tabs[0]:
                st.markdown(f'<div class="top-bar-sub">Financial snapshot &middot; {NOW}</div>', unsafe_allow_html=True)

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

            # ════════════════════════════════════════════════════════════════
            # CASH POSITION TAB
            # ════════════════════════════════════════════════════════════════
            with tabs[1]:
                st.markdown(f'<div class="top-bar-sub">Balances across all accounts &middot; {NOW}</div>', unsafe_allow_html=True)

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

            # ════════════════════════════════════════════════════════════════
            # IDLE CASH TAB
            # ════════════════════════════════════════════════════════════════
            with tabs[2]:
                st.markdown(f'<div class="top-bar-sub">Money sitting in low-yield accounts &middot; {NOW}</div>', unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                reserve = c1.slider("Operating Reserve %", 5, 50, 20, 5, key="idle_reserve") / 100
                target = c2.slider("Target Yield (bps)", 100, 600, 450, 50, key="idle_target")

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

            # ════════════════════════════════════════════════════════════════
            # CASH FORECAST TAB
            # ════════════════════════════════════════════════════════════════
            with tabs[3]:
                st.markdown(f'<div class="top-bar-sub">Projected cash position &middot; {NOW}</div>', unsafe_allow_html=True)

                horizon = st.slider("Forecast Horizon (days)", 30, 365, 90, 30, key="forecast_horizon")
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

            # ════════════════════════════════════════════════════════════════
            # PAYMENTS TAB
            # ════════════════════════════════════════════════════════════════
            with tabs[4]:
                st.markdown(f'<div class="top-bar-sub">Early-pay discount analysis &middot; {NOW}</div>', unsafe_allow_html=True)

                budget = st.number_input("Available cash for early payments ($)", min_value=0, value=0, step=10000, key="payment_budget")
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

            # ════════════════════════════════════════════════════════════════
            # FX EXPOSURE TAB
            # ════════════════════════════════════════════════════════════════
            with tabs[5]:
                st.markdown(f'<div class="top-bar-sub">Unhedged currency risk &middot; {NOW}</div>', unsafe_allow_html=True)

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

            # ════════════════════════════════════════════════════════════════
            # COVENANTS TAB
            # ════════════════════════════════════════════════════════════════
            with tabs[6]:
                st.markdown(f'<div class="top-bar-sub">Compliance monitoring &middot; {NOW}</div>', unsafe_allow_html=True)

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

            # ════════════════════════════════════════════════════════════════
            # CREDIT REPORT TAB
            # ════════════════════════════════════════════════════════════════
            with tabs[7]:
                st.markdown(f'<div class="top-bar-sub">What lenders see &middot; {NOW}</div>', unsafe_allow_html=True)

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

            # ════════════════════════════════════════════════════════════════
            # CREDIT ASSESSMENT TAB
            # ════════════════════════════════════════════════════════════════
            with tabs[8]:
                st.markdown(f'<div class="top-bar-sub">Full underwriting picture &middot; {NOW}</div>', unsafe_allow_html=True)

                income = st.number_input("Combined annual gross income ($)", min_value=0, value=0, step=25000, key="credit_income",
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

            # ════════════════════════════════════════════════════════════════
            # WORKING CAPITAL TAB
            # ════════════════════════════════════════════════════════════════
            with tabs[9]:
                st.markdown(f'<div class="top-bar-sub">Liquidity and efficiency analysis &middot; {NOW}</div>', unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    current_assets = st.number_input("Current Assets ($)", min_value=0, value=5_000_000, step=100_000, key="wc_ca")
                    accounts_receivable = st.number_input("Accounts Receivable ($)", min_value=0, value=2_000_000, step=100_000, key="wc_ar")
                    annual_revenue = st.number_input("Annual Revenue ($)", min_value=0, value=25_000_000, step=1_000_000, key="wc_ar_rev")
                with c2:
                    current_liabilities = st.number_input("Current Liabilities ($)", min_value=0, value=3_000_000, step=100_000, key="wc_cl")
                    accounts_payable = st.number_input("Accounts Payable ($)", min_value=0, value=1_500_000, step=100_000, key="wc_ap")
                    annual_cogs = st.number_input("Annual COGS ($)", min_value=0, value=18_000_000, step=1_000_000, key="wc_cogs")

                if st.button("Analyze", type="primary", key="wc_analyze"):
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
                            st.warning(f'Low runway ({data.get("runway_days", 0):.0f} days). Consider improving collections or negotiating payment terms.')

                        if data.get("recommendations"):
                            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                            st.markdown("### Recommendations")
                            for rec in data["recommendations"]:
                                st.markdown(f'• {rec}')

            # ════════════════════════════════════════════════════════════════
            # FINANCING READINESS TAB
            # ════════════════════════════════════════════════════════════════
            with tabs[10]:
                st.markdown(f'<div class="top-bar-sub">How a bank will evaluate this client &middot; {NOW}</div>', unsafe_allow_html=True)

                # Collect all data for this client
                fr_cash, _ = run_safe(get_cash_position, DATA)
                fr_idle, _ = run_safe(scan_idle_balances, DATA)
                fr_cov, _ = run_safe(monitor_debt_covenants, DATA)
                fr_credit, _ = run_safe(parse_credit_report, DATA)
                fr_assessment, _ = run_safe(assess_credit_position, DATA)

                # ── Scoring Engine ──
                scores = {}

                # 1. Personal Credit (25%)
                pc_score = 0
                pc_findings = []
                pc_actions = []
                if fr_credit and fr_credit.get("personal_profiles"):
                    p = fr_credit["personal_profiles"][0]
                    fico = p.get("credit_score", 0)
                    util = p.get("revolving_utilization_pct", 100)
                    derogs = p.get("derogatory_marks", 0)
                    late30 = p.get("late_payments_30d", 0)
                    late60 = p.get("late_payments_60d", 0)
                    late90 = p.get("late_payments_90d", 0)
                    if fico >= 750: pc_score += 40; pc_findings.append(f"FICO {fico} — excellent")
                    elif fico >= 700: pc_score += 30; pc_findings.append(f"FICO {fico} — good")
                    elif fico >= 680: pc_score += 20; pc_findings.append(f"FICO {fico} — fair")
                    elif fico >= 640: pc_score += 10; pc_findings.append(f"FICO {fico} — below threshold"); pc_actions.append("Raise FICO above 680")
                    else: pc_findings.append(f"FICO {fico} — limited options"); pc_actions.append("Improve FICO above 640")
                    if util <= 20: pc_score += 25
                    elif util <= 30: pc_score += 20
                    elif util <= 50: pc_score += 10; pc_actions.append(f"Reduce utilization from {util:.0f}% to under 30%")
                    else: pc_actions.append(f"Utilization {util:.0f}% — needs to be under 30%")
                    total_lates = late30 + late60 + late90
                    if total_lates == 0 and derogs == 0: pc_score += 25
                    elif total_lates <= 1: pc_score += 15
                    else:
                        if derogs > 0: pc_actions.append(f"{derogs} derogatory marks — address before financing")
                    inquiries = p.get("recent_inquiries_6mo", 0)
                    if inquiries <= 2: pc_score += 10
                    elif inquiries <= 4: pc_score += 5
                else:
                    pc_findings.append("No personal credit data loaded")
                scores["Personal Credit"] = {"score": pc_score, "weight": 0.25, "findings": pc_findings, "actions": pc_actions}

                # 2. Business Credit (20%)
                bc_score = 0
                bc_findings = []
                bc_actions = []
                if fr_credit and fr_credit.get("business_profile"):
                    bp = fr_credit["business_profile"]
                    paydex = bp.get("paydex_score", 0)
                    yrs = bp.get("years_in_business", 0)
                    dbt = bp.get("days_beyond_terms_avg", 99)
                    liens = bp.get("liens", 0)
                    judgments = bp.get("judgments", 0)
                    if paydex >= 80: bc_score += 35; bc_findings.append(f"Paydex {paydex} — strong")
                    elif paydex >= 70: bc_score += 25; bc_findings.append(f"Paydex {paydex} — good")
                    elif paydex >= 50: bc_score += 10; bc_actions.append(f"Boost Paydex from {paydex} above 70")
                    else: bc_actions.append(f"Paydex {paydex} — needs vendor trade lines")
                    if yrs >= 5: bc_score += 25; bc_findings.append(f"{yrs} years in business")
                    elif yrs >= 2: bc_score += 15; bc_findings.append(f"{yrs} years — meets most minimums")
                    elif yrs >= 1: bc_score += 5; bc_actions.append("Consider SBA for newer businesses")
                    if dbt <= 5: bc_score += 20
                    elif dbt <= 15: bc_score += 10
                    else: bc_actions.append(f"Days beyond terms: {dbt:.0f} — needs improvement")
                    if liens == 0 and judgments == 0: bc_score += 20
                    else:
                        if judgments > 0: bc_actions.append(f"{judgments} judgment(s) — must resolve")
                        if liens > 0: bc_actions.append(f"{liens} lien(s) — needs attention")
                else:
                    bc_findings.append("No business credit data loaded")
                scores["Business Credit"] = {"score": bc_score, "weight": 0.20, "findings": bc_findings, "actions": bc_actions}

                # 3. Cash Position (20%)
                cp_score = 0
                cp_findings = []
                cp_actions = []
                if fr_cash:
                    total_cash = fr_cash.get("total_balance", 0)
                    if total_cash >= 500_000: cp_score += 40; cp_findings.append(f"Cash {fmt(total_cash)} — strong")
                    elif total_cash >= 100_000: cp_score += 25; cp_findings.append(f"Cash {fmt(total_cash)} — adequate")
                    elif total_cash >= 25_000: cp_score += 10; cp_actions.append("Build cash reserves")
                    else: cp_actions.append("Cash position is thin")
                    num_accts = len(fr_cash.get("accounts", []))
                    if num_accts >= 2: cp_score += 10
                    if fr_idle:
                        idle_pct = fr_idle.get("total_idle_cash", 0) / max(total_cash, 1) * 100
                        if idle_pct < 20: cp_score += 20
                        elif idle_pct < 50: cp_score += 10; cp_actions.append("Optimize idle cash allocation")
                    forecast_data, _ = run_safe(forecast_cash_position, DATA, 90)
                    if forecast_data and forecast_data.get("projections"):
                        last = forecast_data["projections"][-1]
                        if last.get("ending_balance", 0) >= total_cash * 0.9: cp_score += 30
                        elif last.get("ending_balance", 0) >= total_cash * 0.7: cp_score += 15
                        else: cp_actions.append("Cash forecast shows decline")
                else:
                    cp_findings.append("No cash data loaded")
                scores["Cash & Runway"] = {"score": cp_score, "weight": 0.20, "findings": cp_findings, "actions": cp_actions}

                # 4. Existing Debt (10%)
                debt_score = 0
                debt_findings = []
                debt_actions = []
                if fr_cov:
                    breaches = fr_cov.get("breaches", 0)
                    warnings = fr_cov.get("warnings", 0)
                    if breaches == 0 and warnings == 0: debt_score = 100; debt_findings.append("All covenants compliant")
                    elif breaches == 0: debt_score = 60; debt_findings.append(f"{warnings} warning(s)"); debt_actions.append("Improve covenant headroom")
                    else: debt_findings.append(f"{breaches} breach(es)"); debt_actions.append("Resolve breaches before new financing")
                else:
                    debt_score = 70; debt_findings.append("No existing debt on file")
                scores["Existing Debt"] = {"score": debt_score, "weight": 0.10, "findings": debt_findings, "actions": debt_actions}

                # 5. Working Capital (15%) — use client's annual_revenue from clients.csv
                wc_score = 50  # Default moderate score without WC data
                wc_findings = ["Working capital analysis requires manual input"]
                wc_actions = []
                scores["Working Capital"] = {"score": wc_score, "weight": 0.15, "findings": wc_findings, "actions": wc_actions}

                # 6. Documentation (10%)
                doc_score = 0
                doc_checklist = {
                    "Bank statements": fr_cash is not None,
                    "Personal credit": fr_credit is not None and bool(fr_credit.get("personal_profiles")),
                    "Business credit": fr_credit is not None and bool(fr_credit.get("business_profile")),
                    "Debt schedule": fr_cov is not None,
                    "Vendor data": fr_idle is not None,
                }
                docs_present = sum(1 for v in doc_checklist.values() if v)
                doc_score = int((docs_present / len(doc_checklist)) * 100)
                doc_findings = [f"{docs_present}/{len(doc_checklist)} key data sources loaded"]
                doc_actions = []
                missing_docs = [k for k, v in doc_checklist.items() if not v]
                if missing_docs:
                    doc_actions.append(f"Missing: {', '.join(missing_docs)}")
                scores["Documentation"] = {"score": doc_score, "weight": 0.10, "findings": doc_findings, "actions": doc_actions}

                # ── Calculate Overall Score ──
                overall_score = min(sum(s["score"] * s["weight"] for s in scores.values()), 100)
                if overall_score >= 75: overall_status = "strong"
                elif overall_score >= 55: overall_status = "fair"
                elif overall_score >= 35: overall_status = "needs_work"
                else: overall_status = "not_ready"

                score_color = GREEN if overall_score >= 75 else YELLOW if overall_score >= 50 else RED

                # ── Display Score ──
                st.markdown(f"""<div class="card" style="text-align:center;padding:2rem;">
<div class="card-header">FINANCING READINESS SCORE</div>
<div style="font-size:4rem;font-weight:800;color:{score_color};line-height:1;">{overall_score:.0f}</div>
<div style="font-size:1rem;color:{TEXT_SECONDARY};margin-top:0.5rem;">out of 100</div>
<div style="margin-top:1rem;">{tag_html(overall_status)}</div>
</div>""", unsafe_allow_html=True)

                # ── Category Breakdown ──
                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                st.markdown("### Category Scores")

                for cat_name, cat_data in scores.items():
                    cat_score = cat_data["score"]
                    cat_weight = cat_data["weight"]
                    if cat_score >= 70: cat_status = "strong"
                    elif cat_score >= 40: cat_status = "fair"
                    else: cat_status = "weak"

                    with st.expander(f"{cat_name} — {cat_score}/100 ({cat_weight*100:.0f}% weight)"):
                        ec1, ec2, ec3 = st.columns(3)
                        ec1.metric("Raw Score", f"{cat_score}/100")
                        ec2.metric("Weight", f"{cat_weight*100:.0f}%")
                        ec3.metric("Weighted", f"{cat_score * cat_weight:.0f} pts")
                        if cat_data["findings"]:
                            findings_html = ""
                            for f in cat_data["findings"]:
                                findings_html += status_html(cat_status, f)
                            st.markdown(f'<div class="card">{findings_html}</div>', unsafe_allow_html=True)
                        if cat_data["actions"]:
                            st.markdown("**Action Items:**")
                            for a in cat_data["actions"]:
                                st.markdown(f"- {a}")

                # ── Top Actions ──
                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                st.markdown("### Top Actions Before Financing")

                all_actions = []
                for cat in ["Personal Credit", "Business Credit", "Cash & Runway", "Existing Debt", "Working Capital", "Documentation"]:
                    if cat in scores:
                        for act in scores[cat]["actions"]:
                            all_actions.append({"category": cat, "action": act, "score": scores[cat]["score"]})
                all_actions.sort(key=lambda x: x["score"])

                if all_actions:
                    for i, item in enumerate(all_actions[:8], 1):
                        urgency = "weak" if item["score"] < 30 else "fair" if item["score"] < 60 else "strong"
                        action_text = item["action"]
                        cat_text = item["category"]
                        st.markdown(status_html(urgency, f"{i}. {action_text}", cat_text), unsafe_allow_html=True)
                else:
                    st.markdown(status_html("strong", "Client looks ready for financing"), unsafe_allow_html=True)

                # ── Loan Product Match ──
                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                st.markdown("### Likely Products")

                fico_val = 0
                if fr_credit and fr_credit.get("personal_profiles"):
                    fico_val = fr_credit["personal_profiles"][0].get("credit_score", 0)
                paydex_val = 0
                yrs_biz = 0
                if fr_credit and fr_credit.get("business_profile"):
                    paydex_val = fr_credit["business_profile"].get("paydex_score", 0)
                    yrs_biz = fr_credit["business_profile"].get("years_in_business", 0)
                has_breach = fr_cov.get("breaches", 0) > 0 if fr_cov else False

                products = []
                if fico_val >= 680 and yrs_biz >= 2 and not has_breach:
                    rate = "Prime + 1-3%" if fico_val >= 720 else "Prime + 2-5%"
                    products.append(("Conventional LOC", "strong", rate))
                elif fico_val >= 640:
                    products.append(("Conventional LOC", "fair", "Prime + 3-6%"))
                if fico_val >= 640 and yrs_biz >= 1:
                    products.append(("SBA 7(a)", "strong" if fico_val >= 680 else "fair", "Prime + 2.25-4.75%"))
                products.append(("SBA Microloan", "strong", "6-9%"))
                if fico_val >= 600:
                    products.append(("Equipment Financing", "strong" if fico_val >= 680 else "fair", "5-15%"))
                products.append(("Invoice Factoring", "fair", "1-5% per invoice"))
                if fico_val >= 700 and yrs_biz >= 3 and not has_breach:
                    products.append(("Term Loan", "strong", "Prime + 1-4%"))

                for name, likelihood, rate in products:
                    st.markdown(f'{status_html(likelihood, name, rate)}', unsafe_allow_html=True)
