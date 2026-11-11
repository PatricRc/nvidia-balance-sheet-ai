# DAX implementation contract

The browser uses filing fixtures. These isolated drafts are for review before Power BI authoring. `ledger-measures.dax` is a DAX Query View scratch file with query-scoped definitions. Its sample query depends on the repository’s `NVIDIA Financials` model. See `dependent-measures.dax` for the formulas that require approved future inputs. The [optional funding-share SVG](funding-share-svg.dax) illustrates a token-aligned Image URL rendering with a native table and alt-text companion. No measures in the existing production folders are replaced.

## Filter and grain

Create one synced, single-select fiscal-end control based on `Date[date]`, restricted to `Date[is_fiscal_quarter_end]` and to periods with approved facts. Use a unique friendly label mapped one-to-one to the date if needed. The design drafts require an exact date in filter context. For the peer comparison take prior fiscal-year close for a quarter or a fiscal-year close. Apply the exact comparator with `REMOVEFILTERS('Date')` and a new date filter. Keep Line Item and Filing axes out of headline KPI contexts unless deliberately designed. For an axis-based trend use a separate disconnected period selector and explicitly constrain the trend to dates on or before that selection.

| Chapter | Existing inputs | Draft and future work |
| --- | --- | --- |
| Snapshot | Total Assets, Total Liabilities, Total Equity | Add residual, asset change since prior FY close, equity share and a period-safe accessible sentence. Existing QoQ, YoY and latest-filed rules need exact test cases before using them in the report. |
| Liquidity | Current Assets, Current Liabilities, Cash, Inventory, Accounts Receivable | Draft strict working capital, cash coverage and a quick-ratio variant. The existing Quick Ratio can omit a missing securities fact through BLANK arithmetic. A reconciled combined-securities input is required before enabling the strict variant. |
| Debt | Long-Term Debt, Total Equity | Compose the total only after the current carrying amount is verified. Label existing Debt to Equity as noncurrent debt/equity. Mark lease balances as separate. |
| Evidence | Date, Filing and model amounts | Render accessible text from validated measures. Add source evidence fields from individual fact rows. A calculation can have multiple accessions, so a single “latest filing” string does not replace row-level evidence. |

## Required source reconciliation before debt and liquidity binding

1. Trace each current debt line to its filing tag and scope by period. Prove whether a broader current debt tag already includes the current portion of long-term debt. Use one approved amount per period. Explicit reported zero and absent concept have distinct states.
2. Resolve securities across consolidated and split disclosure. Prefer a verified combined line when present, otherwise use the verified sum of mutually exclusive current marketable debt and equity components when both are known. Exclude nonmarketable investments and amounts already counted in cash equivalents.
3. Check the point-in-time facts against the FY2026 10-K and Q2 FY2027 10-Q fixture values. Preserve reported unit, date and accession. Show securities risk or restriction context in the evidence view.
4. Evaluate each DAX draft by period and with missing operands. Check Q1 wrap and FY close if an actual QoQ comparison is added. For P&L Q1 vs Q4, the prior-year Q4 date can resolve to the annual 10-K value in current QoQ code. Require a validated standalone Q4 or return BLANK. Keep cash conversion hidden unless income and CFO windows align.
5. Use numeric measures for visuals, sorting and export. Apply currency and scale in the format layer. Use separate text measures for titles and alt text. If implementing an HTML component, escape all variable text and keep interactive controls native. [Power BI accessibility guidance](https://learn.microsoft.com/en-in/power-bi/create-reports/desktop-accessibility-creating-reports)

## Acceptance cases

| Case | Expected |
| --- | --- |
| FY2026 | Assets 206,803,000,000. Residual 0. Prior close Jan 26, 2025. Asset change 95,202,000,000. Working capital 93,442,000,000. |
| Q2 FY2027 | Assets 320,272,000,000. Residual 0. Prior close Jan 25, 2026. Asset change 113,469,000,000. Working capital 154,393,000,000. |
| Missing asset, liability or equity | Residual and related caption return unavailable. |
| Missing current debt or securities | Affected debt or net cash measure stays blank. A verified zero is a valid input. |
| Missing/ambiguous selection | Exact-date calculations and commentary return blank or a period prompt. |
| Zero current liabilities | Cash and quick coverage stay blank. The exact ledger can still show a reported zero. |
| Notes | Evidence exists even if no note is approved. An approved note is rendered only when its period and validated evidence match. |
