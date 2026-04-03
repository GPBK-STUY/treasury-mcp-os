"""
TreasuryOS — Web Dashboard
Financial intelligence for commercial banking and business owners.
Run:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os
import sys
import io
import re
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
        if hasattr(f, 'getbuffer'):
            with open(os.path.join(d, name), "wb") as out:
                out.write(f.getbuffer())
        elif isinstance(f, bytes):
            with open(os.path.join(d, name), "wb") as out:
                out.write(f)
    return d


# ─── File Type Keywords → CSV Mapping ──────────────────────
_FILE_MAP_KEYWORDS = {
    "accounts.csv":          ["account", "balance", "bank", "checking", "savings", "deposit"],
    "transactions.csv":      ["transaction", "debit", "credit", "payment", "transfer", "date", "amount"],
    "vendors.csv":           ["vendor", "supplier", "payable", "invoice", "due_date", "discount"],
    "covenants.csv":         ["covenant", "ratio", "threshold", "compliance", "facility", "debt"],
    "fx_rates.csv":          ["currency", "exchange", "rate", "fx", "eur", "gbp", "jpy", "usd"],
    "personal_credit.csv":   ["fico", "credit_score", "utilization", "derogatory", "late_payment", "personal"],
    "business_credit.csv":   ["paydex", "dbt", "lien", "judgment", "years_in_business", "business"],
}

def _guess_csv_type(df, original_name=""):
    """Guess which TreasuryOS CSV type a dataframe matches based on column names."""
    cols_lower = {c.lower().replace(" ", "_") for c in df.columns}
    name_lower = original_name.lower()

    best_match = None
    best_score = 0

    for target_csv, keywords in _FILE_MAP_KEYWORDS.items():
        score = 0
        # Check column names
        for kw in keywords:
            if any(kw in col for col in cols_lower):
                score += 2
        # Check original filename
        target_base = target_csv.replace(".csv", "")
        if target_base in name_lower:
            score += 5
        if score > best_score:
            best_score = score
            best_match = target_csv

    return best_match if best_score >= 2 else None


def _parse_excel(file_bytes, filename):
    """Parse Excel file into dict of {csv_name: csv_bytes}."""
    results = {}
    try:
        import openpyxl
        xls = pd.ExcelFile(io.BytesIO(file_bytes), engine="openpyxl")
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            if df.empty:
                continue
            csv_type = _guess_csv_type(df, f"{filename}_{sheet}")
            if csv_type and csv_type not in results:
                buf = io.BytesIO()
                df.to_csv(buf, index=False)
                results[csv_type] = buf.getvalue()
        # If single sheet and no match, try filename
        if not results and len(xls.sheet_names) == 1:
            df = pd.read_excel(xls, sheet_name=0)
            csv_type = _guess_csv_type(df, filename)
            if csv_type:
                buf = io.BytesIO()
                df.to_csv(buf, index=False)
                results[csv_type] = buf.getvalue()
    except Exception:
        pass
    return results


def _parse_pdf(file_bytes, filename):
    """Extract tables from PDF and map to CSV types."""
    results = {}
    try:
        import pdfplumber
        pdf = pdfplumber.open(io.BytesIO(file_bytes))
        for i, pg in enumerate(pdf.pages):
            tables = pg.extract_tables()
            for j, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue
                df = pd.DataFrame(table[1:], columns=table[0])
                csv_type = _guess_csv_type(df, f"{filename}_p{i}_t{j}")
                if csv_type and csv_type not in results:
                    buf = io.BytesIO()
                    df.to_csv(buf, index=False)
                    results[csv_type] = buf.getvalue()
        pdf.close()
    except Exception:
        pass
    return results


def _parse_docx(file_bytes, filename):
    """Extract tables from Word doc and map to CSV types."""
    results = {}
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        for j, table in enumerate(doc.tables):
            rows = []
            for row in table.rows:
                rows.append([cell.text.strip() for cell in row.cells])
            if len(rows) < 2:
                continue
            df = pd.DataFrame(rows[1:], columns=rows[0])
            csv_type = _guess_csv_type(df, f"{filename}_t{j}")
            if csv_type and csv_type not in results:
                buf = io.BytesIO()
                df.to_csv(buf, index=False)
                results[csv_type] = buf.getvalue()
    except Exception:
        pass
    return results


def parse_uploaded_files(uploaded_files):
    """Parse multiple uploaded files (CSV, Excel, Word, PDF) into a dict of {csv_name: bytes}."""
    all_csvs = {}
    for uf in uploaded_files:
        fname = uf.name.lower()
        raw = uf.read()
        uf.seek(0)  # Reset for potential re-read

        if fname.endswith(".csv"):
            try:
                df = pd.read_csv(io.BytesIO(raw))
                csv_type = _guess_csv_type(df, uf.name)
                if csv_type and csv_type not in all_csvs:
                    all_csvs[csv_type] = raw
                elif csv_type is None:
                    # Fallback: use the original filename
                    safe_name = re.sub(r'[^a-z0-9_.]', '_', fname)
                    all_csvs[safe_name] = raw
            except Exception:
                pass

        elif fname.endswith((".xlsx", ".xls")):
            parsed = _parse_excel(raw, uf.name)
            for k, v in parsed.items():
                if k not in all_csvs:
                    all_csvs[k] = v

        elif fname.endswith(".pdf"):
            parsed = _parse_pdf(raw, uf.name)
            for k, v in parsed.items():
                if k not in all_csvs:
                    all_csvs[k] = v

        elif fname.endswith(".docx"):
            parsed = _parse_docx(raw, uf.name)
            for k, v in parsed.items():
                if k not in all_csvs:
                    all_csvs[k] = v

    return all_csvs


# ─── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# T  TreasuryOS")
    st.markdown("---")

    st.markdown("### Data Source")
    src = st.radio("src", ["Demo Data", "Upload Files"], label_visibility="collapsed")

    if src == "Upload Files":
        st.session_state.using_sample = False
        st.markdown(f'<p style="color:{TEXT_SECONDARY};font-size:0.8rem;">Upload your financial documents — CSV, Excel, Word, or PDF. We\'ll auto-detect the content type.</p>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Drop files here",
            type=["csv", "xlsx", "xls", "docx", "pdf"],
            accept_multiple_files=True,
            key="multi_upload"
        )
        if uploaded_files:
            parsed_csvs = parse_uploaded_files(uploaded_files)
            if parsed_csvs:
                st.session_state.data_dir = save_uploads(parsed_csvs)
                st.session_state.uploaded_files = parsed_csvs
                st.success(f"Loaded {len(parsed_csvs)} data file(s)")
                for fname in parsed_csvs:
                    st.caption(f"  {fname}")
    else:
        st.session_state.using_sample = True
        st.session_state.data_dir = str(_DIR / "sample_data")

    st.markdown("---")
    st.markdown("### Navigation")
    page = st.radio("nav", [
        "Financing Readiness",
        "Overview", "Cash Position", "Idle Cash", "Cash Forecast",
        "Payments", "FX Exposure", "Covenants",
        "Credit Report", "Credit Assessment", "Working Capital",
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


# ═══════════════════════════════════════════════════════════
#  FINANCING READINESS
# ═══════════════════════════════════════════════════════════
elif page == "Financing Readiness":
    st.markdown(f'<div class="top-bar"><div><div class="top-bar-title">Financing Readiness</div><div class="top-bar-sub">How a bank will evaluate your business &middot; {NOW}</div></div></div>', unsafe_allow_html=True)

    # ── Getting Started guide for new users ──
    if st.session_state.get("using_sample", True):
        st.info(
            "**Getting Started:** You're viewing demo data. To see your own readiness score, "
            "switch to **Upload Files** in the sidebar and drop in your financial documents "
            "(bank statements, credit reports, etc.). We accept CSV, Excel, Word, and PDF files."
        )

    # ── Collect all data ──
    cash, cash_e = run_safe(get_cash_position, DATA)
    idle, idle_e = run_safe(scan_idle_balances, DATA)
    cov, cov_e = run_safe(monitor_debt_covenants, DATA)
    credit, credit_e = run_safe(parse_credit_report, DATA)
    assessment, assess_e = run_safe(assess_credit_position, DATA)

    # ── Optional working capital inputs ──
    with st.expander("Enter Working Capital Details (optional — improves accuracy)"):
        wc_c1, wc_c2 = st.columns(2)
        with wc_c1:
            fr_current_assets = st.number_input("Current Assets ($)", min_value=0, value=0, step=100_000, key="fr_ca")
            fr_accounts_receivable = st.number_input("Accounts Receivable ($)", min_value=0, value=0, step=100_000, key="fr_ar")
            fr_annual_revenue = st.number_input("Annual Revenue ($)", min_value=0, value=0, step=500_000, key="fr_rev")
        with wc_c2:
            fr_current_liabilities = st.number_input("Current Liabilities ($)", min_value=0, value=0, step=100_000, key="fr_cl")
            fr_accounts_payable = st.number_input("Accounts Payable ($)", min_value=0, value=0, step=100_000, key="fr_ap")
            fr_annual_cogs = st.number_input("Annual COGS ($)", min_value=0, value=0, step=500_000, key="fr_cogs")

    wc_data = None
    if fr_current_assets > 0 and fr_current_liabilities > 0 and fr_annual_revenue > 0:
        wc_data, _ = run_safe(analyze_working_capital,
                              float(fr_current_assets), float(fr_current_liabilities),
                              float(fr_annual_revenue), float(fr_accounts_receivable),
                              float(fr_accounts_payable), float(fr_annual_cogs))

    # ════════════════════════════════════════════════════════
    #  SCORING ENGINE
    # ════════════════════════════════════════════════════════
    scores = {}       # category -> {"score": 0-100, "weight": float, "status": str, "findings": [str], "actions": [str]}
    max_score = 100

    # ── 1. Personal Credit (25%) ──
    pc_score = 0
    pc_findings = []
    pc_actions = []
    if credit and credit.get("personal_profiles"):
        p = credit["personal_profiles"][0]
        fico = p.get("credit_score", 0)
        util = p.get("revolving_utilization_pct", 100)
        derogs = p.get("derogatory_marks", 0)
        late30 = p.get("late_payments_30d", 0)
        late60 = p.get("late_payments_60d", 0)
        late90 = p.get("late_payments_90d", 0)

        # FICO scoring (0-40 pts)
        if fico >= 750: pc_score += 40; pc_findings.append(f"FICO {fico} — excellent, qualifies for best rates")
        elif fico >= 700: pc_score += 30; pc_findings.append(f"FICO {fico} — good, qualifies for conventional lending")
        elif fico >= 680: pc_score += 20; pc_findings.append(f"FICO {fico} — fair, may face higher rates")
        elif fico >= 640: pc_score += 10; pc_findings.append(f"FICO {fico} — below threshold for most conventional loans"); pc_actions.append("Focus on raising FICO above 680 before applying — pay down balances, dispute errors")
        else: pc_findings.append(f"FICO {fico} — will limit you to SBA or secured lending"); pc_actions.append("Delay financing applications until FICO improves above 640")

        # Utilization (0-25 pts)
        if util <= 20: pc_score += 25; pc_findings.append(f"Utilization {util:.0f}% — excellent")
        elif util <= 30: pc_score += 20; pc_findings.append(f"Utilization {util:.0f}% — good")
        elif util <= 50: pc_score += 10; pc_findings.append(f"Utilization {util:.0f}% — banks prefer under 30%"); pc_actions.append(f"Pay down revolving balances to get utilization under 30% (currently {util:.0f}%)")
        else: pc_findings.append(f"Utilization {util:.0f}% — too high, will hurt your application"); pc_actions.append(f"Reduce revolving utilization from {util:.0f}% to under 30% before applying")

        # Payment history (0-25 pts)
        total_lates = late30 + late60 + late90
        if total_lates == 0 and derogs == 0: pc_score += 25; pc_findings.append("Clean payment history — no lates or derogatory marks")
        elif total_lates <= 1 and derogs == 0: pc_score += 15; pc_findings.append(f"{total_lates} late payment on file")
        else:
            if total_lates > 0: pc_findings.append(f"{total_lates} late payments ({late30}x30d, {late60}x60d, {late90}x90d)")
            if derogs > 0: pc_findings.append(f"{derogs} derogatory mark(s) on file"); pc_actions.append("Address derogatory marks — negotiate pay-for-delete or dispute inaccuracies")

        # Inquiries (0-10 pts)
        inquiries = p.get("recent_inquiries_6mo", 0)
        if inquiries <= 2: pc_score += 10
        elif inquiries <= 4: pc_score += 5; pc_findings.append(f"{inquiries} recent inquiries — banks may see you as rate-shopping")
        else: pc_findings.append(f"{inquiries} recent inquiries — stop applying for credit until you're ready"); pc_actions.append("Avoid new credit applications for 6 months before applying for business financing")
    else:
        pc_findings.append("No personal credit data loaded")
        pc_actions.append("Upload your personal credit report to get a full readiness assessment")

    scores["Personal Credit"] = {"score": pc_score, "weight": 0.25, "findings": pc_findings, "actions": pc_actions}

    # ── 2. Business Credit (20%) ──
    bc_score = 0
    bc_findings = []
    bc_actions = []
    if credit and credit.get("business_profile"):
        bp = credit["business_profile"]
        paydex = bp.get("paydex_score", 0)
        yrs = bp.get("years_in_business", 0)
        dbt = bp.get("days_beyond_terms_avg", 99)
        derogs_biz = bp.get("derogatory_count", 0)
        liens = bp.get("liens", 0)
        judgments = bp.get("judgments", 0)

        # Paydex (0-35 pts)
        if paydex >= 80: bc_score += 35; bc_findings.append(f"Paydex {paydex} — strong, pays on or ahead of terms")
        elif paydex >= 70: bc_score += 25; bc_findings.append(f"Paydex {paydex} — good but room to improve")
        elif paydex >= 50: bc_score += 10; bc_findings.append(f"Paydex {paydex} — below average"); bc_actions.append("Pay all vendors early or on time for 3-6 months to boost Paydex above 70")
        else: bc_findings.append(f"Paydex {paydex} — poor, banks will flag this"); bc_actions.append("Establish vendor trade lines that report to D&B and pay them early")

        # Years in business (0-25 pts)
        if yrs >= 5: bc_score += 25; bc_findings.append(f"{yrs} years in business — meets all lender minimums")
        elif yrs >= 2: bc_score += 15; bc_findings.append(f"{yrs} years in business — meets most conventional lender minimums")
        elif yrs >= 1: bc_score += 5; bc_findings.append(f"{yrs} year(s) — some lenders require 2+ years"); bc_actions.append("Consider SBA microloans or community lenders who serve newer businesses")
        else: bc_findings.append("Under 1 year — most conventional lenders require 2+ years"); bc_actions.append("Build operating history before applying — focus on SBA Microloans or startup-friendly lenders")

        # Days beyond terms (0-20 pts)
        if dbt <= 5: bc_score += 20
        elif dbt <= 15: bc_score += 10; bc_findings.append(f"Averaging {dbt:.0f} days beyond terms — tighten up vendor payments")
        else: bc_findings.append(f"Averaging {dbt:.0f} days beyond terms — this signals cash flow stress to banks"); bc_actions.append(f"Get days-beyond-terms under 10 (currently {dbt:.0f})")

        # Public records (0-20 pts)
        if liens == 0 and judgments == 0 and derogs_biz == 0:
            bc_score += 20; bc_findings.append("No liens, judgments, or derogatory records")
        else:
            if judgments > 0: bc_findings.append(f"{judgments} judgment(s) on file — major red flag for lenders"); bc_actions.append("Resolve outstanding judgments before applying")
            if liens > 0: bc_findings.append(f"{liens} lien(s) on file"); bc_actions.append("Address outstanding liens — these appear on UCC searches")
            if derogs_biz > 0: bc_findings.append(f"{derogs_biz} derogatory item(s) on business credit")
    else:
        bc_findings.append("No business credit data loaded")
        bc_actions.append("Upload your business credit report (Dun & Bradstreet, Experian Business) for a complete assessment")

    scores["Business Credit"] = {"score": bc_score, "weight": 0.20, "findings": bc_findings, "actions": bc_actions}

    # ── 3. Cash Position & Runway (20%) ──
    cp_score = 0
    cp_findings = []
    cp_actions = []
    if cash:
        total_cash = cash.get("total_balance", 0)
        num_accounts = len(cash.get("accounts", []))

        # Cash level (0-40 pts) — context-dependent
        if total_cash >= 500_000: cp_score += 40; cp_findings.append(f"Cash position {fmt(total_cash)} — strong liquidity")
        elif total_cash >= 100_000: cp_score += 25; cp_findings.append(f"Cash position {fmt(total_cash)} — adequate for most small business loans")
        elif total_cash >= 25_000: cp_score += 10; cp_findings.append(f"Cash position {fmt(total_cash)} — thin for conventional lending"); cp_actions.append("Build cash reserves to at least 3 months of operating expenses before applying")
        else: cp_findings.append(f"Cash position {fmt(total_cash)} — banks want to see you can cover payments"); cp_actions.append("Accumulate cash reserves — lenders want to see 3-6 months of runway")

        # Multiple accounts (0-10 pts)
        if num_accounts >= 2: cp_score += 10; cp_findings.append(f"{num_accounts} accounts — shows banking relationship depth")
        else: cp_findings.append("Single account — consider opening a business savings account to show financial discipline")

        # Idle cash penalty/bonus (0-20 pts)
        if idle:
            idle_pct = idle.get("total_idle_cash", 0) / max(total_cash, 1) * 100
            if idle_pct < 20: cp_score += 20; cp_findings.append("Cash is well-deployed across account types")
            elif idle_pct < 50: cp_score += 10; cp_findings.append(f"{idle_pct:.0f}% of cash sitting idle — move to higher-yield accounts"); cp_actions.append("Move idle cash to money market or high-yield savings before applying — shows financial sophistication")
            else: cp_findings.append(f"{idle_pct:.0f}% of cash idle in low-yield accounts"); cp_actions.append("Optimize cash allocation — bankers notice when businesses leave money in 0% checking")

        # Deposit trend (0-30 pts) — use forecast as proxy
        forecast, _ = run_safe(forecast_cash_position, DATA, 90)
        if forecast and forecast.get("projections"):
            last_proj = forecast["projections"][-1]
            ending = last_proj.get("ending_balance", 0)
            if ending >= total_cash * 0.9: cp_score += 30; cp_findings.append("90-day forecast shows stable or growing cash position")
            elif ending >= total_cash * 0.7: cp_score += 15; cp_findings.append("Cash forecast shows moderate decline over 90 days"); cp_actions.append("Ensure cash position is stable or growing when you apply — banks look at trends")
            else: cp_findings.append("Cash forecast shows significant decline"); cp_actions.append("Address cash burn before applying — banks will see the downward trend")
            if forecast.get("deficit_periods"):
                cp_findings.append(f"Potential shortfall periods: {', '.join(forecast['deficit_periods'])}")
                cp_actions.append("Resolve projected cash shortfalls before applying")
    else:
        cp_findings.append("No cash position data loaded")
        cp_actions.append("Upload accounts.csv and transactions.csv for cash analysis")

    scores["Cash & Runway"] = {"score": cp_score, "weight": 0.20, "findings": cp_findings, "actions": cp_actions}

    # ── 4. Working Capital (15%) ──
    wc_score = 0
    wc_findings = []
    wc_actions = []
    if wc_data:
        cr = wc_data.get("current_ratio", 0)
        dso = wc_data.get("days_sales_outstanding", 0)
        ccc = wc_data.get("cash_conversion_cycle_days", 0)
        runway = wc_data.get("runway_days", 0)

        # Current ratio (0-35 pts)
        if cr >= 2.0: wc_score += 35; wc_findings.append(f"Current ratio {cr:.2f}x — strong, exceeds bank requirements")
        elif cr >= 1.5: wc_score += 25; wc_findings.append(f"Current ratio {cr:.2f}x — healthy")
        elif cr >= 1.2: wc_score += 15; wc_findings.append(f"Current ratio {cr:.2f}x — adequate but tight"); wc_actions.append("Improve current ratio above 1.5x by reducing short-term liabilities or building current assets")
        elif cr >= 1.0: wc_score += 5; wc_findings.append(f"Current ratio {cr:.2f}x — banks prefer above 1.25x"); wc_actions.append(f"Current ratio of {cr:.2f}x is borderline — focus on building it above 1.5x")
        else: wc_findings.append(f"Current ratio {cr:.2f}x — below 1.0 means liabilities exceed current assets"); wc_actions.append("Address negative working capital immediately — this will block most financing")

        # DSO (0-25 pts)
        if dso <= 30: wc_score += 25; wc_findings.append(f"DSO {dso:.0f} days — excellent collection speed")
        elif dso <= 45: wc_score += 15; wc_findings.append(f"DSO {dso:.0f} days — acceptable")
        elif dso <= 60: wc_score += 5; wc_findings.append(f"DSO {dso:.0f} days — slow collections concern banks"); wc_actions.append(f"Reduce DSO from {dso:.0f} to under 45 days — tighten payment terms, offer early-pay discounts")
        else: wc_findings.append(f"DSO {dso:.0f} days — very slow, indicates collection problems"); wc_actions.append(f"DSO of {dso:.0f} days is a red flag — implement stricter AR management immediately")

        # Cash conversion cycle (0-20 pts)
        if ccc <= 30: wc_score += 20; wc_findings.append(f"Cash conversion cycle {ccc:.0f} days — efficient")
        elif ccc <= 60: wc_score += 10; wc_findings.append(f"Cash conversion cycle {ccc:.0f} days — moderate")
        else: wc_findings.append(f"Cash conversion cycle {ccc:.0f} days — cash is tied up too long"); wc_actions.append("Shorten cash conversion cycle by collecting faster and negotiating longer vendor terms")

        # Runway (0-20 pts)
        if runway >= 180: wc_score += 20; wc_findings.append(f"Runway {runway:.0f} days — strong buffer")
        elif runway >= 90: wc_score += 10; wc_findings.append(f"Runway {runway:.0f} days — adequate")
        else: wc_findings.append(f"Runway only {runway:.0f} days — banks want 90+ days"); wc_actions.append(f"Build runway from {runway:.0f} to 90+ days before applying")
    else:
        wc_findings.append("No working capital data provided — enter values above for a complete assessment")
        wc_actions.append("Fill in the working capital fields above for a more accurate readiness score")

    scores["Working Capital"] = {"score": wc_score, "weight": 0.15, "findings": wc_findings, "actions": wc_actions}

    # ── 5. Existing Debt & Covenants (10%) ──
    debt_score = 0
    debt_findings = []
    debt_actions = []
    if cov:
        overall = cov.get("overall_status", "unknown")
        breaches = cov.get("breaches", 0)
        warnings = cov.get("warnings", 0)

        if overall == "compliant" and breaches == 0 and warnings == 0:
            debt_score = 100; debt_findings.append("All covenants compliant with no warnings — clean record")
        elif overall == "compliant" and warnings > 0:
            debt_score = 60; debt_findings.append(f"Compliant but {warnings} warning(s) — banks will ask about these"); debt_actions.append("Improve covenant headroom on warning items before seeking new debt")
        elif breaches > 0:
            debt_findings.append(f"{breaches} covenant breach(es) — this will likely block new financing")
            debt_actions.append("Resolve all covenant breaches before applying — lenders check existing facility compliance")
            if cov.get("covenants"):
                for c in cov["covenants"]:
                    if c.get("status") == "breach":
                        debt_findings.append(f"Breach: {c['covenant_name']} (headroom: {c['headroom_pct']:.1f}%)")
    else:
        debt_score = 70  # No existing debt is actually okay
        debt_findings.append("No existing debt covenants on file")

    scores["Existing Debt"] = {"score": debt_score, "weight": 0.10, "findings": debt_findings, "actions": debt_actions}

    # ── 6. Documentation Readiness (10%) ──
    doc_score = 0
    doc_findings = []
    doc_actions = []
    doc_checklist = {
        "Bank statements (accounts.csv)": cash is not None,
        "Transaction history (transactions.csv)": cash is not None,  # loaded together
        "Personal credit report": credit is not None and bool(credit.get("personal_profiles")),
        "Business credit report": credit is not None and bool(credit.get("business_profile")),
        "Debt/covenant schedule": cov is not None,
        "Vendor/AP aging": idle is not None,  # vendors loaded for payment optimizer
        "Working capital data": wc_data is not None,
    }
    docs_present = sum(1 for v in doc_checklist.values() if v)
    docs_total = len(doc_checklist)
    doc_score = int((docs_present / docs_total) * 100)
    doc_findings.append(f"{docs_present} of {docs_total} key documents loaded")
    missing = [k for k, v in doc_checklist.items() if not v]
    if missing:
        doc_actions.append(f"Still needed: {', '.join(missing)}")

    scores["Documentation"] = {"score": doc_score, "weight": 0.10, "findings": doc_findings, "actions": doc_actions}

    # ════════════════════════════════════════════════════════
    #  CALCULATE OVERALL SCORE
    # ════════════════════════════════════════════════════════
    overall_score = sum(s["score"] * s["weight"] for s in scores.values())
    # Normalize: each category max is 100, so weighted sum max is 100
    overall_score = min(overall_score, 100)

    if overall_score >= 75: overall_status = "strong"
    elif overall_score >= 55: overall_status = "fair"
    elif overall_score >= 35: overall_status = "needs_work"
    else: overall_status = "not_ready"

    # ════════════════════════════════════════════════════════
    #  DISPLAY: OVERALL SCORE
    # ════════════════════════════════════════════════════════
    score_color = GREEN if overall_score >= 75 else YELLOW if overall_score >= 50 else RED

    st.markdown(f"""<div class="card" style="text-align:center;padding:2rem;">
<div class="card-header">FINANCING READINESS SCORE</div>
<div style="font-size:4rem;font-weight:800;color:{score_color};line-height:1;">{overall_score:.0f}</div>
<div style="font-size:1rem;color:{TEXT_SECONDARY};margin-top:0.5rem;">out of 100</div>
<div style="margin-top:1rem;">{tag_html(overall_status)}</div>
</div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    #  DISPLAY: CATEGORY BREAKDOWN
    # ════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### Category Scores")

    for cat_name, cat_data in scores.items():
        cat_score = cat_data["score"]
        cat_weight = cat_data["weight"]
        cat_weighted = cat_score * cat_weight
        if cat_score >= 70: cat_status = "strong"
        elif cat_score >= 40: cat_status = "fair"
        else: cat_status = "weak"

        with st.expander(f"{cat_name} — {cat_score}/100 ({cat_weight*100:.0f}% weight)"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Raw Score", f"{cat_score}/100")
            c2.metric("Weight", f"{cat_weight*100:.0f}%")
            c3.metric("Weighted", f"{cat_weighted:.0f} pts")

            if cat_data["findings"]:
                st.markdown("**Findings:**")
                findings_html = ""
                for f in cat_data["findings"]:
                    findings_html += status_html(cat_status, f)
                st.markdown(f'<div class="card">{findings_html}</div>', unsafe_allow_html=True)

            if cat_data["actions"]:
                st.markdown("**Action Items:**")
                for a in cat_data["actions"]:
                    st.markdown(f"- {a}")

    # ════════════════════════════════════════════════════════
    #  DISPLAY: TOP ACTIONS (PRIORITIZED)
    # ════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### Top Actions Before Applying")

    all_actions = []
    priority_order = ["Personal Credit", "Business Credit", "Cash & Runway", "Existing Debt", "Working Capital", "Documentation"]
    for cat in priority_order:
        if cat in scores:
            for action in scores[cat]["actions"]:
                all_actions.append({"category": cat, "action": action, "score": scores[cat]["score"]})

    # Sort by lowest score first (most urgent)
    all_actions.sort(key=lambda x: x["score"])

    if all_actions:
        for i, item in enumerate(all_actions[:8], 1):
            urgency = "weak" if item["score"] < 30 else "fair" if item["score"] < 60 else "strong"
            action_text = item["action"]
            cat_text = item["category"]
            st.markdown(status_html(urgency, f"{i}. {action_text}", cat_text), unsafe_allow_html=True)
    else:
        st.markdown(f'{status_html("strong", "You look ready — no major issues found")}', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    #  DISPLAY: LOAN PRODUCT MATCHER
    # ════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### Loan Products You May Qualify For")

    fico_score = 0
    if credit and credit.get("personal_profiles"):
        fico_score = credit["personal_profiles"][0].get("credit_score", 0)

    paydex_score = 0
    yrs_in_biz = 0
    if credit and credit.get("business_profile"):
        paydex_score = credit["business_profile"].get("paydex_score", 0)
        yrs_in_biz = credit["business_profile"].get("years_in_business", 0)

    total_cash_val = cash.get("total_balance", 0) if cash else 0
    has_breach = cov.get("breaches", 0) > 0 if cov else False

    products = []

    # Conventional Line of Credit
    if fico_score >= 680 and yrs_in_biz >= 2 and not has_breach:
        rate = "Prime + 1-3%" if fico_score >= 720 else "Prime + 2-5%"
        products.append({"name": "Conventional Line of Credit", "likelihood": "strong", "rate": rate,
                         "detail": "Revolving credit for working capital needs. Requires strong personal credit and 2+ years in business."})
    elif fico_score >= 640:
        products.append({"name": "Conventional Line of Credit", "likelihood": "fair", "rate": "Prime + 3-6%",
                         "detail": "Possible but may require additional collateral or higher rates due to credit profile."})

    # SBA 7(a)
    if fico_score >= 640 and yrs_in_biz >= 1:
        products.append({"name": "SBA 7(a) Loan", "likelihood": "strong" if fico_score >= 680 else "fair",
                         "rate": "Prime + 2.25-4.75%",
                         "detail": "Government-backed loan up to $5M. Longer terms and lower rates than conventional. 2-3 month process."})

    # SBA Microloan
    if yrs_in_biz >= 0:  # Available to startups
        products.append({"name": "SBA Microloan", "likelihood": "strong", "rate": "6-9%",
                         "detail": "Up to $50K through nonprofit intermediaries. Good for newer businesses or those building credit."})

    # Equipment Financing
    if fico_score >= 600:
        products.append({"name": "Equipment Financing", "likelihood": "strong" if fico_score >= 680 else "fair",
                         "rate": "5-15% depending on equipment type",
                         "detail": "Secured by the equipment itself. Easier to qualify for since the collateral reduces lender risk."})

    # AR Factoring / Invoice Financing
    if total_cash_val > 0:
        products.append({"name": "Invoice Factoring / AR Financing", "likelihood": "fair",
                         "rate": "1-5% per invoice (factor fee)",
                         "detail": "Sell outstanding invoices for immediate cash. Credit decision based on your customers' creditworthiness, not yours."})

    # Term Loan
    if fico_score >= 700 and yrs_in_biz >= 3 and not has_breach:
        products.append({"name": "Term Loan", "likelihood": "strong", "rate": "Prime + 1-4%",
                         "detail": "Fixed amount, fixed repayment schedule. Best for specific investments (expansion, acquisition, real estate)."})

    if products:
        for prod in products:
            with st.expander(f'{prod["name"]} — {tag_html(prod["likelihood"])} Est. Rate: {prod["rate"]}'):
                st.markdown(f'{tag_html(prod["likelihood"])}', unsafe_allow_html=True)
                st.markdown(f'**Estimated Rate:** {prod["rate"]}')
                st.markdown(prod["detail"])
    else:
        st.warning("Limited data available — upload credit reports and bank statements for product matching.")

    # ════════════════════════════════════════════════════════
    #  DISPLAY: DOCUMENTATION CHECKLIST
    # ════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### Documentation Checklist")
    st.caption("What to bring when you meet with a banker")

    banker_docs = [
        ("3 years of business tax returns", "Required by virtually all lenders"),
        ("3 years of personal tax returns (all guarantors)", "Required for personal guaranty evaluation"),
        ("Year-to-date profit & loss statement", "Shows current year performance"),
        ("Balance sheet (current)", "Shows assets, liabilities, and equity"),
        ("Accounts receivable aging report", "Shows who owes you and how old the invoices are"),
        ("Accounts payable aging report", "Shows what you owe and payment patterns"),
        ("Business debt schedule", "List of all existing loans, lines, and leases with balances and payments"),
        ("Personal financial statement (all guarantors)", "SBA Form 413 or bank equivalent"),
        ("Business plan or use-of-funds narrative", "Explain what the financing is for and how it improves the business"),
        ("Bank statements (last 6 months)", "Shows cash flow patterns and average balances"),
        ("Business licenses and formation documents", "Articles of incorporation, operating agreement, etc."),
    ]

    for doc_name, doc_desc in banker_docs:
        st.markdown(f'{status_html("strong", doc_name, doc_desc)}', unsafe_allow_html=True)
