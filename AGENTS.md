# AGENTS.md — TreasuryOS (treasury-mcp-os)

Instructions for AI coding agents (Codex, GitHub Copilot, Cursor, Claude Code, Replit Agent, Devin, etc.).
Humans: see [README.md](README.md).

## What this repo is

TreasuryOS is a **Model Context Protocol (MCP) server** plus three Streamlit apps that share one
Python analysis engine for small-business banking: cash position, cash-flow forecasting, working
capital, debt covenants, FX exposure, idle cash, payment timing, and credit/loan readiness.

- **MCP server:** `server.py` (FastMCP, 9 tools). Runs over stdio (default) or streamable HTTP.
- **Apps:** `smb_app.py` (business owners), `rm_dashboard.py` (relationship managers), `app.py` (full dashboard).
- **Engine:** `tools/` — pure functions, no side effects, read CSVs from a data directory.

## Setup & run

```bash
# installed package (no clone): uvx treasury-mcp-os

# with uv (preferred)
uv sync                               # MCP server deps only
uv sync --extra apps                  # + Streamlit / PDF / Excel deps for the apps
uv run server.py                      # MCP server, stdio
MCP_TRANSPORT=streamable-http uv run server.py   # MCP server, HTTP on $PORT (default 8000), path /mcp

# with pip
pip install -r requirements.txt
python server.py

# Streamlit apps
streamlit run smb_app.py
streamlit run rm_dashboard.py
streamlit run app.py
```

Python 3.11+. No API keys or secrets are required; everything runs on local CSV data.

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `TREASURY_DATA_DIR` | `./sample_data` | Folder of CSVs the tools read |
| `MCP_TRANSPORT` | `stdio` | `stdio`, `sse`, or `streamable-http` |
| `HOST` / `PORT` | `0.0.0.0` / `8000` | Bind address when using an HTTP transport |

## MCP tools

| Tool | Inputs | Purpose |
|---|---|---|
| `get_cash_position` | — | Balances by currency and account type |
| `scan_idle_balances` | `operating_reserve_pct=0.20`, `target_yield_bps=450` | Idle cash that could earn more |
| `forecast_cash_position` | `horizon_days=90` (7–365) | Cash forecast from transaction history |
| `analyze_working_capital` | current assets/liabilities, revenue, AR, AP, COGS | Current ratio, DSO/DPO/DIO, cash cycle |
| `optimize_payment_timing` | `available_cash=0` | Early-pay discounts worth taking |
| `scan_fx_exposure` | — | Unhedged FX, VaR, hedge suggestions |
| `monitor_debt_covenants` | — | Covenant breaches and warnings |
| `parse_credit_report` | — | FICO, Paydex, utilization, derogatories |
| `assess_credit_position` | `annual_gross_income=0` | Combined credit + cash-flow lending readiness |

Common chains and the financial/credit guardrails the tools' outputs must respect are in
[CLAUDE.md](CLAUDE.md). Read it before changing scoring logic or thresholds.

## Data format

Each client is a folder of CSVs: `accounts.csv`, `transactions.csv`, `vendors.csv`, `fx_rates.csv`,
`covenants.csv`, `personal_credit.csv`, `business_credit.csv`.
- `sample_data/` — single demo company (Apex Manufacturing).
- `portfolio_data/<client-slug>/` — multi-client book for the RM dashboard; `portfolio_data/clients.csv` indexes them.

All data in this repo is synthetic. Never commit real customer data.

## Repo layout

```
server.py          MCP server entry point (main())
models.py          Pydantic models shared by tools
tools/             Analysis engine — one module per tool
smb_app.py         Streamlit: business-owner loan readiness app
rm_dashboard.py    Streamlit: RM portfolio dashboard
app.py             Streamlit: full dashboard
sample_data/       Demo CSVs
portfolio_data/    Multi-client demo CSVs
setup.sh           Installs the server into Claude Desktop
treasury_mcp_os/   Package shim; the wheel bundles server.py, models.py, tools/, sample_data/ inside it
server.json        MCP Registry metadata
```

## Releasing

Bump `version` in `pyproject.toml`, then push a tag `vX.Y.Z`. `.github/workflows/publish.yml`
builds, smoke-tests, publishes to PyPI (trusted publishing) and to the MCP Registry (GitHub OIDC).

## Conventions for agents making changes

- Keep tools in `tools/` **pure and idempotent**: inputs in, dict out, no writes, no network.
- New tool → add module in `tools/`, wrap it with `@mcp.tool()` in `server.py` with a clear docstring
  (the docstring is what MCP clients show to models), and add a row to the table above.
- Money: format as `$1,250,000.00`; convert bps to % for display (450 bps = 4.50%).
- Credit output is advisory, never a lending decision.
- Don't commit `__pycache__/`, `.venv/`, `.DS_Store`, or `*.backup` files.
- Quick smoke test: `python -c "import server; print(server.get_cash_position())"`.
