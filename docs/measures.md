# NVIDIA Financials — KPI, ratio, and analysis measures

Applied by `fabric/notebooks/nb_measures_financial.ipynb` onto the **NVIDIA Financials** Direct Lake model. Host table: **Balance Sheet**. Display folders: `02-kpi`, `03-ratios`, `04-analysis`. Base totals in `01-base` (`[Revenue]`, `[Net Income]`, `[Total Assets]`, `[Total Equity]`, `[Cash]`, `[Operating Cash Flow]`, `[Debt to Equity]`, `[Revenue YoY %]`, …) are reused, not redefined.

All period-based measures use the **single latest `period_end` in filter context** with `is_latest_filing = TRUE()`. Balance-sheet amounts are point-in-time. Income and cash-flow amounts are duration totals for that one period (not a sum of quarters). Time intelligence uses `Date[fiscal_year]`, `Date[fiscal_quarter]`, and `is_fiscal_quarter_end` — not `SAMEPERIODLASTYEAR` or `DATEADD` on calendar months (NVIDIA is a 52/53-week fiscal calendar ending the last Sunday of January).

## Average vs ending balances

`[Average Assets]`, `[Average Equity]`, `[Average Inventory]`, and `[Average Receivables]` are **(ending + prior-period-end) / 2**. At **fiscal-year grain** the prior period is the prior FY end; at **fiscal-quarter grain** it is the prior fiscal-quarter end (Q1 wraps → Q4 of the prior FY). If the prior balance is missing, the measure **falls back to the ending balance**.

`[ROE]`, `[ROA]`, `[Asset Turnover]`, and `[Equity Multiplier]` all use those averages, so DuPont tiles:

`[Net Margin %] × [Asset Turnover] × [Equity Multiplier] = [ROE]`

`[DuPont Check]` is `[DuPont ROE] − [ROE]` and should be ~0.

Ratios are **not annualized** in a quarterly context (quarterly net income over average equity is a quarterly ROE).

## Day counts (DIO / DSO)

`[DIO]` and `[DSO]` use `[Period Days]` = `duration_days` of the latest income-statement period (COALESCE 365). A NVIDIA fiscal year is typically **363 days**, not 365.

## TTM and Q4

`[TTM Revenue]` and `[TTM Net Income]` sum four **standalone** fiscal quarters. Q4 is not filed as a 10-Q; it is derived as **FY − Q1 − Q2 − Q3** only when those three quarters exist, are `is_latest_filing`, and are **not** `is_ytd`. If the current period is the annual 10-K (`fiscal_period = FY` or duration > 300 days), TTM equals the annual measure.

P&L **QoQ** measures are **BLANK** when the latest period is annual, so a 10-K total is not compared to Q3. Balance-sheet QoQ at year-end is Q4 vs Q3 (point-in-time) and is kept.

Cash-flow 10-Q figures with `duration_days > 100` are YTD (`[Cash Flow Is YTD]`). `[CFO to Net Income]` can mix YTD cash with a standalone quarter of earnings in that case — prefer annual or aligned windows.

## Concepts used

Only curated `gold.dim_line_item` concepts (29 rows). Revenue prefers `RevenueFromContractWithCustomerExcludingAssessedTax` then `Revenues` (already in `[Revenue]`). Cost of Revenue prefers `CostOfRevenue` then `CostOfGoodsAndServicesSold`. Dividends use `PaymentsOfDividends`. Quick Ratio treats a blank `MarketableSecuritiesCurrent` as 0 (missing in some years, including FY2026 companyfacts).

## Skipped (no invented concepts)

| Requested | Why skipped |
|---|---|
| SG&A | Not in `gold.dim_line_item` |
| Shares / weighted-average shares | Not in the map (only `EarningsPerShareDiluted`) |
| Interest Coverage / interest expense | Not in the map |
| Dividends Paid (Common) | Concept `PaymentsOfDividendsCommonStock` is in the map but **absent** from NVIDIA companyfacts; `[Dividends Paid]` uses `PaymentsOfDividends` |
| Shareholders' Equity (separate measure) | Same as existing `[Total Equity]` (`StockholdersEquity`) |
| Debt to Equity, Revenue YoY % | Already in `01-base`; not redefined |

CapEx / Free Cash Flow stay in `01-base` (CapEx is blank after mid-FY2020 in companyfacts).
