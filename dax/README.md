# dax/

DAX measures for the Direct Lake semantic model — one `.dax` file each with a commented header, grouped by page (same framework as `trading-analytics-fabric`).

| Folder | Purpose |
|---|---|
| `01-base/` | Core balance-sheet totals, period helpers, restatement flags |
| `02-page1-snapshot/` | Page 1 — Balance Sheet Snapshot |
| `03-page2-liquidity/` | Page 2 — Liquidity & Working Capital |
| `04-page3-debt/` | Page 3 — Debt & Net Cash |
| `05-page4-ai-notes/` | Page 4 — AI Analyst Notes & Evidence |
| `06-html-cards/` | KPI cards + insight panels (HTML Content visual) |
| `07-svg-visuals/` | Charts drawn in DAX as SVG (Image URL) |
| `08-page1-layout/` … `11-page4-layout/` | Framed cards, headers and rail per page |
| `12-alt-text/` | Alt-text sentences for the main visuals |
| `_all-measures.dax` | One script to load everything via DAX query view |

**Day 1:** folder stubs only. Measures land after gold tables exist and are hand-checked.
