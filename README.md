# TreasuryOS

Two tools built on one engine. Pick your door.

---

## For Business Owners

**Find out if you're ready for a business loan — free, in 5 minutes.**

Upload your bank statements and credit reports. Get a 0-100 readiness score, see what's hurting you, learn what to fix, find out which loans you qualify for, and get a checklist of what to bring to the bank.

No account needed. No cost. No sales pitch.

**[Try it now →](https://treasury-mcp-os-dru9zxrd9n82aelwgkvcel.streamlit.app/)**

**What you get:**
- A readiness score based on the same things a bank looks at
- What's helping and what's hurting — in plain English
- Which loans fit your profile (SBA, line of credit, equipment financing, etc.)
- A prioritized list of what to fix before you apply
- A checklist of what to bring to the banker meeting

**How to use it:**
1. Click the link above
2. Hit **"See a Demo Score"** to see how it works
3. Switch to **"Upload My Files"** in the sidebar
4. Drop in your bank statements, credit reports, or financial docs
5. See your score and game plan

---

## For Bankers & Relationship Managers

**A portfolio dashboard that does the prep work for you.**

Search clients, pull up profiles, see financing readiness across your book. The same scoring engine, built for the RM workflow — one search bar to get the full picture on any client.

**[Open RM Dashboard →](https://treasury-os-rm.streamlit.app/)**

**What you get:**
- Portfolio view with search across all clients
- Client profiles with credit, cash, covenants, and readiness score
- 9 analysis tools: cash position, forecast, working capital, credit assessment, covenant monitoring, FX exposure, idle cash, payment optimization
- MCP server integration with Claude Desktop for AI-powered analysis

**Quick start (Claude Desktop):**
```bash
git clone https://github.com/GPBK-STUY/treasury-mcp-os.git ~/Desktop/treasury-mcp-os
bash ~/Desktop/treasury-mcp-os/setup.sh
```

See [QUICKSTART.md](QUICKSTART.md) for full setup.

---

## How It's Built

One analysis engine powers everything. Three apps serve different audiences.

| App | Who it's for | Live link | File |
|-----|-------------|-----------|------|
| SMB App | Business owners | [Launch](https://treasury-mcp-os-dru9zxrd9n82aelwgkvcel.streamlit.app/) | `smb_app.py` |
| RM Dashboard | Bank RMs | [Launch](https://treasury-os-rm.streamlit.app/) | `rm_dashboard.py` |
| Full Dashboard | Power users | [Launch](https://treasury-mcp-os-dru9zxrd9n82aelwgkvcel.streamlit.app/) | `app.py` |

### The Scoring Engine

Six categories, each scored 0-100:

| Category | What It Measures |
|----------|-----------------|
| Personal Credit | FICO, credit card usage, payment history, inquiries |
| Business Credit | Paydex, years in business, vendor payment speed, liens |
| Cash Position | Total cash, account count, 90-day forecast |
| Working Capital | Current ratio, collection speed, cash cycle, runway |
| Existing Debt | Covenant compliance, breaches, warnings |
| Documentation | Which key documents have been uploaded |

### Analysis Tools (9)

```
Cash Position Aggregator    Credit Report Parser
Idle Cash Scanner           Credit Position Assessor
Cash Flow Forecaster        Covenant Monitor
Working Capital Analyzer    FX Exposure Scanner
Payment Optimizer
```

### File Upload

Accepts CSV, Excel (.xlsx), Word (.docx), and PDF. Auto-detects content type by scanning column headers and maps to the right data format.

### Run Locally

```bash
git clone https://github.com/GPBK-STUY/treasury-mcp-os.git
cd treasury-mcp-os
pip install -r requirements.txt
streamlit run smb_app.py        # Business owner app
streamlit run rm_dashboard.py   # RM dashboard
streamlit run app.py            # Full dashboard
```

### File Structure

```
treasury-mcp-os/
├── smb_app.py             ← Business owner app
├── rm_dashboard.py        ← RM portfolio dashboard
├── app.py                 ← Full dashboard (all 11 pages)
├── server.py              ← MCP server for Claude Desktop
├── tools/                 ← Shared analysis engine (9 tools)
├── sample_data/           ← Demo data (Apex Manufacturing Corp)
├── portfolio_data/        ← Multi-client data for RM dashboard
└── setup.sh               ← One-command Claude Desktop installer
```

---

## About

Built by [Grant Page](mailto:gpage2771@gmail.com) — 5 years in commercial banking, now building the tools that should have existed the whole time.

## License

MIT
