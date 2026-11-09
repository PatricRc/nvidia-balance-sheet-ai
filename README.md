# NVIDIA — Behind the Balance Sheet

A Microsoft Fabric + Power BI portfolio project: SEC EDGAR companyfacts land once in a OneLake lakehouse, move through a bronze → silver → gold medallion model, feed a Direct Lake semantic model, and end in a four-page Power BI report. A server-side Claude batch job writes validated, citation-backed analyst notes into gold — never inventing numbers outside the evidence pack.

**Guiding question:** *How has NVIDIA's financial position changed?*

> **Status: Gold tables + calendar + Direct Lake model + KPI/ratio/analysis measures ready.** After gold, `gold.dim_date`, and `nb_semantic_model.ipynb` have been run (model **NVIDIA Financials** exists), import `fabric/notebooks/nb_measures_financial.ipynb`, attach `NVIDIALakehouse`, kernel **Python**, Run all. Report pages, Publish to web, Claude batch, and chatbot are not built yet.

## The story in four pages

| Page | Question | What it will show |
|---|---|---|
| **1 · Balance Sheet Snapshot** | What does the position look like now, and how did it change? | Period selector (fiscal), assets / liabilities / equity stack, YoY and multi-period trend, restatement flags |
| **2 · Liquidity & Working Capital** | Can near-term obligations be covered? | Cash & equivalents, current assets vs current liabilities, working-capital trend, liquidity ratios from gold |
| **3 · Debt & Net Cash** | How levered is the balance sheet, and what is net cash? | Gross debt (leases shown separately), net-cash definition card, restatement / version flags, trend |
| **4 · AI Analyst Notes & Evidence** | What does a grounded model say, and on which SEC facts? | Validated insight cards with SEC evidence IDs, model id, prompt version, token/cost, review status |

## Architecture

```
SEC EDGAR  data.sec.gov
  submissions + companyfacts JSON
  (free, no API key; fair-access ≤10 req/s;
   declared User-Agent required; no CORS)
        │
        ▼
nb_bronze_silver_gold_sec_edgar  (Fabric notebook)
        │  raw JSON landed once → Files/bronze/sec_edgar/…
        ▼
silver.financial_fact
  one row per taxonomy/concept/unit/observation
        │
        ▼
gold.balance_sheet + gold.income_statement + gold.cash_flow
  + gold.dim_filing + gold.dim_line_item
  primary-period + latest-filed rules; identity check
        │
        ├──► Direct Lake model **NVIDIA Financials** (`nb_semantic_model.ipynb` + `nb_measures_financial.ipynb`) ──► Power BI report (4 pages)
        │
        └──► Claude Messages API  (batch, server-side)
                key in Azure Key Vault only
                │
                ▼
         gold.ai_insight
           evidence IDs · model id · prompt version
           input hash · token usage · validation status
           reviewer · timestamp
```

**Phase 2 (not started):** a separate HTML / FastAPI chatbot that reads the same gold tables, calls Claude server-side, and is linked from the report. The API key never appears in the repo, notebooks checked into git, DAX, the `.pbix`/PBIP, or any HTML.

## Data-correctness rules

These are non-negotiable before any report page or AI note ships:

1. **Fiscal vs calendar.** NVIDIA’s fiscal year ends late January / early February. Labels use fiscal periods from the filing; calendar-year shortcuts are forbidden in gold and on the canvas.
2. **Instant vs duration.** Balance-sheet concepts are *instant* (point-in-time). Income / cash-flow concepts are *duration*. Do not mix them in the same fact grain without an explicit period type.
3. **10-Q YTD.** Duration facts on 10-Q with long windows are flagged `is_ytd` and kept raw. Standalone quarter derivation (Q2 = YTD₂ − YTD₁, Q4 = FY − 9M) is out of scope for v1 unless exact and lineage-tagged.
4. **Restatements.** Keep every filed version. Gold’s “latest-filed” rule selects the current series for charts and **retains the original accession** so restatement flags and citations stay honest.
5. **companyfacts ≠ the full filing.** EDGAR companyfacts is a structured extract, not the complete 10-K/10-Q narrative or every note disclosure. Say so on the report and in AI prompts.
6. **No double counting.** Gross debt, current portion of long-term debt, and lease liabilities are modelled as separate concepts. Net-cash definitions are documented on page 3 and computed once in gold / DAX — never ad-hoc in a visual.

## AI guardrails

Claude is a **citation engine over gold**, not a free-form equity analyst.

- No number may appear in an insight unless it is in the evidence pack for that run.
- Every claim carries at least one **evidence ID** (concept + period + accession / filed date).
- The model must **abstain** when evidence is insufficient; abstentions are stored, not dropped.
- A small, labelled **eval set** of expected insights / refusals gates prompt changes.
- **Human review** (`reviewer`, `validation_status`) is required before an insight is published to page 4.
- Prompt version, model id, input hash, and token usage are stored on every `gold.ai_insight` row.
- Secrets: `ANTHROPIC_API_KEY` lives in **Azure Key Vault** only. Never in `.env` committed to git, Fabric notebook source in this repo, DAX, report files, or HTML.

## Repository layout

```
dax/             DAX measures, one .dax file each (commented header)
  01-base/              core BS totals, ratios, period helpers
  02-kpi/               gross profit, WC, R&D, EPS, buybacks, dividends
  03-ratios/            margins, ROE/ROA, liquidity, turnover, DIO/DSO
  04-analysis/          QoQ/YoY, TTM, CAGR, common-size %, DuPont
  02-page1-snapshot/    later page 1 measures (stub)
  03-page2-liquidity/   later page 2 measures (stub)
  04-page3-debt/        later page 3 measures (stub)
  05-page4-ai-notes/    later page 4 measures (stub)
  06-html-cards/        KPI cards + insight panels (HTML Content visual)
  07-svg-visuals/       charts drawn in DAX as SVG (Image URL)
  08–11-page*-layout/   framed cards, headers and rail per page
  12-alt-text/          alt-text sentences for the main visuals
  _all-measures.dax     one script to load everything via DAX query view
powerbi/         theme JSON (generated from tokens once design starts)
html/            tokens.css (same tokens for HTML components)
dashboard/
  html/          HTML prototypes of the four pages (later)
  svg/           chart components
  screenshots/   rendered PNGs once the report exists
fabric/
  notebooks/     bronze SEC pull, silver flatten, gold BS + Claude batch
  semantic-model/ Direct Lake model notes
scripts/         Python generators for DAX / HTML / SVG (later)
docs/            build guide, correctness rules, AI eval notes
.env.example     placeholder names only — real secrets stay in Key Vault
```

## Tech

Microsoft Fabric (Lakehouse, Notebooks, OneLake, Direct Lake) · Delta Lake · Python · Power BI · SEC EDGAR `data.sec.gov` · Claude Messages API (batch, server-side) · Azure Key Vault · (phase 2) FastAPI + HTML chatbot

## Roadmap

| Stage | Item | Status |
|---|---|---|
| Day 1 | README, folder scaffold, `.gitignore`, `.env.example` | **Done** |
| Ingest | `nb_bronze_silver_gold_sec_edgar.ipynb` — bronze SEC JSON + `silver.financial_fact` + `gold.balance_sheet` / `income_statement` / `cash_flow` | **Done (notebook in repo; run in Fabric)** |
| Calendar | `nb_gold_dim_date.ipynb` — `gold.dim_date` | **Done (run in Fabric)** |
| Model | `nb_semantic_model.ipynb` — Direct Lake **NVIDIA Financials**, relationships, 01-base measures | **Done (run in Fabric)** |
| Measures | `nb_measures_financial.ipynb` — 02-kpi / 03-ratios / 04-analysis, validated vs gold | **Notebook in repo; run in Fabric (Python kernel)** |
| Next | First report page + Publish to web | Not started |
| | Claude batch notebook → `gold.ai_insight` + page 4 | Not started |
| | Phase 2 HTML/FastAPI chatbot linked from the report | Not started |
| Later | Save as PBIP and commit TMDL + report JSON | Not started |
| | Scheduled Fabric pipeline instead of manual Run all | Not started |

## Build (once notebooks exist)

1. Set `SEC_USER_AGENT` (and pull Claude credentials from Key Vault — never commit them).
2. Run bronze → silver → gold notebooks in the Fabric workspace / lakehouse named in `.env.example`.
3. Re-run gold (`nb_bronze_silver_gold_sec_edgar`) so date columns are Delta Date, then `nb_gold_dim_date` (checks still apply), then `nb_semantic_model.ipynb` (Python kernel, lakehouse attached) to create **NVIDIA Financials**, then `nb_measures_financial.ipynb` (same kernel and lakehouse) for KPI/ratio/analysis measures. Last cell must print OVERALL: PASS.
4. Apply `powerbi/` theme when generated.
5. Only after gold is hand-checked against the filing: run the Claude batch job and review `ai_insight` rows before publishing page 4.

## Data & attribution

- Source: [SEC EDGAR](https://www.sec.gov/edgar) company submissions and companyfacts via `data.sec.gov` (see [SEC fair access](https://www.sec.gov/os/accessing-edgar-data)).
- Declare a descriptive `User-Agent` on every request. Respect the ≤10 requests/second fair-access guidance. There is no API key and no browser CORS path into this API from a public HTML page.
- This repository does not redistribute SEC bulk files; notebooks are expected to land them in OneLake.

## Disclaimer

**Not investment advice.** This is an independent portfolio study of public SEC filings. It is not affiliated with NVIDIA Corporation, the SEC, Anthropic, or Microsoft. Figures in future report pages will be derived from EDGAR extracts and may differ from investor presentations or audited financial statement notes. Do not use this project to make trading or investment decisions.

[DataPat.ai](https://data-pat-ai.netlify.app/) · [LinkedIn](https://www.linkedin.com/in/patriciorioscanepa)
