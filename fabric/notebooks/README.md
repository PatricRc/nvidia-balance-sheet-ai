# fabric/notebooks/

Fabric notebook sources for `NVIDIA-BalanceSheet-AI` / lakehouse `NVIDIALakehouse`.

| Notebook | Role | Status |
|---|---|---|
| **`nb_bronze_silver_gold_sec_edgar.ipynb`** | End-to-end: SEC pull → bronze JSON → `silver.financial_fact` → `gold.balance_sheet` / `income_statement` / `cash_flow` + dims | **Implemented** — import into Fabric, attach `NVIDIALakehouse`, Run all |
| `nb_bronze_sec_edgar.py` | Stub pointer (logic lives in the .ipynb) | Pointer |
| `nb_silver_financial_fact.py` | Stub pointer | Pointer |
| `nb_gold_balance_sheet.py` | Stub pointer | Pointer |
| `nb_gold_ai_insight.py` | Batch Claude Messages API → `gold.ai_insight` | Not started |

## How to run

1. In workspace **NVIDIA-BalanceSheet-AI**, open or import `nb_bronze_silver_gold_sec_edgar.ipynb`.
2. Attach default lakehouse **NVIDIALakehouse** (schema-enabled).
3. Confirm parameter cell: `SEC_USER_AGENT = "DataPat.ai patricrc10@gmail.com"`.
4. Run all. Tables written with `saveAsTable` into schemas `silver` and `gold`.

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
