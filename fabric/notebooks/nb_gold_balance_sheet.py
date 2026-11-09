# nb_gold_balance_sheet.py
# Merged into nb_bronze_silver_gold_sec_edgar.ipynb (also builds income_statement + cash_flow).
#
# Behaviour (implemented in the .ipynb):
#   - gold.dim_line_item  curated concept map
#   - gold.dim_filing     from submissions (accn, form, filingDate, reportDate, sec_url)
#   - gold.balance_sheet / gold.income_statement / gold.cash_flow (long format)
#   - Instant facts for BS; duration for IS/CF; 10-K annual + 10-Q
#   - Restatements: latest filed per concept+period window; keep accn
#   - is_period_primary when period_end == filing reportDate (exclude comparatives)
#   - 10-Q YTD cash flow / income flagged (is_ytd); raw YTD kept — no invented quarters
#   - Quality: Assets == LiabilitiesAndStockholdersEquity (tol $1) on latest primary periods
