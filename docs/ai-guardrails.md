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
