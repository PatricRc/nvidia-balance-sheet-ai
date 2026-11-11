# Design review checklist

| Scenario | Expected |
| --- | --- |
| Fresh load | Cover opens in Q2 FY2027, compare to FY2026 close, USD composition. Assets $320.27B. |
| Composition switch | USD and percent change only Snapshot bars and labels. Toggle keeps keyboard focus and updates pressed state. |
| Cross-chapter filter | FY2026 persists while navigating through all six chapters. Filing URL, accession and comparator update together. |
| Help | Opens by keyboard, closes with Escape or Close, returns focus and preserves chapter and period. |
| Reset | Returns to default fiscal period and USD composition within the current chapter. |
| Exact values | Both filing columns reconcile in USD millions. Security-inclusive cash and debt calculations match the evidence inputs. |
| Responsive | Readable at 1280 px and narrow widths. No horizontal page scrolling. Exact-value tables have a bounded overflow region. |
| Keyboard and contrast | Active chapter and metric mode have textual or structural signals. Clear focus, good contrast, direct links and an accessible chart-equivalent table. |
| Future report | Reconcile the two filing cases against model measures. Verify missing tags, period boundaries, and runtime support for native theme and controls before binding the report. |

## Prototype verification

The browser checks exercised all five chapters, both fiscal presets, USD and common-size mode, focus preservation, help via Enter and Escape, reset, evidence disclosure, the five financial statement views, and the debt schedule link. Layout was checked at 1280 px and 390 px. The local file URL rendered without a server. Fixture arithmetic checks covered balance-sheet identities, components of current assets, and the principal debt and working-capital calculations. [Browser captures](../dashboard/screenshots/)

DAX was reviewed against source definitions. Model execution and Power BI rendering are later-phase checks.

The classified asset, liability and equity subtotals reconcile at all three reporting dates. All four income and cash flow columns reconcile to their displayed subtotals and closing cash. The browser check verified three-month profit and six-month interim cash flow labels and checked narrow-screen overflow in every statement view.
