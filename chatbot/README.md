# Claude analyst chatbot (RAG over the NVIDIA Financials semantic model)

A chat panel inside the Power BI report that answers questions about NVIDIA's financial position
using **only** the Direct Lake semantic model **NVIDIA Financials**, with SEC evidence and a
grounding check on every number. Claude (Opus 5.5) runs server-side; the Anthropic API key never
reaches the report, the visual, DAX or HTML.

```
Power BI report (Fabric)                       Azure Container Apps                         Fabric
┌──────────────────────────┐   HTTPS + SSE   ┌───────────────────────────────┐  executeQueries  ┌────────────────────┐
│ NVIDIA Analyst Chat      │ ──────────────► │ FastAPI  /api/chat            │ ───────────────► │ NVIDIA Financials  │
│ (custom visual, WebAccess│ ◄────────────── │  ├ catalog.py  (retrieval)    │ ◄─────────────── │ Direct Lake model  │
│  privilege, no secrets)  │   tokens/events │  ├ tools.py    (safe DAX)     │   rows (JSON)    │ (gold Delta tables)│
│ Date[fiscal_year/quarter]│                 │  ├ agent.py    (Claude loop)  │                  └────────────────────┘
│ → report_context         │                 │  └ grounding.py(number check) │
└──────────────────────────┘                 │ Key Vault: ANTHROPIC_API_KEY  │ ──► Claude Messages API
  or: standalone page (/)                    │ Managed identity / SP → Power BI│    (claude-opus-5-5, streaming)
      with the report embedded               └───────────────────────────────┘
```

## How the RAG works

Retrieval happens in two stages, both against the semantic model rather than a document store:

| Stage | What is retrieved | How |
|---|---|---|
| 1. Schema retrieval | Which measures / us-gaap concepts / tables answer the question | `search_semantic_model` - BM25 over a catalog built at startup from `dax/<folder>/*.dax` (all 84 measures with definitions) and the gold `CONCEPT_MAP`. The digest is also in the cached system prompt. `executeQueries` does not support `INFO` functions or DMVs, so the catalog comes from the repo (the source of truth the model is built from). |
| 2. Data retrieval | Live numbers and SEC evidence | `query_measures`, `get_trend`, `get_sec_evidence` build DAX from validated, whitelisted inputs and run it through the Power BI **Execute Queries** REST API. |
| 3. Generation | The answer | Claude writes only from tool results; `grounding.py` then checks every $, %, and x figure in the answer against the numbers the tools returned and labels the answer *verified* / *unverified*. |

Tools Claude can call:

| Tool | DAX it builds | Guardrails |
|---|---|---|
| `search_semantic_model(query, k)` | none (catalog search) | - |
| `query_measures(measures[], periods[])` | `EVALUATE UNION(ROW("request", …, "Period Label", CALCULATE([Period Label], …), "<measure>", CALCULATE([<measure>], 'Date'[fiscal_year] = …, 'Date'[fiscal_quarter] = …)), …)` | measure names must exist in the catalog; ≤ 12 measures × 8 periods; one table per query |
| `get_trend(measure, grain, last_n)` | `SUMMARIZECOLUMNS('Date'[fiscal_year], 'Date'[fiscal_quarter], TREATAS({TRUE()}, 'Date'[is_fiscal_quarter_end]), "value", [<measure>])` + `TOPN` | measure whitelisted; 2-24 points |
| `get_sec_evidence(concepts[], fiscal_year, fiscal_period)` | `UNION` of `SELECTCOLUMNS(FILTER(<fact>, is_latest_filing && …), …, RELATED('Filing'[sec_url]))` over the three fact tables | concept names regex-checked; returns `evidence_id = concept|period_end|accn` |
| `run_dax_query(query)` | the query as given | **off by default** (`ALLOW_FREEFORM_DAX`); must start with `EVALUATE`/`DEFINE`; ≤ 200 rows returned |

Claude API details (from the official docs / Python SDK 2.x): `client.beta.messages.stream` with
`thinking={"type": "adaptive"}`, `output_config={"effort": "medium"}`, server-side refusal
fallbacks (`betas=["server-side-fallback-2026-07-01"]`, `fallbacks="default"`), strict tool schemas with
`eager_input_streaming` (inputs validated with pydantic before any DAX runs), prompt caching on the
stable system prompt + catalog, and the report's slicer state sent as a mid-conversation `system`
message. Turns that stop on `refusal` or `max_tokens` never execute their tools.

## Repository layout

```
chatbot/
  backend/
    app/config.py      settings (env / .env), no secrets in code
    app/keyvault.py    ANTHROPIC_API_KEY from Azure Key Vault (DefaultAzureCredential)
    app/catalog.py     semantic-model catalog + BM25 retrieval
    app/powerbi.py     executeQueries client (token, 120/min limiter, errors) + offline fixture backend
    app/tools.py       tool schemas, input validation, DAX builders, executor
    app/agent.py       Claude streaming tool loop -> SSE events
    app/grounding.py   number-level grounding check
    app/main.py        FastAPI: /api/chat (SSE), /api/health, static UI, CORS, rate limit, daily budget
    app/static/index.html  standalone chat page (optionally embeds the published report)
    app/fixtures/fy2026.json  offline demo rows (real FY2026 SEC values)
    tests/             19 tests: catalog, DAX builders, validation, grounding, agent loop, API
    Dockerfile         build from repo root (ships dax/ + concept map for the catalog)
  visual/              Power BI custom visual (pbiviz, API 5.11) - chat inside the report
```

## Run locally (no Azure needed)

```bash
cd chatbot/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

```bash
export ANTHROPIC_API_KEY=...   # or `ant auth login`; local only
POWERBI_MODE=fixture uvicorn app.main:app --reload
```

Open http://localhost:8000. Fixture mode answers from `app/fixtures/fy2026.json` (FY2026 figures, a
revenue trend, SEC evidence rows) so you can try the full Claude loop without Fabric. Every real
question costs Claude API tokens.

## Connect to the live semantic model

1. **Tenant settings** (Fabric admin portal): enable *Dataset Execute Queries REST API*
   (Integration settings) and *Service principals can use Fabric/Power BI APIs* (Developer settings,
   scoped to a security group).
2. **Identity**: create an Entra app registration (service principal) or use the Container App's
   managed identity. Add it to workspace **NVIDIA-BalanceSheet-AI** as *Viewer* and give it **Build**
   on **NVIDIA Financials**. The model has no RLS (service principals cannot query RLS/SSO models).
3. **IDs**: `FABRIC_WORKSPACE_ID` = workspace (group) id, `POWERBI_DATASET_ID` = the semantic model id
   (from its URL in Fabric).
4. Set `POWERBI_MODE=live`. The backend requests a token for
   `https://analysis.windows.net/powerbi/api/.default` with `DefaultAzureCredential`
   (managed identity in Azure; `AZURE_TENANT_ID` / `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` locally).

Limits respected by `powerbi.py`: one query and one table per call, 100,000 rows / 1,000,000 values /
15 MB per query, 120 queries per minute per identity (client throttles at `POWERBI_QUERIES_PER_MINUTE=100`).

## Deploy (Azure Container Apps)

Build from the repository root (the image ships `dax/` and the gold notebook for the catalog):

```bash
az acr build --registry <acr> --image nvidia-analyst:1 --file chatbot/backend/Dockerfile .
```

```bash
az containerapp create --name nvidia-analyst --resource-group <rg> --environment <aca-env> \
  --image <acr>.azurecr.io/nvidia-analyst:1 --registry-server <acr>.azurecr.io \
  --target-port 8000 --ingress external --system-assigned --min-replicas 1 --max-replicas 1
```

Then on the Container App:

- enable a **system-assigned managed identity**; grant it *Key Vault Secrets User* on the vault holding
  `anthropic-api-key`, and the Power BI access from step 2 above
- environment: `AZURE_KEY_VAULT_NAME`, `POWERBI_MODE=live`, `FABRIC_WORKSPACE_ID`, `POWERBI_DATASET_ID`,
  `TRUST_PROXY_HEADERS=true`, `ALLOWED_ORIGINS=["null","https://<your-site>"]`
- keep one replica (rate limits and the daily budget are in memory; move them to Redis to scale out)
- set a spend limit for the API key in the Claude Console as the hard cost cap

## Put the chat in the report

**Option A - custom visual (in the canvas).**

1. In `chatbot/visual/src/visual.ts` set `BACKEND_URL` to the Container App URL, and make sure it
   matches a `WebAccess` parameter in `capabilities.json` (default `https://*.azurecontainerapps.io`).
2. `cd chatbot/visual && npm install && npx pbiviz package` → `dist/*.pbiviz`.
3. Power BI Desktop → Visualizations → *Import a visual from a file*, or publish it to your organization's
   visuals. Admins must allow custom visuals to access external resources (WebAccess) in the tenant.
4. Drop it on page 4 (AI Analyst Notes). Optionally bind `Date[fiscal_year]` and `Date[fiscal_quarter]`:
   when the report filters them to one value, answers follow that period.

The visual cannot hold a secret, and the Power BI authentication API for visuals is only available
to AppSource-certified visuals, so the backend treats requests from it as anonymous. Protection is
CORS (`ALLOWED_ORIGINS` must include `null`, the sandboxed iframe origin), per-IP rate limits, a
daily request budget, read-only tools, and the API key's spend limit.

**Option B - standalone page next to the report.** Serve `/` and open
`https://<app>/?report=<Power BI embed URL>&fy=2026` to get the published report on the left and the
chat on the right; or link to the page from a report button. Useful for Publish to web, where
custom visuals and external calls are more restricted.

## Guardrails (aligned with docs/ai-guardrails.md)

- Numbers only from tool results; the system prompt forbids computing new figures, and
  `grounding.py` flags any figure not found in the returned data.
- Every SEC citation is an `evidence_id` (`concept|period_end|accession`) with the filing link.
- Abstains on missing data (for example Quick Ratio / Net Cash are BLANK from FY2026 because
  NVIDIA stopped tagging current marketable securities).
- Fiscal labels only; 10-Q cash flows called out as year-to-date; no investment advice.
- Secrets: `ANTHROPIC_API_KEY` only in Key Vault (or a local shell); `.env` is git-ignored.
