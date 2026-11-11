# Data correctness

Rules enforced by `nb_bronze_silver_gold_sec_edgar.ipynb`. Expand with more worked NVIDIA examples as gold is hand-checked against filed 10-K / 10-Q HTML.

## Rules

1. **Fiscal labels from the filing** — use `fy` / `fp` from companyfacts; do not relabel by calendar year. NVIDIA’s fiscal year ends late January.
2. **Instant vs duration** — balance-sheet concepts are *instant* (`start` is null). Income / cash-flow concepts are *duration*. Gold filters by the curated `expected_period_type`.
3. **Primary period vs comparatives** — a single 10-K often restates prior years under the same `fy`/`fp`. Mark `is_period_primary` when `period_end == filings.reportDate` for that `accn`. Charts / “latest” KPIs use `is_latest_filing` (latest filed among primary rows per concept+fy+fp).
4. **10-Q YTD** — duration facts on 10-Q with `duration_days > 100` are flagged `is_ytd=true`. Raw YTD is kept. Do **not** invent standalone quarters unless an exact derivation is coded (e.g. Q4 = FY − 9M YTD when both exist) and stored with lineage — that derivation is **not** in v1 of this notebook.
5. **Restatements** — silver keeps every observation. Gold collapses duplicates on `(concept, start, end, fy, fp, form_base, unit)` keeping the latest `filed` and retaining `accn` for citations. Because `fy`/`fp` are the *filing's* fiscal period and primary rows require `end == reportDate` of that filing, gold shows values **as originally reported**; comparatives restated in later filings are kept in silver only.
   - **One latest row per period** — a Q2/Q3 10-Q carries both the 3-month and the 6/9-month YTD duration row with the same end, accession and filed date. `is_latest_filing` prefers the standalone 3-month row (also on the older-filing fallback path); YTD is latest only when it is the sole window (10-Q cash flows). The notebook asserts zero YTD income rows among Q1–Q3 latest rows and exactly one latest row per concept × fy × fp.
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

- From the FY2026 10-K onward NVIDIA stopped tagging `MarketableSecuritiesCurrent` (last value: Q3 FY2026, 2025-10-26, 49,122 M). Later 10-Qs tag `DebtSecuritiesCurrent` + `EquitySecuritiesFvNi` instead; gold maps both, and `[Marketable Securities]` uses the old tag when present, otherwise the sum of those two at the same `period_end` (latest filing, so FY2026 close is the 10-Q comparative — the 10-K has no current-securities total). Do not add `EquitySecuritiesFVNINoncurrent` (noncurrent; 22,251 M at FY2026). Do not use `AvailableForSaleSecuritiesDebtSecurities` (39,520 M at FY2026, 455 M above `DebtSecuritiesCurrent`, and it includes cash equivalents). `EquitySecuritiesFvNi` is not labeled current in the taxonomy; NVIDIA presents it as the current marketable-equity companion to `DebtSecuritiesCurrent` from FY2026, and it overlapped `MarketableSecuritiesCurrent` in FY2022 (do not add the two).
- `PaymentsOfDividendsCommonStock` is absent from NVIDIA companyfacts; gold uses `PaymentsOfDividends`.
- `PaymentsToAcquirePropertyPlantAndEquipment` (CapEx) last appears in NVIDIA companyfacts around mid-FY2020; later periods (including FY2026) have no CapEx row, so Free Cash Flow is BLANK.
- Recent annual revenue is tagged `Revenues`; older years may also have `RevenueFromContractWithCustomerExcludingAssessedTax` — both stay on `gold.dim_line_item`.


## `gold.dim_date` (calendar + NVIDIA fiscal)

Built by `nb_gold_dim_date.ipynb` as a **physical Delta table** (required for Direct Lake — do not replace with a DAX calculated date table).

**Fiscal rule** (validated 24/24 vs SEC submissions `reportDate` for 10-K/10-Q, FY2021–Q2 FY2027):

1. Fiscal year ends on the **last Sunday of January**.
2. Fiscal year number = calendar year of that January end (`FY2026` ended `2026-01-25`).
3. Q1–Q3 = **13 weeks** each from FY start; Q4 = remainder (13 or 14 weeks).
4. Known checks: FY2026 → `2026-01-25`; Q2 FY2027 → `2026-07-26`.

**Join key:** `date` (DateType) / `date_key` (yyyymmdd). Fact `period_end` (and other date-ish gold/silver columns) are written as Delta **Date** via `to_date` in `nb_bronze_silver_gold_sec_edgar`, then joined to `Date[date]`.

**Coverage:** Jan 1 of the earliest gold `period_end` year through the end of the NVIDIA fiscal year that contains (~today + 2 years). Overwrite rebuild.

**Assert:** every primary (`is_period_primary`) `period_end` in the three gold statement tables has `is_fiscal_quarter_end = true`. Relative “is_today / offset” flags are omitted on purpose — they go stale under Direct Lake; put those in DAX if needed.
