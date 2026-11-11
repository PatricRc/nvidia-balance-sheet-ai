# 02 · Liquidity & Working Capital

**Browser prototype.** The browser composition uses a prominent working-capital figure, a ratio strip, and a zero-centered ranked chart of current asset changes. The layout table below is a future native report reference.

**Question.** How much coverage do current assets provide and where is that coverage concentrated?

**Opening line.** A wider working-capital cushion. Start with absolute working capital and the current ratio. Then separate cash, marketable securities, receivables and inventories. The warm paper treatment gives the statement ledger visual priority.

| Zone | Native layout target and binding |
| --- | --- |
| Context | Same masthead and dates as Snapshot. Add “Balances at fiscal period end.” |
| Summary | y=120–232. Working Capital, Current Ratio, and Cash Ratio. Show prior ratio to give the multiple a baseline. |
| Coverage | x=224–828, y=248–610. Current assets vs current liabilities for each date using grouped bars and a shared scale. Show the working-capital difference as text. |
| Liquidity ledger | x=844–1248. Current asset composition, current liabilities and working capital in exact USD millions. Keep cash ratio methodology in the caption. |
| Footer | Advance to Debt & Net Cash for interest-bearing obligations and liquidity definitions. |

**DAX.** Reuse Current Assets, Current Liabilities, Cash, Inventory and Accounts Receivable. Add blank-safe working capital and cash coverage for this report. Hold the strict quick ratio until the securities input reconciles. The current repo quick ratio can effectively omit a missing securities input. Inventory turnover, DIO and DSO belong in a second-level detail view with compatible period income and balance denominators.

**Check.** Q2 FY2027 current assets $197.412B, current liabilities $43.019B, working capital $154.393B, current ratio 4.59×, cash ratio 0.52×. Confirm that neither a missing liability nor a zero denominator is displayed as zero coverage.
