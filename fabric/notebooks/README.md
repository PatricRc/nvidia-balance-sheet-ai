# fabric/notebooks/

Fabric notebook sources (exported `.py` / `.ipynb` cells), named like `trading-analytics-fabric`:

| Planned notebook | Role |
|---|---|
| `nb_bronze_sec_edgar.py` | Pull `submissions` + `companyfacts` from `data.sec.gov` with declared `User-Agent`; land once under `Files/bronze/sec/ingest_date=.../`; write ingest metadata |
| `nb_silver_financial_fact.py` | Flatten companyfacts → `silver.financial_fact` (concept × unit × period × form × accession × filed) |
| `nb_gold_balance_sheet.py` | Build `gold.balance_sheet_period` (fiscal-aware, latest-filed version rule, deterministic ratios) |
| `nb_gold_ai_insight.py` | Batch Claude Messages API over an evidence pack → `gold.ai_insight` (Key Vault secret; validated JSON) |
| `nb_bronze_delta_writes_cell.py` | Shared OneLake `abfss://` Delta write pattern (same fix as trading-analytics-fabric) |

**Day 1:** stubs only — no live pulls yet.
