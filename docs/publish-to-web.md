# Publish to web

**Live report:** not published yet. Add the public link here once Patricio approves publishing.

Publish to web won't publish a report on a Direct Lake model: Direct Lake reads OneLake as the viewer. The public version therefore runs on an Import-mode copy, the same recipe as `trading-analytics-fabric`:

| Item | Mode | Purpose |
|---|---|---|
| `NVIDIA Financials` + `NVIDIA-financial-report` | Direct Lake on OneLake | development, always current; left untouched |
| `NVIDIA Financials Public` + `NVIDIA-financial-report - Public` | Import | Publish to web |

## How it's built
1. `fabric/notebooks/nb_build_import_model.ipynb` (semantic-link-labs, `MODE = "build"`) reads the Direct Lake model's BIM, swaps every `directLake` partition for an Import partition (`Sql.Database(<SQL endpoint>, "NVIDIALakehouse")`, schema `gold`), drops the Direct Lake shared expression and creates `NVIDIA Financials Public`. The 6 gold tables, the calculated `_Measures` table, all 84 measures with their display folders, the 9 relationships and the date table come over with the BIM. The notebook checks this against the source.
2. The same run clones the report onto the copy with the Power BI REST `Reports/Clone` API (`targetModelId`): `NVIDIA-financial-report - Public`.
3. The copy's SQL data source is mapped to an **OAuth 2.0 cloud connection** to the lakehouse SQL endpoint instead of *Default: Single Sign-On* (SSO can't refresh and also blocks Publish to web).
4. `MODE = "refresh"`: full refresh, then the anchors (FY2026 Marketable Securities 51,951M, Net Cash 54,088M) and a check that all 84 measures return the same FY2026 values as the Direct Lake model.
5. `MODE = "fix_report"`: the clone kept two things Publish to web refuses. Its `definition.pbir` still pointed at the Direct Lake model (Clone's `targetModelId` didn't take), and it carries report-level measures in `reportExtensions.json`. The notebook promotes those measures into `_Measures` of the Import model (folder `Report\Ledger`, saved to `dax/report-ledger-measures/`). It then removes every `"Schema": "extension"` reference from the visuals, pages and bookmarks, deletes `reportExtensions.json`, points the pbir at the Import model, saves with `updateDefinition`, calls Rebind and re-reads the definition to confirm: `FIX REPORT: PASS`.
6. File → Embed report → Publish to web (public).

## Keeping it current (on demand, no schedule)
SEC filings arrive quarterly, so nothing is scheduled. `pl_nvidia_sec_refresh` ends with a notebook activity **Refresh public model** that runs `nb_build_import_model` with `MODE = "refresh"` after the measures validation succeeds. The trading project used a scheduled refresh instead; this project doesn't.

When measures or tables change in `NVIDIA Financials`, the Import copy doesn't follow automatically: the structure check fails. Rebuild the copy (see the how-to, "When the source model changes").

Steps: `docs/how-to-publish-public-dashboard.md`. Handoff for an agent: `docs/llm-handoff-publish-public-dashboard.md`.
