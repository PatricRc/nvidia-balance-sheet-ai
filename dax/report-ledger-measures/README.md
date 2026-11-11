# Report-level measures promoted into the public model

The report `NVIDIA-financial-report` defined **240** report-level measures (the `Ledger …` measures and others) in `definition/reportExtensions.json`, on entity `_Measures`. Publish to web refuses reports that contain report-level measures. `nb_build_import_model` with `MODE = "fix_report"` therefore moves them, for the `- Public` copy only, into `_Measures` of **NVIDIA Financials Public** under display folder `Report\Ledger`.

`report-ledger-measures.json` is the source of truth: **240** measures, each with `table`, `name`, `expression`, `dataType`, `formatString`, `hidden` (plus `dataCategory` and `references` when set). It is the export written by `MODE = "fix_report"` to the lakehouse at `Files/exports/report-ledger-measures.json` and committed here.

- **Data types:** TOM infers a model measure's data type from its DAX, so `dataType` is kept here for reference only. DateTime measures keep their format string.
- **Direct Lake model:** these measures aren't in `NVIDIA Financials`. The refresh check compares only the 84 shared measures, and separately checks that these evaluate without error.
