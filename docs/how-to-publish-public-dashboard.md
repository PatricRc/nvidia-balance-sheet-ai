# How to publish the NVIDIA report to the public web

How to make **NVIDIA-financial-report - Public** viewable without signing in. Adapted from `trading-analytics-fabric/docs/how-to-publish-public-dashboard.md`.

**Public link:** not published yet.

## Why a copy is needed
Publish to web is greyed out for `NVIDIA-financial-report` because `NVIDIA Financials` is Direct Lake on OneLake. Turning on the tenant setting and mapping the model to a fixed-identity connection (`nvidia-directlake-fixed`) didn't enable it. The fix is a second model in **Import** mode that reads the same gold tables, with the report cloned onto it. The original model and report stay as they are for private work.

## Steps

### 1. Tenant settings (Fabric admin, already on for this tenant)
- *Publish to web*: enabled
- *Allow users to create new embed codes*: on
- *Block Public Internet Access*: off

### 2. Build the Import model and clone the report
Import `fabric/notebooks/nb_build_import_model.ipynb` into **NVIDIA-BalanceSheet-AI**, set the kernel to **Python 3.12**, attach **NVIDIALakehouse**, keep `MODE = "build"` and Run all. It:
1. Reads the Direct Lake model's BIM (`labs.get_semantic_model_bim`).
2. Replaces each `directLake` partition with `Sql.Database(<SQL endpoint>, "NVIDIALakehouse")` → `Schema="gold"`, `Item=<table>`.
3. Removes the Direct Lake shared expression.
4. Creates `NVIDIA Financials Public` (`labs.create_semantic_model_from_bim`). If it already exists it's left alone.
5. Checks tables, relationships, measures, folders and format strings against the source: `STRUCTURE CHECK: PASS`, 84 measures on `_Measures`.
6. Clones `NVIDIA-financial-report` to `NVIDIA-financial-report - Public` (Power BI REST `Reports/Clone`, `targetModelId`). The clone still needs step 5 below: in practice it kept the Direct Lake binding in `definition.pbir`, and it carries report-level measures.
7. Prints the SQL endpoint server and database for step 3.

### 3. Connect the data source
The new model maps to *Default: Single Sign-On*, which can't refresh and blocks Publish to web.
1. Workspace → `NVIDIA Financials Public` → Settings → Gateway and cloud connections.
2. *Maps to* → **Create a connection**: type *Cloud*, connection type *SQL Server*, the server and database printed by the notebook, authentication **OAuth 2.0**. Edit credentials, sign in, then click Create straight away (the token expires if the panel sits open).
3. Set *Maps to* to the new connection and Apply.

### 4. Refresh and check
Set `MODE = "refresh"` and Run all. It syncs the SQL endpoint metadata, runs a full refresh, then checks the FY2026 anchors and that all 84 measures match the Direct Lake model. Last line: `OVERALL: PASS`.

### 5. Fix the public report (`MODE = "fix_report"`)
Publish to web stays greyed out on the clone while it has report-level measures (`definition/reportExtensions.json`) or a `definition.pbir` bound to the Direct Lake model. A blank report on `NVIDIA Financials Public` does allow it. Set `MODE = "fix_report"` and Run all. It:
1. Reads the public report with Fabric `getDefinition` (PBIR).
2. Saves the report-level measures to `Files/exports/report-ledger-measures.json`. Download it and commit it to `dax/report-ledger-measures/`.
3. Adds each one to `_Measures` of **NVIDIA Financials Public** (TOM; name, DAX, format string, hidden, description; folder `Report\Ledger`). Measures already there with the same DAX are skipped. If a name exists with different DAX, it stops before changing anything.
4. Rewrites the report: drops `reportExtensions.json`, removes every `Schema: "extension"` from visuals, pages, bookmarks and filters, and sets the pbir to `semanticmodelid=<Import model>` / `initial catalog="NVIDIA Financials Public"`. Then `updateDefinition` and the Power BI `Rebind` call.
5. Re-reads the definition (no extensions, no extension references, pbir on the Import model) and evaluates every promoted measure. Last line: `FIX REPORT: PASS`.

Safe to rerun. It only touches the `- Public` report and the Import model.

### 6. Check the public report
Open `NVIDIA-financial-report - Public`, page through every page and confirm no visual is blank or shows an error. Edit only this copy.

### 7. Publish to web (needs Patricio's go-ahead)
In the public report: **File → Embed report → Publish to web (public)** → Create embed code → Publish. Copy the link labelled *Link you can send in email*, open it in a private window, and add it to `docs/publish-to-web.md`.

## Refresh on demand
No schedule: SEC data changes quarterly. In `pl_nvidia_sec_refresh`, add a last **Notebook** activity:
- Name: `Refresh public model` (no `+` in activity names)
- Notebook: `nb_build_import_model`
- Base parameter: `MODE` (String) = `refresh`
- Dependency: **On success** of the measures-validation activity

The activity fails (and so the pipeline fails) if an anchor or any measure differs from the Direct Lake model.

## When the source model changes
If `NVIDIA Financials` gains or changes measures, tables or relationships, the structure check fails. Rebuild the copy: set `DST` and `REPORT_PUBLIC` in the notebook to new names, run `MODE = "build"` (new model and clone), map the connection, refresh, and switch the public embed over. Delete the old copy only when Patricio names it.

## Things to know
- **Anyone with the link can see all data in the Import model.** It's public SEC data, so that's fine here, but don't add private tables to this model.
- **Changes aren't instant.** Publish to web caches the report; changes can take up to about an hour to appear.
- **The public copy only updates when it refreshes**, i.e. when `pl_nvidia_sec_refresh` runs.
- **Deletion vectors:** the Import refresh reads gold through the SQL endpoint, which handles deletion vectors. No parquet reads.

## Related files
- `fabric/notebooks/nb_build_import_model.ipynb`: build, clone, refresh, report fix and checks.
- `dax/report-ledger-measures/`: report-level measures promoted into the public model.
- `tests/test_fix_report.py`: offline test of the report fix on PBIR samples (`python3 tests/test_fix_report.py`).
- `dax/`, `dax/measure-folders.csv`: the measure library and folders (source of the Direct Lake model).
- `docs/publish-to-web.md`: short summary.
