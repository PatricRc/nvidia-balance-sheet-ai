# nb_bronze_sec_edgar.py
# Merged into nb_bronze_silver_gold_sec_edgar.ipynb (bronze + silver + gold in one run).
#
# Behaviour (implemented in the .ipynb):
#   - Parameter SEC_USER_AGENT = "DataPat.ai patricrc10@gmail.com"
#   - GET data.sec.gov submissions + companyfacts for NVIDIA (CIK 0001045810)
#   - Respect fair-access guidance (≤10 requests/second)
#   - Land raw JSON once under
#       Files/bronze/sec_edgar/cik=0001045810/ingest_date=YYYY-MM-DD/
#         {companyfacts,submissions}.json
#   - Idempotent: reuse same-day bronze if both files exist
#
# Do not commit API keys. SEC endpoints need a User-Agent, not a key.
# Import the .ipynb into Fabric and attach lakehouse NVIDIALakehouse.
