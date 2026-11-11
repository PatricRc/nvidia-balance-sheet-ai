# Narrative and editorial contract

## How NVIDIA’s balance sheet changed

The report is a six-chapter financial statement analysis. Start with **scale and funding**, move to **near-term coverage**, then **interest-bearing obligations**, then follow the **filing evidence** into **financial statements**. Every chapter answers one financial question and supplies the next action. Each headline names a change the selected figures support. The evidence layer preserves the distinction between a filed number, a calculated interpretation, and an approved generated note.

| Chapter | Question | Default case, Q2 FY2027 vs FY2026 close |
| --- | --- | --- |
| 00 · Cover | What does this dossier explain? | Introduce the financing question, preview assets, working capital and debt, and show readers where to start. |
| 01 · Balance Sheet Snapshot | What grew and how was the expansion funded? | Assets rose by $113.469B. Equity increased $71.691B and liabilities increased $41.778B. These movements reconcile to the asset increase. |
| 02 · Liquidity & Working Capital | Did near-term coverage improve and what makes up the cushion? | Working capital expanded from $93.442B to $154.393B. The current ratio moved from 3.91× to 4.59×. Receivables, inventory and marketable securities need separate interpretation. |
| 03 · Debt & Net Cash | What happened to debt, and how does the definition of liquidity change the answer? | Debt carrying amount rose to $33.366B. Cash alone gives a net-debt position of $10.923B, while cash plus reported current marketable securities gives a positive net position of $66.003B. |
| 04 · AI Analyst Notes & Evidence | Which claims can I reproduce from the filings? | Show the calculation trail and exact values. The prototype shows editorial notes with filing evidence and a withheld AI state. |
| 05 · Financial Statements | What does the formal accounting presentation show? | A classified balance sheet plus switches for matching-period profit and cash flow, with supplemental debt and liquidity schedules. |

The default balance-sheet comparison is **since fiscal year-end**, a six-month balance-sheet comparison. It must never appear as QoQ or YoY. The FY2026 preset compares year-end with FY2025 close. A later multi-period trend needs separate verified period observations. Keep the current prototype honest with two observations in each comparison. The fiscal date, comparison date, unit and filing form stay visible throughout. [FY2027 Q2 Form 10-Q](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm) · [FY2026 Form 10-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm)

## Financial interpretation

- The two sides of the balance sheet reconcile. Changes in liabilities and equity are a funding composition view, with no causal claim about individual capital flows.
- Track working capital as an absolute cushion and current ratio as coverage. Receivables and inventory carry collection and conversion risk. Add coverage labels so the cash, securities, and receivables definitions are explicit.
- Use carrying amount for reported debt. List operating leases separately and give cash-only and marketable-securities-inclusive views distinct labels. Marketable equities can be volatile or subject to restrictions. Present this as a reporting-date definition, with separate evidence for restrictions, facilities or commitments.
- Keep statements and dates aligned. Use the exact fiscal-end for point-in-time items. A cash-flow YTD amount cannot be compared to one quarter of earnings as a cash-conversion ratio. Missing values, including missing source tags for known filing lines, must remain distinguishable from zero.

## Filter contract

The fiscal period is global across all six chapters. Current and comparative dates are locked to each preset. Amount versus common-size mode only changes the Snapshot composition visual. Help and evidence disclosure preserve the filter and focus. In the eventual report use a display-only bookmark for help and a separate reset action. A missing or ambiguous period yields an explicit prompt or unavailable state. Source paths must retain accession, statement line, date, and unit even when values are rounded for presentation.

## Layout references

The opening spread, ranked liquidity drivers, zero-centered debt comparison, evidence index, and statements folio each use a different composition. The approach draws on the separate story pages and ledger in [Trading Analytics Fabric](https://github.com/PatricRc/trading-analytics-fabric), the variance and account detail in [Transit Ledger](https://github.com/PatricRc/transit-ledger-mta-financial-dashboard), and the Overview, Production, Trade, and Tabular chapters in [The World of Peaches](https://github.com/gusbavia/the-world-of-peaches).
