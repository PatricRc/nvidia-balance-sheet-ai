# Design system

## Brand research and direction

NVIDIA publishes official logo and brand usage guidance and a trademark PDF. The PDF identifies NVIDIA Green as #76B900. The public brand page limits use of its assets and tells communicators to avoid imitating the NVIDIA brand. The public material reviewed concerns identity and usage. It did not provide a reusable public dashboard UI kit. The report uses the company name as the subject and the project’s own masthead, **The Financial Ledger**. It uses original artwork and system fonts. [NVIDIA brand guidance](https://www.nvidia.com/en-gb/about-nvidia/legal-info/logo-brand-usage/) · [Trademark PDF](https://www.nvidia.com/content/dam/en-zz/Solutions/about-us/documents/NVIDIA-Trademark-and-Logo-Usage-Guidelines.pdf)

Use the hierarchy of a printed annual report with the interactivity of a modern research terminal. Warm paper, a small set of dark ink colors, a strong serif headline, tabular numerals, understated rules, and numbered chapters establish the editorial identity. Use a project-specific chartreuse accent for the active rail and data emphasis. Reference Gus Bavia’s method through the stable rail, disciplined token mapping, one hero per chapter, guide overlay, and evidence path. [The World of Peaches](https://github.com/gusbavia/the-world-of-peaches)

## Annual report references

- Berkshire Hathaway's printed annual report separates the shareholder narrative from the audited statements and notes. Borrow its progressive reading path and restrained treatment of exact values. [Berkshire Hathaway 2025 Annual Report](https://berkshirehathaway.com/2025ar/2025ar.pdf)
- IBM's investor reporting makes annual and quarterly releases easy to locate by period. Apply that source navigation to the period control and filing record, with the exact SEC accession one step from the headline. [IBM financial reporting](https://www.ibm.com/investor/financial-reporting)

## Tokens and layout

[CSS token source](../html/tokens.css) is the canonical browser token sheet. Map colors by role into a future native theme after design review. Preserve the distinction between visual emphasis and financial direction.

| Role | Value or rule |
| --- | --- |
| Paper / surface | #F2F0E8 / #FCFBF6 |
| Ink / muted | #1A241F / #505D53 |
| Rail / reverse text | #15211D / #F4F3E9 |
| Accent / accent ink | #CBE66D / #294500. Bright lime is a fill with dark text. |
| Neutral analytical series | #496052 for liabilities and #7A684C for a comparison. Distinguish series with direct labels and order. |
| Direction | #2F5D39 for increases, #8C3B31 for decreases where explicit. An increase in debt is a direction, with no implication of quality. |
| Type | Georgia for headlines, system sans for navigation and labels, system mono for folios and accession IDs. Tabular lining figures and aligned numeric columns. |
| Spacing / radius | 4, 8, 12, 16, 24, 32, 48 px. Cards use 4 px radius, rules do most of the work. |
| Native canvas draft | 1280 × 720. Rail 192 px, content x=224 through x=1248, header 112 px, 16 px column gutters. Chapter wireframes specify priorities. |
| Browser | Two-column shell with persistent navigation on desktop. Compact top navigation and single-column cards on narrow screens. Detail tables scroll inside their region. |

## Controls and states

| Component | Default and hover | Focus, active, and exceptional states |
| --- | --- | --- |
| Chapter link | Reverse text on graphite, brighter rail fill and underline on hover | Lime edge and solid fill for current page. Visible outline, plus native link semantics and `aria-current`. |
| Primary button | Lime fill with dark text, lighter fill on hover | Darker pressed fill. Distinct focus outline with offset. |
| Secondary button | Paper with ink border, subdued green tint on hover | Same focus treatment. Pressed toggle has selected fill and `aria-pressed`. Disabled control has native disabled semantics. |
| Filing link | Underlined with offset | Hover thickens underline. Keep the action in keyboard order. |
| Selector | Labeled fiscal period, stable width | Focus outline and native keyboard behavior. On change announce the period and clear any stale evidence detail. |
| Help | “How to read” from every chapter | Modal with visible Close and Escape behavior. Restore focus. Preserve period and chapter when closing. |
| Empty / withheld | Text states “Unavailable in this period” or “No reviewed AI notes” | Keep the evidence table accessible. Zero uses an explicit numeric label. |
| Evidence row | Fine rules and aligned values | Reveal provenance through native disclosure. The closed summary contains enough context to find the source again. |

Body text should meet a 4.5:1 contrast target. Test keyboard navigation, layout at 200% zoom, and phone widths. Use a readable text label for every chart and preserve an exact-value table. Keep imagery behind a scrim or beside text. Keep generated visuals decorative and out of the analytical reading order.
