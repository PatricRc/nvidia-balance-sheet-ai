# AI guardrails (draft)

Day 1 outline for the Claude batch job that writes `gold.ai_insight`.

## Contract

- Input: a small **evidence pack** built only from gold rows (concept, period, value, unit, accession, filed date).
- Output: validated JSON stored in `gold.ai_insight` with evidence IDs, model id, prompt version, input hash, token usage, validation status, reviewer, timestamp.
- Refusals / abstentions are first-class rows, not silent drops.

## Secrets

`ANTHROPIC_API_KEY` is read from **Azure Key Vault** at runtime. It must never appear in this repo, Fabric notebook source committed here, DAX, Power BI files, or HTML (including the phase-2 chatbot).

## Before page 4 publishes

1. Eval set green for the prompt version.
2. Human `reviewer` + `validation_status` set on each insight shown.
3. Every numeric claim maps to at least one evidence ID in the pack.

## Interactive chatbot (`chatbot/`)

The same contract applies to live questions:

- Retrieval only from the **NVIDIA Financials** model: catalog search, then whitelisted DAX through the Power BI Execute Queries API. Free-form DAX is off by default.
- The system prompt forbids figures that did not come from a tool result in the conversation; `chatbot/backend/app/grounding.py` checks every $, % and x figure in the answer and labels it *verified* or *unverified* in the UI.
- SEC citations use `concept|period_end|accession` evidence IDs with the filing link.
- `ANTHROPIC_API_KEY` is read from Azure Key Vault at startup; the visual and the report hold no secret. Public exposure is limited by CORS, per-IP rate limits, a daily request budget and the API key's spend limit.
