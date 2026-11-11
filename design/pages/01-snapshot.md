# 01 · Balance Sheet Snapshot

**Browser prototype.** The browser composition is an illustrated opening followed by vertical funding columns and an adjacent funding bridge in text. The full statement lives in chapter 05. The layout table below is a future native report reference.

**Question.** How much did the balance sheet expand and how did the funding mix change?

**Opening line.** The balance sheet expands. In the Q2 FY2027 preset, assets reached $320.272B, up $113.469B from FY2026 close. Show the change in liabilities and equity with the same comparator and scope. The design uses the chip image behind the chapter opening and keeps the analytical marks on paper.

| Zone | Native layout target and binding |
| --- | --- |
| Masthead | Header y=24–104. Show fiscal end date, comparison basis, filing form and an evidence action. |
| Summary | Three KPI columns y=120–232. Bind Total Assets, Total Liabilities, Total Equity and each matched change. Use units on every card. |
| Main visual | Left x=224–828, y=248–610. Two stacked horizontal bars for comparator and current. Stack liabilities plus equity and use a common zero baseline. Add an optional 100% composition mode. |
| Statement check | Right x=844–1248. Exact USD million amounts and the identity residual. |
| Footer | Guide the viewer to Liquidity. Include the comparator and filing accession in the evidence path. |

**DAX.** Reuse the base measures. Pin both observations to exact fiscal dates and show the residual from unrounded numbers. The comparison is fiscal year-end for this prototype. Use the existing QoQ and YoY measures only with their matching comparisons. Calculate liabilities/assets and equity/assets only when all three values are present. For a future trend use period end on the axis and retain the anchor for the displayed comparison. Validate that each trend point represents one balance and carries its period label.

**Check.** Compare $206.803B with $320.272B. Confirm the two deltas sum to $113.469B and the bars sum to 100% in common-size mode. Show any reconciliation difference in the table. Explain an unavailable balance without drawing a zero-length mark.
