# NVIDIABalanceSheetModel

Direct Lake semantic model (name TBD) on the NVIDIA lakehouse.

## Planned tables

| Table | Grain / role |
|---|---|
| `gold.balance_sheet_period` | One row per fiscal period × concept set (latest-filed rule) |
| `gold.ai_insight` | Validated Claude notes with evidence IDs and review status |
| `silver.financial_fact` | Optional supporting detail (not all columns on the canvas) |
| dims (date / period / concept / form) | As needed for slicers and relationships |

## Still to do (Day 1)

- Create Fabric workspace + lakehouse
- Relationships (facts → period / concept dims)
- DAX measures in `dax/`
- Cast / type checks for numeric concepts in silver
- Mark the period/date table correctly for time intelligence
