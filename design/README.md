# The Financial Ledger

Independent research design for **NVIDIA — Behind the Balance Sheet**. The reader is an analyst who wants to move from the reported balance sheet to an explanation and then to the filing evidence.

| Deliverable | Start here |
| --- | --- |
| Interactive browser prototype | [Dashboard](../dashboard/html/index.html) |
| Browser captures | [Cover](../dashboard/screenshots/nvidia-cover.png) · [Snapshot](../dashboard/screenshots/nvidia-snapshot.png) · [Liquidity](../dashboard/screenshots/nvidia-liquidity.png) · [Debt](../dashboard/screenshots/nvidia-debt.png) · [Evidence](../dashboard/screenshots/nvidia-evidence.png) · [Statements](../dashboard/screenshots/nvidia-statements.png) · [Cash flow](../dashboard/screenshots/nvidia-cash-flow.png) · [Phone](../dashboard/screenshots/nvidia-mobile.png) |
| Brand research, tokens, interaction states | [Design system](design-system.md) |
| Story, controls, and interpretation | [Narrative](narrative.md) |
| Per-page layout and measure bindings | [Snapshot](pages/01-snapshot.md) · [Liquidity](pages/02-liquidity.md) · [Debt and net cash](pages/03-debt.md) · [Evidence](pages/04-evidence.md) · [Financial Statements](pages/05-statements.md) |
| Metric definitions and review-ready measure drafts | [DAX contract](dax/README.md) |
| Local data fixtures and provenance | [Sources](../dashboard/html/SOURCES.md) |
| Verification checklist | [Review](review.md) |

Open `dashboard/html/index.html` locally to start on the cover. The cover introduces the financial question, shows three figures for the selected reporting date, and offers links to the analysis and financial statements. The browser prototype uses filing-backed static fixtures and changes views and periods client-side. The DAX drafts are isolated here for a later implementation phase. The official model measures and notebooks remain the source for the current deployed project.
