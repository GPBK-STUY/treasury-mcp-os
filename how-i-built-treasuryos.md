# How I Built the TreasuryOS MCP Server — Step by Step

## What is an MCP Server, in Banking Terms?

Think of an MCP server like a **commercial lending platform** that a Relationship Manager uses. The RM doesn't build the credit models — they use tools that someone else built. They click "run credit analysis" and get a DSCR back. They don't need to know the math. They just need the answer to make a decision.

An MCP server works the same way, except the "Relationship Manager" is Claude. You build tools (functions) that Claude can call on its own, whenever it needs data to answer a question. Claude reads the tool descriptions, decides which ones to use, and chains them together — just like an experienced RM knows to check the cash position *before* recommending a sweep account.

**MCP = Model Context Protocol.** It's just a standard way to connect tools to AI models. Think of it like the USB-C of AI — a universal plug that lets Claude talk to your code.

---

## The Architecture (How the Pieces Fit Together)

```
┌─────────────────────────────────────────────────┐
│                  Claude (the AI)                 │
│         Acts as your Junior RM / Analyst         │
│    Reads tool descriptions, decides what to call │
└──────────────────────┬──────────────────────────┘
                       │  MCP Protocol
                       │  (the "USB-C" connection)
                       ▼
┌─────────────────────────────────────────────────┐
│              server.py (Control Plane)           │
│    Registers 7 tools, routes requests to them    │
│    Think: the branch manager routing work        │
└──────────────────────┬──────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌───────────┐ ┌──────────┐ ┌──────────┐
   │  Tool 1   │ │  Tool 2  │ │ Tool 3-7 │
   │ Cash Pos  │ │Idle Cash │ │  etc...  │
   └─────┬─────┘ └────┬─────┘ └────┬─────┘
         │            │            │
         ▼            ▼            ▼
┌─────────────────────────────────────────────────┐
│           sample_data/ (Resource Plane)          │
│    CSV files today → Bank APIs tomorrow          │
│    Think: the core banking system                │
└─────────────────────────────────────────────────┘
```

**Why this split matters:** The tools contain your banking logic (how to calculate DSCR, what "idle cash" means, when to flag a covenant). The data layer is separate. Today it reads CSVs. Tomorrow you swap in Plaid or a bank API. The tools don't change at all. Same logic, different data source.

---

## Step-by-Step Build Process

### Step 1: Define Your Data Models (models.py)

**Banking analogy:** Before you build any reports, you define what fields go on each report. A credit memo has specific fields (borrower name, DSCR, leverage ratio). A cash position report has different fields (account, balance, currency).

**What I did:** Created 13 Pydantic models — these are Python classes that define the exact shape of data each tool returns. For example:

```python
class IdleCashOpportunity(BaseModel):
    account_id: str          # Which account
    bank_name: str           # Which bank
    current_balance: float   # What's in it
    idle_amount: float       # What's sitting there doing nothing
    current_yield_bps: int   # What it's earning now (basis points)
    annual_opportunity_cost: float  # How much you're losing per year
    recommended_action: str  # What to do about it
```

**Why Pydantic?** It enforces types. If someone passes a string where a number should be, it throws an error immediately instead of giving you garbage data downstream. In banking terms — it's like input validation on a loan application. You catch errors at the front door, not after the loan is booked.

**Key models I created:**
- `CashPositionReport` — aggregated balances across all accounts
- `IdleCashReport` — idle cash opportunities and their cost
- `CashFlowForecast` — weekly projections with confidence levels
- `WorkingCapitalMetrics` — DSO, DPO, CCC, runway, health assessment
- `PaymentOptimizationReport` — early-pay discount analysis
- `FXExposureReport` — unhedged currency risk and VaR
- `CovenantReport` — compliance status with headroom percentages

---

### Step 2: Create Sample Data (sample_data/)

**Banking analogy:** You can't test a credit model without test loans. I created a fictional mid-market client — Apex Manufacturing Corp, ~$25M revenue, US and European operations.

**5 CSV files:**

1. **accounts.csv** — 8 bank accounts across Citizens, JPMorgan, Deutsche Bank. Mix of checking (0 yield), savings (1.25%), money market (4.35-4.50%), and a CD (5.10%). Two currencies: USD and EUR.

2. **transactions.csv** — 44 transactions over 3 months. Realistic patterns: bi-weekly payroll (~$385k), monthly rent ($32k), quarterly taxes ($125k), AR collections ($165k-$525k), AP payments, loan payments ($45k/mo).

3. **vendors.csv** — 10 vendors with different payment terms. Some have early-pay discounts (2/10 net 30), some don't. Three currencies (USD, EUR, JPY).

4. **covenants.csv** — 5 debt covenants across two facilities (Citizens Revolver and JPM Term Loan). DSCR, leverage, current ratio, interest coverage, fixed charge coverage. All currently compliant but one is tight.

5. **fx_rates.csv** — 4 currency pairs (EUR/USD, GBP/USD, USD/JPY, USD/CHF).

**Why this matters:** Realistic sample data lets you test edge cases. The Fixed Charge Coverage is deliberately set at 1.18x against a 1.10x minimum — only 7.3% headroom. That tests whether the covenant monitor correctly flags it as a warning.

---

### Step 3: Build Each Tool (tools/ folder)

Each tool is a single Python file with a single function. This is important — one file, one job. Easy to test, easy to fix, easy to understand.

**Tool 1: Cash Position Aggregator** (`tools/aggregator.py`)
- **What it does:** Reads accounts.csv, totals everything up by currency and account type
- **Banking logic:** This is your daily cash position report. Every treasury operation starts here.
- **Code pattern:** Load CSV with pandas → loop through rows → build model objects → aggregate → return

**Tool 2: Idle Cash Detector** (`tools/idle_cash.py`)
- **What it does:** Scans checking and savings accounts for cash above operating reserves
- **Banking logic:** Any checking account balance earning 0% with more than $50k above the 20% operating reserve is money being wasted. Calculates exact annual cost.
- **Key calculation:** `annual_opportunity_cost = idle_amount × (target_yield - current_yield) / 10000`
- **Example:** $2.27M idle in a checking account at 0%, target 4.50% = **$102k/year lost**

**Tool 3: Cash Flow Forecaster** (`tools/forecaster.py`)
- **What it does:** Looks at 3 months of transaction history, calculates weekly averages by category, projects forward
- **Banking logic:** Same concept as Citizens' forecaster, but the output feeds directly into other tools instead of sitting in a dashboard nobody checks
- **Confidence levels:** Weeks 1-4 = high, 5-8 = medium, 9+ = low (forecasts degrade over time)

**Tool 4: Working Capital Analyzer** (`tools/working_capital.py`)
- **What it does:** Takes balance sheet inputs and calculates all the ratios an RM needs
- **Banking logic:** Current ratio, DSO, DPO, cash conversion cycle, runway days. Plus a health assessment using the same thresholds you'd use in credit analysis.
- **Why top-level inputs:** Claude passes in the numbers directly (no nested objects). This prevents the AI from getting confused by complex input structures.

**Tool 5: Payment Timing Optimizer** (`tools/payment_optimizer.py`)
- **What it does:** Parses vendor discount terms (e.g., "2/10 net 30") and calculates the annualized return of paying early
- **Banking logic:** 2/10 net 30 means 2% discount for paying 20 days early. Annualized, that's ~36.7%. If your cost of capital is 10%, that's free money.
- **Key formula:** `annualized_return = (discount% / (100 - discount%)) × (365 / days_accelerated) × 100`
- **Decision rule:** Only recommend "pay_early" if annualized return exceeds 10% (cost of capital proxy)

**Tool 6: FX Exposure Scanner** (`tools/fx_scanner.py`)
- **What it does:** Identifies non-USD vendor payables, converts to USD, calculates Value at Risk
- **Banking logic:** Unhedged FX is a hidden cost. A $175k EUR payable with 30 days to settlement has real risk if EUR/USD moves against you.
- **VaR calculation:** `VaR = USD_equivalent × 5% annual volatility × √(days/365)` — simplified but directionally correct

**Tool 7: Debt Covenant Monitor** (`tools/covenant_monitor.py`)
- **What it does:** Reads covenant thresholds, compares to current values, calculates headroom
- **Banking logic:** Headroom below 10% = warning. Below 0% = breach. A breach can trigger cross-default clauses — never minimize this.
- **Smart recommendations:** If there's a warning, it names the specific covenant and its headroom. "Fixed Charge Coverage has 7.3% headroom — monitor closely."

---

### Step 4: Wire It All Together (server.py)

**Banking analogy:** This is your branch operating system. It doesn't do the analysis itself — it routes requests to the right department (tool).

**What server.py does:**
1. Imports the FastMCP library (the framework that handles the MCP protocol)
2. Sets the data directory path (where to find the CSVs)
3. Imports all 7 tool functions
4. Registers each tool with `@mcp.tool()` decorator — this tells Claude "hey, this tool exists, here's what it does, here's what arguments it takes"
5. Provides the `mcp.run()` entry point

**The `@mcp.tool()` decorator is the key magic.** When you write:

```python
@mcp.tool()
def get_cash_position() -> dict:
    """Get aggregated cash position across all bank accounts.
    Returns balances by currency and account type."""
    return _get_cash_position(data_dir=DATA_DIR)
```

...you're telling Claude three things:
- **Name:** `get_cash_position` (what to call)
- **Description:** "Get aggregated cash position..." (when to call it)
- **Return type:** dict (what to expect back)

Claude reads these descriptions and decides on its own which tools to use. If someone asks "how's our cash looking?", Claude sees `get_cash_position` and thinks "that's relevant" — then calls it.

---

### Step 5: Write the Agent Instructions (CLAUDE.md)

**Banking analogy:** This is the policy and procedures manual for your Junior RM. It tells Claude the rules of engagement.

**What CLAUDE.md contains:**
- **Tool chaining patterns:** "If someone asks about cash, run tools 1, 2, and 3 in sequence"
- **Financial guardrails:** "Flag any DSCR below 1.25x" — the same rules you'd teach a new analyst
- **Formatting standards:** "Always show currency with commas, convert basis points to percentages"
- **Risk thresholds:** When to escalate, when to recommend immediate action

This file lives in the project root. When you connect the MCP to Claude Desktop, Claude reads it and follows the rules. It's what turns Claude from a generic AI into your domain-specific treasury analyst.

---

## The File Structure (What Goes Where)

```
treasury-mcp-os/
├── server.py            ← Entry point. Registers tools. Run this.
├── models.py            ← Data shapes. What each tool returns.
├── CLAUDE.md            ← Agent instructions. Banking rules.
├── pyproject.toml       ← Project config and dependencies.
├── tools/
│   ├── __init__.py      ← Empty file that makes this a Python package.
│   ├── aggregator.py    ← Tool 1: Cash position
│   ├── idle_cash.py     ← Tool 2: Idle cash scanner
│   ├── forecaster.py    ← Tool 3: Cash flow forecast
│   ├── working_capital.py ← Tool 4: Working capital analysis
│   ├── payment_optimizer.py ← Tool 5: Payment timing
│   ├── fx_scanner.py    ← Tool 6: FX exposure
│   └── covenant_monitor.py ← Tool 7: Covenant compliance
└── sample_data/
    ├── accounts.csv     ← Bank accounts and balances
    ├── transactions.csv ← 3 months of transaction history
    ├── vendors.csv      ← Vendor payables and terms
    ├── covenants.csv    ← Debt covenant thresholds
    └── fx_rates.csv     ← Currency exchange rates
```

---

## Key Concepts for a Banker Learning to Code

**Python packages:** The `tools/` folder with `__init__.py` is a "package." It's just a way to organize related files. When server.py says `from tools.aggregator import get_cash_position`, it's reaching into the tools folder and grabbing that one function.

**Pandas DataFrame:** Think of it as an Excel spreadsheet in Python. `pd.read_csv("accounts.csv")` loads the CSV into a table you can filter, sort, and aggregate. `df.groupby("currency")["balance"].sum()` is the same as a pivot table summing balances by currency.

**Pydantic BaseModel:** A template that says "this type of data must have these exact fields with these exact types." If the data doesn't match, it throws an error. Like form validation on a loan app.

**`@mcp.tool()` decorator:** The `@` symbol before a function is a "decorator" — it wraps the function with extra behavior. In this case, it registers the function as a tool that Claude can call. You don't need to understand how it works internally, just know that any function with `@mcp.tool()` above it becomes available to Claude.

**`-> dict` return type:** The `-> dict` after a function name tells Python (and Claude) what type of data the function returns. `dict` means a dictionary — Python's version of a JSON object (key-value pairs).

**`.model_dump()`:** Converts a Pydantic model into a plain dictionary. MCP tools need to return simple data types (dicts, lists, strings, numbers) — not Pydantic objects. So every tool builds a Pydantic model for validation, then calls `.model_dump()` to convert it before returning.

---

## How to Modify and Extend

**To change the sample data:** Edit the CSVs in sample_data/. Add accounts, change balances, add vendors. The tools will pick up the changes automatically.

**To add a new tool:**
1. Create a new file in tools/ (e.g., `tools/loan_analyzer.py`)
2. Write a function that returns a dict
3. Create a Pydantic model in models.py for the return type
4. Import and register it in server.py with `@mcp.tool()`

**To connect real data:** Set the `TREASURY_DATA_DIR` environment variable to point at a folder with real CSVs in the same format. Or replace the CSV reads with API calls to Plaid, MX, or your bank's API. The tool interface stays the same — only the data source changes.

**To connect to Claude Desktop:** Edit `~/Library/Application Support/Claude/claude_desktop_config.json` and add your server. Then restart Claude Desktop.
