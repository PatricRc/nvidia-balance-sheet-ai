# dax/

DAX measures for the Direct Lake semantic model **NVIDIA Financials** — one `.dax` file each with a commented header, grouped by page (same framework as `trading-analytics-fabric`). Applied in Fabric by `fabric/notebooks/nb_semantic_model.ipynb`.

| Folder | Purpose |
|---|---|
| `01-base/` | Core totals, ratios, YTD flag (implemented) |
| `02-page1-snapshot/` | Page 1 — Balance Sheet Snapshot |
| `03-page2-liquidity/` | Page 2 — Liquidity & Working Capital |
| `04-page3-debt/` | Page 3 — Debt & Net Cash |
| `05-page4-ai-notes/` | Page 4 — AI Analyst Notes & Evidence |
| `06-html-cards/` | KPI cards + insight panels (HTML Content visual) |
| `07-svg-visuals/` | Charts drawn in DAX as SVG (Image URL) |
| `08-page1-layout/` … `11-page4-layout/` | Framed cards, headers and rail per page |
| `12-alt-text/` | Alt-text sentences for the main visuals |
| `_all-measures.dax` | Concatenated 01-base script (and later pages) |

Base measures use the latest `period_end` in filter context and `is_latest_filing` only — they do not sum across quarters. See `fabric/semantic-model/README.md`.
