# nb_bronze_sec_edgar.py
# Day 1 stub. Fabric notebook source will live here.
#
# Planned behaviour:
#   - Read SEC_USER_AGENT from env / Fabric settings (required).
#   - GET data.sec.gov submissions + companyfacts for NVIDIA (CIK 0001045810).
#   - Respect fair-access guidance (≤10 requests/second).
#   - Land raw JSON once under Files/bronze/sec/ingest_date=YYYY-MM-DD/...
#   - Write ingest metadata (accession, filed, retrieved_at, http status, bytes).
#   - No copies of video or bulk redistribution; OneLake is the system of record.
#
# Do not commit API keys. SEC endpoints need a User-Agent, not a key.
