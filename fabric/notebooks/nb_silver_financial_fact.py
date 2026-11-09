# nb_silver_financial_fact.py
# Merged into nb_bronze_silver_gold_sec_edgar.ipynb.
#
# Behaviour (implemented in the .ipynb):
#   - Read bronze companyfacts JSON from Files/bronze/sec_edgar/...
#   - Emit silver.financial_fact: one row per
#       taxonomy + concept + label + unit + start + end + val
#       + fy + fp + form + accn + filed + frame
#   - Add period_type (instant|duration) and duration_days
#   - Taxonomies: us-gaap + dei
#   - Preserve every filed version at silver; restatement collapse happens in gold
