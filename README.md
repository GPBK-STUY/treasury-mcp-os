TreasuryOS — AI-Powered Treasury Management for Commercial Banking
I built this because I spent 5 years as a commercial banker and watched millions in client value slip through the cracks every single quarter. Idle cash sitting in checking accounts earning 0%. Early-pay discounts nobody calculated. Covenant headroom nobody tracked until it was too late. Not because bankers are lazy — because the tools are garbage.
TreasuryOS is an MCP server that turns Claude into a treasury analyst. You give it bank accounts, transactions, vendor payables, and debt covenants — it gives you the answers that actually move the needle for your clients.

Why This Exists
Here's something most fintech founders don't understand: the money in commercial banking isn't made on flashy dashboards. It's made in the conversations between RMs and their clients.
At Citizens, we had a cash flow forecaster. Beautiful tool. Almost nobody used it. Why? Because it was built for clients to self-serve, and clients don't want to self-serve on treasury. They want their banker to call them and say "hey, you've got $2.3M sitting in a checking account earning nothing — let's fix that."
That's what TreasuryOS does. It gives the RM (or in this case, Claude) the firepower to surface those insights automatically. Every tool is designed around one question: what would a great RM tell their client right now?

What It Does
7 composable tools that Claude can chain together on its own:
1. Cash Position Aggregator — Pulls balances across all accounts, rolls them up by currency and account type. This is where every treasury conversation starts.
2. Idle Cash Detector — Scans checking and savings accounts for cash above operating reserves earning below-market rates. The math is simple: $2.27M in a checking account at 0% when money markets are paying 4.50% = $102K/year in lost yield. That's a real number you can put in front of a CFO.
3. Cash Flow Forecaster — Looks at 3 months of transaction history, calculates weekly averages by category, projects forward 90 days. Confidence levels degrade over time because forecasts are guesses and we should be honest about that.
4. Working Capital Analyzer — DSO, DPO, cash conversion cycle, current ratio, runway days. Everything an RM needs for a credit review or a QBR. Pass in the numbers, get back a health assessment using real underwriting thresholds.
5. Payment Timing Optimizer — Parses vendor discount terms (2/10 net 30) and tells you the annualized return of paying early. 2% discount for paying 20 days early = ~36.7% annualized. If your cost of capital is 10%, that's free money. Only recommends early payment when the math actually works.
6. FX Exposure Scanner — Identifies non-USD payables, converts to USD, calculates Value at Risk. Most mid-market companies have unhedged FX exposure they don't even know about. This finds it.
7. Debt Covenant Monitor — Tracks compliance across all facilities, calculates headroom percentages. Flags warnings below 10% headroom. A covenant breach can trigger cross-default clauses — you never want to be surprised by this.
8. Credit Report Parser — Reads personal and business credit reports already on file from the application process. Extracts FICO scores, Paydex, utilization, payment history, derogatories, and public records. No new credit pull needed — uses what the institution already has.
9. Credit Position Assessor — The integration tool. Chains credit data with cash position and covenant compliance to produce an overall credit rating, risk factors, lending capacity estimate, and cross-sell opportunities. This is the full underwriting picture in one query.

The Architecture
┌──────────────────────────────────────────────────┐
│                 Claude (the AI)                   │
│          Acts as your Junior RM / Analyst         │
│     Reads tool descriptions, decides what to call │
└───────────────────────┬──────────────────────────┘
                        │  MCP Protocol
                        ▼
┌──────────────────────────────────────────────────┐
│              server.py (Control Plane)            │
│     Registers 7 tools, routes requests to them   │
└───────────────────────┬──────────────────────────┘
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
    ┌───────────┐ ┌──────────┐ ┌──────────┐
    │  Tool 1   │ │  Tool 2  │ │ Tool 3-7 │
    │ Cash Pos  │ │Idle Cash │ │  etc...  │
    └─────┬─────┘ └────┬─────┘ └────┬─────┘
          │            │            │
          ▼            ▼            ▼
┌──────────────────────────────────────────────────┐
│           sample_data/ (Resource Plane)           │
│     CSV files today → Bank APIs tomorrow          │
└──────────────────────────────────────────────────┘
The tools contain the banking logic. The data layer is separate. Today it reads CSVs. Tomorrow you swap in Plaid or your bank's API. The tools don't change. Same logic, different data source.

Quick Start (One Command)
Open Terminal and paste:
```bash
git clone https://github.com/GPBK-STUY/treasury-mcp-os.git ~/Desktop/treasury-mcp-os && bash ~/Desktop/treasury-mcp-os/setup.sh
```
That's it. The setup script checks Python, installs dependencies, and configures Claude Desktop automatically. Restart Claude Desktop, look for the 🔨 icon, and start asking questions.

**Bankers & RMs:** See [QUICKSTART.md](QUICKSTART.md) — connects to Claude Desktop for AI-powered analysis.
**Business Owners & Founders:** See [QUICKSTART-OWNERS.md](QUICKSTART-OWNERS.md) — same tool, written for people running the business instead of advising it.

**Just want the dashboard? No Claude needed:**
```bash
git clone https://github.com/GPBK-STUY/treasury-mcp-os.git ~/Desktop/treasury-mcp-os && cd ~/Desktop/treasury-mcp-os && uv sync && uv run streamlit run app.py
```
Opens a web dashboard in your browser. Upload your CSVs and go.

Test a Tool
Open Claude Desktop and ask "What's my current cash position?" You should see balances for Apex Manufacturing Corp across 8 accounts in USD and EUR.
Then ask "Do I have any idle cash?" — it'll tell you exactly how much money is sitting there doing nothing and what it's costing per year.

Sample Data
The repo comes with a fictional mid-market client: Apex Manufacturing Corp (~$25M revenue, US and European operations).

8 bank accounts across Citizens, JPMorgan, Deutsche Bank — checking, savings, money market, CD
48 transactions over 3 months — payroll, AR collections, AP payments, debt service, taxes
10 vendors with different payment terms and early-pay discounts
5 debt covenants across two facilities (one deliberately tight at 7.3% headroom)
FX rates for EUR, GBP, JPY, CHF

The data is realistic. I've seen these exact patterns on real commercial clients. The tight covenant is there on purpose — if your monitoring tool doesn't flag it, your tool is broken.

Financial Guardrails
These are baked into the agent instructions (CLAUDE.md), not the tools themselves. They're the same thresholds you'd use in real credit analysis:

DSCR < 1.25x → flag it. Below 1.0x means the business can't service debt from operations.
Current Ratio < 1.20x → flag it. Below 1.0x = negative working capital.
Leverage > 3.50x → flag it.
Covenant headroom < 10% → warning. Below 0% = breach.
Never deploy cash below 20% of checking balance — that's the operating reserve.
Runway < 90 days → escalate. Below 30 days → immediate action.
Only recommend early payment if annualized return > 10% (cost of capital proxy).


How to Extend This
Add a new tool:

Create a new file in tools/ (e.g., tools/loan_analyzer.py)
Write a function that returns a dict
Add a Pydantic model in models.py for the return type
Import and register it in server.py with @mcp.tool()

Swap in real data:
Change the CSVs in sample_data/ or replace the CSV reads with API calls to Plaid, MX, or your core banking system. The tool interface stays the same.
Change the guardrails:
Edit CLAUDE.md. That's the policy manual. Want stricter DSCR thresholds? Change the number. Want different tool chaining patterns? Update the instructions.

File Structure
treasury-mcp-os/
├── server.py              ← MCP entry point. Registers 9 tools. For Claude Desktop.
├── app.py                 ← Web dashboard. Run: streamlit run app.py
├── models.py              ← Data shapes. What each tool returns.
├── CLAUDE.md              ← Agent instructions. Banking guardrails.
├── QUICKSTART.md          ← Setup guide for bankers & RMs.
├── QUICKSTART-OWNERS.md   ← Setup guide for business owners.
├── setup.sh               ← One-command installer.
├── pyproject.toml         ← Project config and dependencies.
├── tools/
│   ├── __init__.py
│   ├── aggregator.py      ← Cash position
│   ├── idle_cash.py       ← Idle cash scanner
│   ├── forecaster.py      ← Cash flow forecast
│   ├── working_capital.py ← Working capital ratios
│   ├── payment_optimizer.py ← Payment timing
│   ├── fx_scanner.py      ← FX exposure
│   ├── covenant_monitor.py ← Covenant compliance
│   ├── credit_parser.py   ← Credit report parser
│   └── credit_assessor.py ← Credit position assessor
└── sample_data/
    ├── accounts.csv
    ├── transactions.csv
    ├── vendors.csv
    ├── covenants.csv
    ├── fx_rates.csv
    ├── personal_credit.csv
    └── business_credit.csv

Who This Is For
Two audiences, same tool. If you're a **commercial banker or RM**, TreasuryOS is your junior analyst — it does the number-crunching so you can focus on the client conversation. If you're a **business owner or founder**, it's the CFO you can't afford yet — it watches your cash, your credit, and your debt so nothing sneaks up on you.

Where This Is Going
This is V1. The tools work, the math is right, the architecture is clean. But the real play is bigger than a demo.
Commercial banks are sitting on a goldmine of client data and doing almost nothing intelligent with it. Every RM in every bank manually pulls the same reports, does the same math, and gives the same generic advice. TreasuryOS is the start of changing that — give the AI the same tools a great RM uses, point it at real client data, and let it surface the insights that actually drive revenue.
Next up: document parsing (balance sheets, P&Ls, AP aging reports, bank statements) → automated financial spreading → risk rating. The goal is to take what used to be a 2-hour credit analysis and make it a 2-minute conversation.

About Me
5 years in commercial banking. 1 year writing code. Built this because I kept seeing the same problem from both sides — banks have the data but not the tools, and fintechs have the tools but don't understand the business. TreasuryOS is what happens when you actually know both.

License
MIT
