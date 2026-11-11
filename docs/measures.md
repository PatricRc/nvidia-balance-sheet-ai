# NVIDIA Financials — KPI, ratio, and analysis measures

Applied by `fabric/notebooks/nb_semantic_model.ipynb` (14 base measures) and `fabric/notebooks/nb_measures_financial.ipynb` (the other 70) onto the **NVIDIA Financials** Direct Lake model. All 84 measures live on the calculated **`_Measures`** table. Display folders use a Category path plus, where mapped, one or more Pages paths separated by `;` (a field can appear in several folders — see [Organize your measures](https://learn.microsoft.com/power-bi/transform-model/desktop-measures)). Folder metadata is `dax/measure-folders.csv`, applied by `scripts/build_measures.py`. Base totals in `01-base` (`[Revenue]`, `[Net Income]`, `[Total Assets]`, `[Total Equity]`, `[Cash]`, `[Operating Cash Flow]`, `[Debt to Equity]`, `[Revenue YoY %]`, …) are reused, not redefined.

## Measures table

`_Measures` is a calculated table with expression `ROW("Dummy", BLANK())`. The `Dummy` column is hidden so the table shows the measure icon at the top of the Data pane. The table is Import mode and **does not reference any Direct Lake table or column**, which is supported in every Direct Lake mode, including Direct Lake on SQL ([Direct Lake overview](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview)). This model is Direct Lake on OneLake (`use_sql_endpoint=False`), so a lakehouse stub table is unnecessary. The notebooks create the table if it is missing and will not drop it on rerun. TOM cannot move a measure: if one is still on `Balance Sheet` (or any other table), the notebook removes it and re-adds it on `_Measures` with the same expression, format string, and description.

## Display-folder tree

Counts are unique measures. A measure with several Pages folders is counted in each of those pages and once under its Category subject.

```
_Measures
├── Category
│   ├── 01 Base (14)
│   │   ├── Balance Sheet (5)        Total Assets, Total Liabilities, Total Equity, Cash, Long-Term Debt
│   │   ├── Income Statement (2)     Revenue, Net Income
│   │   ├── Cash Flow (3)            Operating Cash Flow, CapEx, Free Cash Flow
│   │   ├── Growth (1)               Revenue YoY %
│   │   ├── Profitability (1)        Net Income Margin %
│   │   ├── Leverage (1)             Debt to Equity
│   │   └── Period (1)               Cash Flow Is YTD
│   ├── 02 KPI (21)
│   │   ├── Balance Sheet (7)        Current Assets, Current Liabilities, Inventory, Accounts Receivable,
│   │   │                            Marketable Securities, Long-Term Debt Current, Operating Lease Liabilities
│   │   ├── Income Statement (5)     Gross Profit, Operating Income, Cost of Revenue, R&D Expense, EPS Diluted
│   │   ├── Cash Flow (4)            Share Repurchases, Dividends Paid, Cash from Investing, Cash from Financing
│   │   ├── Liquidity (3)            Working Capital, Net Cash, Net Cash (Cash Only)
│   │   ├── Leverage (1)             Gross Debt
│   │   └── Period (1)               Period Label
│   ├── 03 Ratios (21)
│   │   ├── Profitability (7)        Gross / Operating / Net Margin %, R&D % of Revenue, ROE, ROA, CFO to Net Income
│   │   ├── Liquidity (3)            Current Ratio, Quick Ratio, Cash Ratio
│   │   ├── Leverage (2)             Liabilities to Assets, Equity Multiplier
│   │   ├── Efficiency (4)           Asset Turnover, Inventory Turnover, DIO, DSO
│   │   └── Helpers (5)              Average Assets / Equity / Inventory / Receivables, Period Days
│   └── 04 Analysis (28)
│       ├── Growth (21)              YoY/QoQ change and % for Revenue, Net Income, Total Assets, Equity, Cash;
│       │                            Revenue CAGR 3Y / 5Y
│       ├── TTM (2)                  TTM Revenue, TTM Net Income
│       ├── DuPont (2)               DuPont ROE, DuPont Check
│       ├── Common Size (1)          Common Size %
│       └── Helpers (2)              Revenue / Net Income Standalone Quarter (hidden)
└── Pages
    ├── 00 Cover (16)
    ├── 01 Financial Position (17)
    ├── 02 Liquidity (16)
    ├── 03 Debt & Net Cash (10)
    ├── 04 Notes & Evidence (24)
    └── 05 Financial Statements (46)
```

Page folders follow the six HTML routes in the report prompt. Mapping starts from `reconciliation.csv` / `RECONCILIATION.md` and is completed with measures the report pages will need (for example `[Period Label]` on every page, liquidity ratios on Liquidity, DuPont on Notes & Evidence). Thirteen helper or growth measures have a Category folder only and no Pages folder: the four averages, `[Period Days]`, the two standalone-quarter helpers, Revenue/Net Income QoQ change and %, and the two CAGRs.

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
