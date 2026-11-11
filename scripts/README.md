# scripts/

Python generators, same role as in `trading-analytics-fabric`:

| Planned script | Purpose |
|---|---|
| `build_measures.py` | **Implemented.** `dax/<folder>/*.dax` (source of truth) → `dax/_all-measures.dax` + the `MEASURES` lists in `nb_semantic_model.ipynb` / `nb_measures_financial.ipynb`. Run after editing any `.dax`; `--check` exits 1 when out of sync. |
| `build_dax.py` | Token dict → design-token DAX (HTML/SVG measures) — later |
| `build_dash.py` | Build HTML page prototypes under `dashboard/html/` |
| (helpers) | SVG chart builders, evidence-pack preview utilities |

**Day 1:** stubs only. No generators checked in yet.
