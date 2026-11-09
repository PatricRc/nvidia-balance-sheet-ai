# Data correctness

Rules enforced by `nb_bronze_silver_gold_sec_edgar.ipynb`. Expand with more worked NVIDIA examples as gold is hand-checked against filed 10-K / 10-Q HTML.

## Rules

1. **Fiscal labels from the filing** — use `fy` / `fp` from companyfacts; do not relabel by calendar year. NVIDIA’s fiscal year ends late January.
2. **Instant vs duration** — balance-sheet concepts are *instant* (`start` is null). Income / cash-flow concepts are *duration*. Gold filters by the curated `expected_period_type`.
3. **Primary period vs comparatives** — a single 10-K often restates prior years under the same `fy`/`fp`. Mark `is_period_primary` when `period_end == filings.reportDate` for that `accn`. Charts / “latest” KPIs use `is_latest_filing` (latest filed among primary rows per concept+fy+fp).
4. **10-Q YTD** — duration facts on 10-Q with `duration_days > 100` are flagged `is_ytd=true`. Raw YTD is kept. Do **not** invent standalone quarters unless an exact derivation is coded (e.g. Q4 = FY − 9M YTD when both exist) and stored with lineage — that derivation is **not** in v1 of this notebook.
5. **Restatements** — silver keeps every observation. Gold collapses duplicates on `(concept, start, end, fy, fp, form_base, unit)` keeping the latest `filed` and retaining `accn` for citations.
6. **companyfacts ≠ the full filing** — structured XBRL extract only; footnotes and MD&A are out of scope for these tables.
7. **Identity check** — for every latest primary period that has both concepts: `Assets == LiabilitiesAndStockholdersEquity` within $1. Notebook prints pass/fail counts.
8. **Units** — statement money lines use `USD`; EPS uses `USD/shares`. Other units are excluded from gold statement tables.
9. **Debt / leases** — `LongTermDebtNoncurrent`, `OperatingLeaseLiabilityCurrent`, and `OperatingLeaseLiabilityNoncurrent` stay separate concepts (no silent netting in gold).

## Worked check (local verification, FY2026 10-K)

Source accession `0001045810-26-000021`, filed `2026-02-25`, period end `2026-01-25`:

| Line | Concept | value_usd |
|---|---|---|
| Total Assets | Assets | 206,803,000,000 |
| Total Liabilities | Liabilities | 49,510,000,000 |
| Stockholders' Equity | StockholdersEquity | 157,293,000,000 |
| Cash & Equivalents | CashAndCashEquivalentsAtCarryingValue | 10,605,000,000 |
| Long-Term Debt (Noncurrent) | LongTermDebtNoncurrent | 7,469,000,000 |
| Revenue | Revenues | 215,938,000,000 |
| Net Income (Loss) | NetIncomeLoss | 120,067,000,000 |
| Cash from Operating Activities | NetCashProvidedByUsedInOperatingActivities | 102,718,000,000 |

`Assets` − (`Liabilities` + `StockholdersEquity`) = 0 for that period.

## Known gaps

- `PaymentsOfDividendsCommonStock` is absent from NVIDIA companyfacts; gold uses `PaymentsOfDividends`.
- Recent annual revenue is tagged `Revenues`; older years may also have `RevenueFromContractWithCustomerExcludingAssessedTax` — both stay on `gold.dim_line_item`.
