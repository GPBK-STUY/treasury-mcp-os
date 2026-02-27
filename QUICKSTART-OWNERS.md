# TreasuryOS — Quick Start for Business Owners

Your CFO dashboard. Know exactly where your money is, where it's going, and what you're leaving on the table.

No finance degree required. No spreadsheet gymnastics. No AI subscriptions. Just open your browser.

---

## What This Does For You

You know that feeling when your accountant sends a report and you think "great, but what does this actually mean for my business?" TreasuryOS answers the questions you actually care about:

- **"How much cash do I really have?"** — Pulls every bank account into one view. No more logging into three different banks.
- **"Am I wasting money?"** — Finds cash sitting in low-interest accounts that could be earning 4-5% somewhere else. For a business with $500K in checking, that's $20K+ per year you're giving away.
- **"Will I have enough cash next quarter?"** — Forecasts your cash position based on your actual transaction patterns. Know before it's a problem.
- **"Should I pay this vendor early?"** — Calculates whether early-payment discounts are worth taking. Sometimes 2/10 net 30 is free money. Sometimes it's not.
- **"Am I in trouble with my lender?"** — Monitors your debt covenants and flags when you're getting close to a breach — before your banker calls you.
- **"How does my credit look?"** — Breaks down your personal and business credit into plain language with specific things to fix.

---

## What You Need

1. **A Mac or PC** with a web browser
2. **Your financial data** as CSV files (details below) — or just try it with the included sample data first

That's it. No Claude subscription, no AI account, no special software.

---

## Setup (One Command)

Open **Terminal** (Mac: press `Cmd + Space`, type "Terminal", hit Enter) and paste this:

```bash
git clone https://github.com/GPBK-STUY/treasury-mcp-os.git ~/Desktop/treasury-mcp-os && cd ~/Desktop/treasury-mcp-os && bash setup.sh && uv run streamlit run app.py
```

Your browser will open automatically with the TreasuryOS dashboard.

**Already set up? Just run:**
```bash
cd ~/Desktop/treasury-mcp-os && uv run streamlit run app.py
```

---

## Using the Dashboard

The web dashboard has 10 pages you can navigate from the sidebar:

### Overview
Your financial snapshot — total cash, idle cash, covenant status, and credit rating all on one screen.

### Cash Position
Every bank account in one table. See balances by account type and currency.

### Idle Cash
Find money sitting in checking accounts earning nothing. The tool calculates exactly how much it's costing you per year — and what to do about it.

### Cash Forecast
See where your cash is headed over the next 30-365 days. Flags potential shortfalls before they happen.

### Vendor Payments
Should you pay a vendor early to capture a discount? The tool calculates the annualized return and tells you when it makes sense and when it doesn't.

### FX Exposure
If you pay any vendors in foreign currency, this shows your unhedged exposure and Value at Risk.

### Debt Covenants
Green/yellow/red status for every covenant. See your headroom percentage and get warned before you're in trouble.

### Credit Report
Your personal and business credit broken down — FICO scores, utilization, payment history, derogatories, everything a lender looks at.

### Credit Assessment
The full picture. Combines your credit, cash position, and covenant data into an overall rating with specific risk factors, lending capacity estimate, and recommendations.

### Working Capital
Enter your financials manually and get DSO, DPO, cash conversion cycle, current ratio, and runway. Know exactly how healthy your working capital is.

---

## Want AI-Powered Analysis Too?

The web dashboard gives you the numbers. If you also want to have a conversation with AI about your financials — ask follow-up questions, chain analyses together, get plain-English explanations — you can optionally connect TreasuryOS to Claude Desktop.

Run the setup script to configure Claude:
```bash
bash ~/Desktop/treasury-mcp-os/setup.sh
```

Then restart Claude Desktop and ask questions like:
- "Give me the full financial picture — cash, debt, credit, everything."
- "What are the top 3 things I should fix in my financial position right now?"
- "If I wanted to apply for a line of credit next quarter, where do I stand?"

---

## Loading Your Own Data

TreasuryOS comes with sample data so you can test it immediately. When you're ready to use your own numbers, here's what to do.

Your data goes in this folder:
```
~/Desktop/treasury-mcp-os/sample_data/
```

### Where to Get Your Data

| What You Need | Where to Get It | File to Create |
|---------------|----------------|----------------|
| Bank balances | Download from your online banking (most banks have a CSV export) | `accounts.csv` |
| Transactions | Download 3 months of history from each bank account | `transactions.csv` |
| Vendor invoices | Export from QuickBooks, Xero, or your AP system | `vendors.csv` |
| Loan covenants | Pull from your loan agreement or ask your banker | `covenants.csv` |
| Credit reports | Download from annualcreditreport.com (personal) or Nav.com / D&B (business) | `personal_credit.csv` and `business_credit.csv` |

**Don't have all of these?** That's fine. Only `accounts.csv` and `transactions.csv` are required. Start with those two and add the rest over time.

**Not sure about the format?** Look at the sample files in the `sample_data` folder — they show you exactly what columns are expected. Match those headers and you're good.

**Tip:** Most accounting software (QuickBooks, Xero, Wave, FreshBooks) can export to CSV. Look for "Export" or "Reports → Export to Excel/CSV" in your software.

---

## Troubleshooting

**"I don't see the hammer icon"**
→ Quit Claude Desktop fully (not just close the window — right-click the dock icon and click Quit) and reopen it.

**"Something broke"**
→ Open Terminal and run: `bash ~/Desktop/treasury-mcp-os/setup.sh`
→ This will re-check everything and fix common issues.

**"I want to update to the latest version"**
→ Open Terminal and run:
```bash
cd ~/Desktop/treasury-mcp-os && git pull origin main && bash setup.sh
```

**"My CSV isn't working"**
→ Open the sample files and compare your column headers to theirs. The headers need to match.

---

## What This Isn't

TreasuryOS is a financial analysis tool, not a financial advisor. It crunches your numbers and surfaces insights — it doesn't tell you what to do with your money. Always consult with your accountant, banker, or financial advisor before making major financial decisions.

Think of it as the smartest spreadsheet you've ever used, one that actually talks back.

---

## Questions?

GitHub: [github.com/GPBK-STUY/treasury-mcp-os](https://github.com/GPBK-STUY/treasury-mcp-os)

Built by a commercial banker who got tired of watching business owners fly blind.
