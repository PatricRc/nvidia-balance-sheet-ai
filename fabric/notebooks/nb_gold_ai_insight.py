# nb_gold_ai_insight.py
# Day 1 stub.
#
# Planned behaviour:
#   - Build a small evidence pack from gold.balance_sheet_period (+ supporting facts).
#   - Call Claude Messages API server-side; secret from Azure Key Vault only.
#   - Validate JSON; require evidence IDs; allow abstain.
#   - Write gold.ai_insight with model id, prompt version, input hash,
#     token usage, validation_status, reviewer, timestamp.
#   - Never log or print the API key.
