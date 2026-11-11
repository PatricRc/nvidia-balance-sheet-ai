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

Gold guarantees **one `is_latest_filing` row per concept × fiscal year × fiscal period**, and on Q1–Q3 income rows it is the **standalone 3-month** row (a 10-Q also carries the 6/9-month YTD row; the notebook asserts YTD never wins). So `[Revenue]` / `[Net Income]` on a 10-Q are standalone quarters.

`[Revenue Standalone Quarter]` / `[Net Income Standalone Quarter]` (hidden) return one standalone quarter for any fiscal quarter-end: Q1–Q3 = the base measure; at the FY end Q4 is derived as **FY − Q1 − Q2 − Q3** (BLANK unless all three quarters exist).

`[TTM Revenue]` / `[TTM Net Income]` sum the four standalone quarters ending at the latest period (via the helpers) and are **BLANK unless all four exist** — a missing quarter is never counted as 0. If the current period is the annual 10-K (`fiscal_period = FY` or duration > 300 days), TTM equals the annual measure.

P&L **QoQ** measures compare standalone quarters, so **Q1 is compared with the derived Q4** (not with the 12-month 10-K total). They are **BLANK** when the latest period is annual, or the prior quarter is missing. Balance-sheet QoQ at year-end is Q4 vs Q3 (point-in-time) and is kept.

All `* Change` measures (YoY and QoQ) return **BLANK when the current or prior value is missing** — never the full current value as a fake "change".

`[Revenue CAGR 3Y]` / `[5Y]` use the latest **completed** fiscal year on or before the latest period in context (an in-progress year falls back to the prior FY) and are BLANK when either endpoint is missing (previously −100%).

Cash-flow 10-Q figures with `duration_days > 100` are YTD (`[Cash Flow Is YTD]`). `[CFO to Net Income]` is **BLANK** when cash flow is YTD but Net Income is a standalone quarter (Q2/Q3), so windows always match.

## Debt, leases and net cash (page 3)

| Measure | Definition |
|---|---|
| `[Long-Term Debt Current]` | `LongTermDebtCurrent` (tagged from FY2020) |
| `[Gross Debt]` | `[Long-Term Debt]` + `[Long-Term Debt Current]` (blank current portion = 0). Leases excluded. |
| `[Operating Lease Liabilities]` | `OperatingLeaseLiabilityCurrent` + `OperatingLeaseLiabilityNoncurrent`, shown separately |
| `[Net Cash]` | `[Cash]` + `[Marketable Securities]` − `[Gross Debt]`. Follows `[Marketable Securities]`. |
| `[Net Cash (Cash Only)]` | `[Cash]` − `[Gross Debt]` — conservative, always available; label it "cash only" |
| `[Period Label]` | Text such as `Q2 FY2027 · ended 2026-07-26` for card subtitles |

FY2026 check: Gross Debt = 7,469 + 999 = **$8,468M** (= us-gaap `LongTermDebt`); Net Cash (Cash Only) = 10,605 − 8,468 = **$2,137M**; Marketable Securities = 39,065 + 12,886 = **$51,951M** (Q2 FY2027 10-Q comparative); Net Cash = 10,605 + 51,951 − 8,468 = **$54,088M**; Quick Ratio = (10,605 + 51,951 + 38,466) / 32,163 = **3.14**.

## Concepts used

Only curated `gold.dim_line_item` concepts (29 rows). Revenue prefers `RevenueFromContractWithCustomerExcludingAssessedTax` then `Revenues` (already in `[Revenue]`). Cost of Revenue prefers `CostOfRevenue` then `CostOfGoodsAndServicesSold`. Dividends use `PaymentsOfDividends`. `MarketableSecuritiesCurrent` stops at Q3 FY2026 (2025-10-26): NVIDIA no longer tags it from the FY2026 10-K and companyfacts has no us-gaap replacement (`AvailableForSaleSecuritiesDebtSecurities` also includes cash equivalents). `[Quick Ratio]` and `[Net Cash]` therefore return **BLANK** for those periods instead of treating it as 0, which would understate liquidity by tens of billions.

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
