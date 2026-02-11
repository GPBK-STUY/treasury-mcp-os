# TreasuryOS — Quick Reference Commands

## Start the MCP Inspector (for testing tools)
```
cd ~/Desktop/treasury-mcp-os
mcp dev server.py
```

## If port is already in use
```
lsof -ti:6274 -ti:6277 | xargs kill
mcp dev server.py
```

## Connect to Claude Desktop
Edit: ~/Library/Application Support/Claude/claude_desktop_config.json
```json
{
  "mcpServers": {
    "treasury": {
      "command": "python3",
      "args": ["/Users/grantpage/Desktop/treasury-mcp-os/server.py"]
    }
  }
}
```
Then restart Claude Desktop.

## Install dependencies (first time only)
```
pip3 install "mcp[cli]" pandas pydantic pydantic-settings
```

## Check Python version (need 3.11+)
```
python3 --version
```

## 12 Available Tools

### Phase 1: Treasury Analysis
1. get_cash_position — aggregated balances across all accounts
2. scan_idle_balances — finds cash earning below target yield
3. forecast_cash_position — 90-day weekly cash flow projection
4. analyze_working_capital — liquidity ratios and runway
5. optimize_payment_timing — early-pay discount opportunities
6. scan_fx_exposure — unhedged foreign currency risk
7. monitor_debt_covenants — compliance status and headroom

### Phase 2: Document Parsers
8. parse_balance_sheet — extracts data from BS (CSV/Excel)
9. parse_income_statement — extracts data from P&L (CSV/Excel)
10. parse_ap_aging — extracts vendor payables and aging buckets
11. parse_bank_statement — extracts balances and transactions
12. spread_financials — full credit analysis from BS + P&L

## Sample tool arguments for testing

### spread_financials (the big one)
- balance_sheet_path: sample_docs/balance_sheet.csv
- income_statement_path: sample_docs/income_statement.csv
- annual_debt_service: 0 (auto-calculates)
- annual_lease_payments: 384000

### analyze_working_capital
- current_assets: 11082500
- current_liabilities: 3675000
- annual_revenue: 26125000
- accounts_receivable: 3200000
- accounts_payable: 1850000
- annual_cogs: 16200000

### scan_idle_balances
- operating_reserve_pct: 0.20
- target_yield_bps: 450

## Save your work with git
```
cd ~/Desktop/treasury-mcp-os
git add -A
git commit -m "description of what you changed"
```
