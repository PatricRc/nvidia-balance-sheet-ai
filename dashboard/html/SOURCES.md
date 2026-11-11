# Prototype data and artwork

The fixture contains three published balance-sheet snapshots. Values in `filings.js` use USD millions. Calculations run locally in the browser.

| Preset | Current / comparative | Source and scope |
| --- | --- | --- |
| Q2 FY2027 | July 26, 2026 / January 25, 2026 | Condensed Consolidated Balance Sheets in Form 10-Q. Q2 is unaudited. Compare with fiscal year-end. For both columns current marketable securities is the sum of the two reported marketable security lines. [SEC filing](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm) |
| FY2026 | January 25, 2026 / January 26, 2025 | Consolidated Balance Sheets in Form 10-K. Compare with prior fiscal year-end. FY2025 short-term debt is a reported dash transcribed as zero. [SEC filing](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm) |

The selected filing contains both balance-sheet columns. The prototype does not assume that a comparative column identifies a restatement. The model may have different concept coverage than the filed statements. In particular, the fixture's short-term debt and combined securities values are not a claim that the current model already exposes those lines. The date presets are fixed examples and do not imply live refresh. Artwork is documented with its [generation prompts](assets/README.md).

## Statement explorer

The Q2 Profit & Loss view uses matching three-month periods. The Q2 Cash Flow view uses matching six-month fiscal YTD periods and the filed operating, investing, and financing totals. Annual views compare full fiscal years. Balance sheet and supplemental schedules use dates, while profit and cash flow use durations. Net cash, working capital, coverage ratios, and common-size values are analyst calculations. The underlying full filings are linked in each view.
