# TreasuryOS — Quick Start Guide

Get up and running in under 5 minutes. No coding required.

---

## What You Need

1. **A Mac** (Windows support coming soon)
2. **Claude Desktop** — download free at [claude.ai/download](https://claude.ai/download)
3. **Your client data** as CSV files (or use the included sample data to test)

---

## Setup (One Command)

Open **Terminal** (press `Cmd + Space`, type "Terminal", hit Enter) and paste this:

```bash
git clone https://github.com/GPBK-STUY/treasury-mcp-os.git ~/Desktop/treasury-mcp-os && bash ~/Desktop/treasury-mcp-os/setup.sh
```

That's it. The script installs everything and connects TreasuryOS to Claude Desktop.

**Already have the repo?** Just run:
```bash
bash ~/Desktop/treasury-mcp-os/setup.sh
```

---

## After Setup

1. **Quit Claude Desktop completely** (right-click the dock icon → Quit)
2. **Reopen Claude Desktop**
3. Look for the **hammer icon** 🔨 in the bottom-right of the chat box
4. Click it — you should see **TreasuryOS** with 9 tools listed

If you don't see the hammer icon, try quitting and reopening Claude Desktop one more time.

---

## What to Ask Claude

Once TreasuryOS is connected, just talk to Claude like you normally would. Here are some starters:

### Cash & Treasury
- "What's my current cash position across all accounts?"
- "Do I have any idle cash that could be earning more?"
- "Forecast my cash position for the next 90 days"
- "Check my debt covenant compliance"
- "Are there any early payment discounts I should take?"
- "What's my FX exposure look like?"

### Credit Analysis
- "Parse the credit reports on file"
- "Assess this client's credit position with $250K combined income"
- "Give me a full underwriting picture"

### Combining Tools
The real power is chaining questions:
- "Pull the cash position, check covenants, and run credit — give me the full picture"
- "What's the lending capacity based on credit and cash flow?"

---

## Using Your Own Data

Your data lives in the `sample_data` folder:

```
~/Desktop/treasury-mcp-os/sample_data/
```

Replace the sample CSVs with your client's data. The files TreasuryOS looks for:

| File | What It Contains | Required? |
|------|-----------------|-----------|
| `accounts.csv` | Bank account balances | Yes |
| `transactions.csv` | Transaction history | Yes |
| `covenants.csv` | Debt covenant terms & actuals | Optional |
| `vendors.csv` | Vendor payment terms & invoices | Optional |
| `fx_rates.csv` | FX rates for multi-currency | Optional |
| `personal_credit.csv` | Guarantor FICO data | Optional |
| `business_credit.csv` | Business credit (Paydex, D&B) | Optional |

**Tip:** Export from your core banking system or Excel → Save As CSV → drop it in the folder.

---

## Troubleshooting

**"I don't see the hammer icon"**
→ Quit Claude Desktop fully (not just close the window) and reopen it.

**"The tools show an error"**
→ Open Terminal and run: `bash ~/Desktop/treasury-mcp-os/setup.sh`
→ This will re-check everything and fix common issues.

**"I need to update to the latest version"**
→ Open Terminal and run:
```bash
cd ~/Desktop/treasury-mcp-os && git pull origin main && bash setup.sh
```

**"My CSV isn't working"**
→ Make sure your CSV has headers in the first row. Check the sample files for the expected column names.

---

## Questions?

GitHub: [github.com/GPBK-STUY/treasury-mcp-os](https://github.com/GPBK-STUY/treasury-mcp-os)

Built by a commercial banker, for commercial bankers.
