# TreasuryOS

**Find out if you're ready for a business loan — free, in 5 minutes.**

Upload your bank statements and credit reports. Get a readiness score, see what's hurting you, learn what to fix, and find out which loans you qualify for. No account needed. No sales pitch.

**[Try it now →](https://treasury-mcp-os-dru9zxrd9n82aelwgkvcel.streamlit.app/)**

---

## What You Get

- **A readiness score from 0-100** — based on the same things a bank looks at when you apply
- **What's helping and what's hurting** — broken down into plain English, not banker jargon
- **Which loans fit your profile** — SBA, line of credit, equipment financing, and more
- **What to fix first** — prioritized action items before you walk into the bank
- **A checklist of what to bring** — so your first meeting with a banker actually goes somewhere

## How It Works

1. Go to the app and click **"See a Demo Score"** to see an example
2. Switch to **"Upload My Files"** in the sidebar
3. Drop in your bank statements, credit reports, or financial docs (CSV, Excel, Word, or PDF)
4. See your score and what to do next

## Who This Is For

Business owners thinking about getting a loan, a line of credit, or SBA financing — and wanting to know where they stand before they apply and use a hard credit pull.

---

## Under the Hood

TreasuryOS is built by a former commercial banker who spent 5 years on the other side of the desk evaluating loan applications. The scoring engine uses real underwriting logic — the same criteria banks use to decide whether to approve you.

### The Scoring Engine

Six weighted categories, each scored 0-100:

| Category | What It Measures |
|----------|-----------------|
| Personal Credit | FICO score, credit card usage, payment history, recent inquiries |
| Business Credit | Paydex score, years in business, vendor payment speed, liens |
| Cash Position | Total cash, number of accounts, 90-day cash forecast |
| Working Capital | Current ratio, collection speed, cash cycle, runway |
| Existing Debt | Covenant compliance, breaches, warning signs |
| Documentation | Which key documents have been uploaded |

### Three Apps, One Engine

| App | Audience | File |
|-----|----------|------|
| **SMB App** | Business owners | `smb_app.py` |
| **Full Dashboard** | Power users / all tools | `app.py` |
| **RM Dashboard** | Bank relationship managers | `rm_dashboard.py` |

All three share the same Python analysis engine in `tools/`.

### Analysis Tools (9 total)

The engine behind the scoring — also available as an MCP server for Claude Desktop:

1. **Cash Position Aggregator** — Balances across all accounts, rolled up by currency and type
2. **Idle Cash Scanner** — Finds cash sitting in low-yield accounts and calculates the opportunity cost
3. **Cash Flow Forecaster** — Projects cash position forward 90 days based on transaction patterns
4. **Working Capital Analyzer** — Current ratio, DSO, DPO, cash conversion cycle, runway
5. **Payment Optimizer** — Finds early-pay discounts that beat your cost of capital
6. **FX Exposure Scanner** — Identifies unhedged foreign currency risk
7. **Covenant Monitor** — Tracks debt covenant compliance and flags breaches
8. **Credit Report Parser** — Extracts FICO, Paydex, utilization, payment history from credit data
9. **Credit Position Assessor** — Combines everything into an overall credit rating and lending capacity estimate

### File Structure

```
treasury-mcp-os/
├── smb_app.py             ← Business owner app (the product)
├── app.py                 ← Full dashboard with all 11 pages
├── rm_dashboard.py        ← RM portfolio dashboard
├── server.py              ← MCP server for Claude Desktop
├── models.py              ← Data models
├── tools/                 ← Analysis engine (9 tools)
├── sample_data/           ← Demo data (Apex Manufacturing Corp)
├── portfolio_data/        ← Multi-client data for RM dashboard
├── requirements.txt
├── pyproject.toml
└── setup.sh               ← One-command installer for Claude Desktop
```

### Quick Start (Local)

**Web dashboard (no Claude needed):**
```bash
git clone https://github.com/GPBK-STUY/treasury-mcp-os.git
cd treasury-mcp-os
pip install -r requirements.txt
streamlit run smb_app.py
```

**MCP server (Claude Desktop integration):**
```bash
git clone https://github.com/GPBK-STUY/treasury-mcp-os.git ~/Desktop/treasury-mcp-os
bash ~/Desktop/treasury-mcp-os/setup.sh
```

See [QUICKSTART.md](QUICKSTART.md) for bankers/RMs or [QUICKSTART-OWNERS.md](QUICKSTART-OWNERS.md) for business owners.

### File Upload

Accepts CSV, Excel (.xlsx), Word (.docx), and PDF files. Auto-detects content type by scanning column headers and maps to the expected data format.

### Sample Data

The repo includes demo data for a fictional mid-market company (Apex Manufacturing Corp, ~$25M revenue) with bank accounts, transactions, vendor payables, debt covenants, FX rates, and credit reports.

---

## About

Built by [Grant Page](mailto:gpage2771@gmail.com) — 5 years in commercial banking, now building the tools that should have existed the whole time.

## License

MIT
