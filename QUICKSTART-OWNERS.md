# TreasuryOS — Quick Start for Business Owners

Your AI-powered CFO assistant. Know exactly where your money is, where it's going, and what you're leaving on the table.

No finance degree required. No spreadsheet gymnastics. Just ask questions in plain English.

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

1. **A Mac** (Windows support coming soon)
2. **Claude Desktop** — download free at [claude.ai/download](https://claude.ai/download)
3. **Your financial data** as CSV files (details below) — or just try it with the included sample data first

---

## Setup (One Command)

Open **Terminal** (press `Cmd + Space`, type "Terminal", hit Enter) and paste this:

```bash
git clone https://github.com/GPBK-STUY/treasury-mcp-os.git ~/Desktop/treasury-mcp-os && bash ~/Desktop/treasury-mcp-os/setup.sh
```

The script handles everything. When it finishes:

1. **Quit Claude Desktop completely** (right-click the dock icon → Quit)
2. **Reopen Claude Desktop**
3. Look for the **hammer icon** 🔨 in the bottom-right of the chat box
4. Click it — you should see **TreasuryOS** with 9 tools listed

---

## Questions to Ask Claude

Once TreasuryOS is connected, just talk to Claude like you're talking to a financial advisor. Here are real questions to start with:

### Your Cash
- "Where is all my cash right now? Break it down by account."
- "Am I leaving money on the table with my current bank accounts?"
- "What does my cash flow look like for the next 90 days? Any red flags?"

### Your Bills & Vendors
- "Which vendors are offering me early-pay discounts? Are any of them worth taking?"
- "Do I have any foreign currency exposure I should worry about?"

### Your Debt
- "Am I in compliance with all my loan covenants?"
- "How much headroom do I have before I trip a covenant?"

### Your Credit
- "Break down my credit reports — personal and business. What do lenders see?"
- "Based on my cash and credit, how much could I borrow if I needed to?"
- "What's hurting my credit the most and what should I fix first?"

### The Big Picture
- "Give me the full financial picture — cash, debt, credit, everything."
- "If I wanted to apply for a line of credit next quarter, where do I stand?"
- "What are the top 3 things I should fix in my financial position right now?"

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
