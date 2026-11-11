# dax/

DAX measures for the Direct Lake semantic model **NVIDIA Financials** — one `.dax` file each with a commented header. Hosted on **Balance Sheet**.

Applied in Fabric by:

- `fabric/notebooks/nb_semantic_model.ipynb` — `01-base`
- `fabric/notebooks/nb_measures_financial.ipynb` — `02-kpi`, `03-ratios`, `04-analysis`

| Folder | Purpose |
|---|---|
| `01-base/` | Core totals, FCF, Debt to Equity, Revenue YoY %, YTD flag |
| `02-kpi/` | Gross profit, operating income, working capital, R&D, EPS, buybacks, dividends, … |
| `03-ratios/` | Margins, ROE/ROA (average balances), liquidity, turnover, DIO/DSO, cash conversion |
| `04-analysis/` | QoQ/YoY, TTM, CAGR, common-size %, DuPont |
| `02-page1-snapshot/` … `12-alt-text/` | Later report-page / HTML / SVG measures (stubs) |
| `_all-measures.dax` | Concatenated 01–04 scripts |

Edit the per-measure `.dax` files only, then run `python scripts/build_measures.py` — it regenerates `_all-measures.dax` and the measure lists embedded in both notebooks (`--check` verifies they are in sync).

See `docs/measures.md` for formulas, average-vs-ending rules, and skipped concepts.
