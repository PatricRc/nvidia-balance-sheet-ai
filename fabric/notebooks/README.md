# fabric/notebooks/

Fabric notebook sources for `NVIDIA-BalanceSheet-AI` / lakehouse `NVIDIALakehouse`.

| Notebook | Role | Status |
|---|---|---|
| **`nb_bronze_silver_gold_sec_edgar.ipynb`** | End-to-end: SEC pull → bronze JSON → `silver.financial_fact` → `gold.balance_sheet` / `income_statement` / `cash_flow` + dims | **Implemented** — import into Fabric, attach `NVIDIALakehouse`, Run all |
| **`nb_measures_financial.ipynb`** | KPI, ratio, and analysis measures on **NVIDIA Financials** (folders `02-kpi` / `03-ratios` / `04-analysis`), validated vs gold | **Implemented** — Python kernel, attach `NVIDIALakehouse`, Run all after the semantic model exists |
| **`nb_semantic_model.ipynb`** | Direct Lake model **NVIDIA Financials**: tables, relationships, date table, 01-base measures, FY2026 assert | **Implemented** — import, attach `NVIDIALakehouse`, kernel **Python**, Run all |
| **`nb_gold_dim_date.ipynb`** | Contiguous `gold.dim_date` (calendar + NVIDIA fiscal calendar) for Direct Lake | **Implemented** — run after gold statements exist |
| `nb_bronze_sec_edgar.py` | Stub pointer (logic lives in the .ipynb) | Pointer |
| `nb_silver_financial_fact.py` | Stub pointer | Pointer |
| `nb_gold_balance_sheet.py` | Stub pointer | Pointer |
| `nb_gold_ai_insight.py` | Batch Claude Messages API → `gold.ai_insight` | Not started |

## How to run

1. In workspace **NVIDIA-BalanceSheet-AI**, open or import `nb_bronze_silver_gold_sec_edgar.ipynb`.
2. Attach default lakehouse **NVIDIALakehouse** (schema-enabled).
3. Confirm parameter cell: `SEC_USER_AGENT = "DataPat.ai patricrc10@gmail.com"`.
4. Run all. Tables written with `saveAsTable` into schemas `silver` and `gold`. Date columns (`period_end`, `start`/`end`, `filed`, `filingDate`/`reportDate`, `ingest_date`) are stored as Date.
5. Import/open **`nb_gold_dim_date.ipynb`**, attach the same lakehouse, Run all → `gold.dim_date` (re-run after a gold type change so the period_end checks still pass).
6. Import/open **`nb_semantic_model.ipynb`**, attach the same lakehouse, set kernel to **Python** (not PySpark), Run all → semantic model `NVIDIA Financials`. Requires XMLA read/write on the capacity. Run this only after gold date types are in place.
7. Import/open **`nb_measures_financial.ipynb`**, attach the same lakehouse, kernel **Python**, Run all → KPI/ratio/analysis measures. Requires the **NVIDIA Financials** model and XMLA read/write. Last cell must print OVERALL: PASS.

## Tables produced

| Table | Layer | Grain |
|---|---|---|
| `Files/bronze/sec_edgar/cik=0001045810/ingest_date=…/{companyfacts,submissions}.json` | Bronze | Raw SEC JSON (landed once per ingest_date) |
| `silver.financial_fact` | Silver | One row per taxonomy/concept/unit/observation |
| `gold.dim_filing` | Gold | One row per accession in submissions.recent |
| `gold.dim_line_item` | Gold | Curated statement line ↔ us-gaap concept |
| `gold.balance_sheet` | Gold | Long BS lines (instant) |
| `gold.income_statement` | Gold | Long IS lines (duration) |
| `gold.cash_flow` | Gold | Long CF lines (duration; YTD flagged) |

Named like `trading-analytics-fabric` (`nb_*`). No secrets in source.
