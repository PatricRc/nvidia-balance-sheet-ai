# Handoff: publish the NVIDIA report to the public web

**Audience:** an LLM agent (or a person) driving the Fabric UI for this repo.
**Reference:** `trading-analytics-fabric` did the same for *TradingDashboard - Public* (Import copy, report clone, OAuth connection, Publish to web).

## 0. Rules before you start
- **Publishing makes all data in the model viewable by anyone with the link.** Don't create an embed code until Patricio explicitly says to publish in the conversation. Building the copy is fine.
- Don't write, store or print credentials. The OAuth sign-in is done by Patricio in the browser popup.
- Keep `NVIDIA Financials` and `NVIDIA-financial-report` untouched. Everything public goes into the copy.
- Delete Fabric items only when Patricio names them exactly.
- Trial capacity: if a run fails with HTTP 430, stop idle sessions (Monitor hub) and retry.

## 1. Why a copy is needed
Publish to web rejects a report whose model is Direct Lake, DirectQuery or a live connection, uses single sign-on to its source, or has RLS. `NVIDIA Financials` is Direct Lake on OneLake, so the menu item is greyed out even with the tenant setting on and a fixed-identity connection. The fix is an **Import** copy with the same tables, measures and relationships, and the report cloned onto it.

## 2. Ids
| Item | Value |
|---|---|
| Workspace `NVIDIA-BalanceSheet-AI` | `d1d09fde-24c7-4984-a4b0-eb55acf7c4f4` |
| Lakehouse `NVIDIALakehouse` (schemas on, `gold`) | `ece4bf8e-457a-4e4e-9628-4957de7a9c54` |
| Source model `NVIDIA Financials` (Direct Lake) | `28fb4dc4-d49a-4d2f-b561-85bd3a3a3a43` |
| Source report | `NVIDIA-financial-report` |
| Import model (created) | `NVIDIA Financials Public` |
| Public report (created) | `NVIDIA-financial-report - Public` |

Expected in both models: 7 tables (6 gold + `_Measures`), 9 relationships, 84 measures, all on `_Measures`.

## 3. Build the copy
1. Import `fabric/notebooks/nb_build_import_model.ipynb` into the workspace.
2. Kernel **Python 3.12** (imports can arrive as PySpark: switch it). Attach **NVIDIALakehouse**.
3. Parameter cell `MODE = "build"`. Run all.
4. Expect: `tables switched to Import` (6 lines), `created NVIDIA Financials Public`, `STRUCTURE CHECK: PASS`, `cloned: <id> NVIDIA-financial-report - Public`, and the SQL endpoint server and database.

## 4. Connect the data source (Patricio's step)
Refresh fails until this is done ("uses a default data connection without explicit connection credentials").
1. `NVIDIA Financials Public` → Settings → Gateway and cloud connections.
2. *Maps to* → **Create a connection**: Cloud, *SQL Server*, server and database from step 3, **OAuth 2.0**.
3. **Edit credentials**: a sign-in popup opens. Patricio signs in. Click **Create** right away.
4. Set *Maps to* to the connection and **Apply**.

An agent can't complete the popup: ask Patricio and wait.

## 5. Refresh and verify
Set `MODE = "refresh"` and Run all. Expect `SQL endpoint metadata synced`, the refresh, `PASS anchor Marketable Securities FY2026: 51951000000`, `PASS anchor Net Cash FY2026: 54088000000`, `84/84 measures match the Direct Lake model` and `OVERALL: PASS`.

## 6. Check the public report
Open `NVIDIA-financial-report - Public`. Every page should show values with no broken visuals. Fix only this copy. If a visual is broken, rebind it: select it → Visualizations → remove the field → pick the same measure from `_Measures`.

## 7. Publish to web (approval required)
Only after Patricio says to publish:
1. **File → Embed report → Publish to web (public)** → Create embed code → Publish.
2. Copy **Link you can send in email** (and the HTML embed if asked).
3. Open the link in a private window: it must load without signing in, all pages present.
4. Put the link in `docs/publish-to-web.md`.

Changes can take up to an hour to appear on the public link.

## 8. Keeping it current (no schedule)
Add to `pl_nvidia_sec_refresh` a final Notebook activity `Refresh public model` → `nb_build_import_model`, base parameter `MODE` = `refresh` (String), on success of the measures-validation activity. Don't add a schedule: the pipeline runs on demand.

## 9. Verification checklist
- [ ] `STRUCTURE CHECK: PASS` (same tables, relationships, measures, folders).
- [ ] `OVERALL: PASS` after refresh.
- [ ] The public report's dataset is `NVIDIA Financials Public` (report → Settings, or `fabric.list_reports`).
- [ ] Every visual shows values.
- [ ] Patricio approved publishing.
- [ ] The public link opens signed out.
