# Data correctness (draft)

Day 1 outline. Expand with worked NVIDIA examples only after bronze/silver exist and numbers are hand-checked against a filed 10-K / 10-Q.

## Rules (summary)

1. Fiscal labels from the filing — not calendar-year shortcuts.
2. Instant (balance sheet) vs duration (income / cash flow) stay separate grains.
3. Derive quarters from 10-Q year-to-date duration values; store the derivation.
4. Restatements: keep all filed versions; gold “latest-filed” keeps the original accession for citations.
5. `companyfacts` is a structured extract, not the full filing narrative.
6. Debt, current portion, and leases are separate concepts; net cash is defined once.

See the root README for the full wording used on the project.
