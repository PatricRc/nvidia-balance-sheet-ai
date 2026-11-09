# nb_silver_financial_fact.py
# Day 1 stub.
#
# Planned behaviour:
#   - Read bronze companyfacts JSON from Files/bronze/sec/...
#   - Emit silver.financial_fact: one row per
#       concept + unit + period + form + accession + filed date
#   - Preserve instant vs duration; keep every filed version (restatements).
