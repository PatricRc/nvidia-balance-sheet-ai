"""Post-answer grounding check: every money, percent and multiple figure in the answer must match a
number the tools returned this turn (within the rounding the answer shows).

It does not block the answer - it labels it, so the UI can show "verified against the model"
or flag the figures that were not found. This mirrors the project's AI guardrail: no number
may appear unless it is in the evidence pack.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

SCALE = {"": 1.0, "k": 1e3, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12, "thousand": 1e3,
         "million": 1e6, "billion": 1e9, "trillion": 1e12}

# $206.8B | $1,234M | -$2.1 billion | 58.3% | 2.40x | 1,234,567 (comma-grouped) | 0.67
FIGURE = re.compile(
    r"(?P<neg>[-−])?(?P<cur>\$)?(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"\s?(?P<unit>%|x\b|×|thousand\b|million\b|billion\b|trillion\b|[kKMBT]\b)?"
)


@dataclass
class Figure:
    text: str
    value: float
    tolerance: float
    kind: str  # money | percent | multiple | number


def extract_figures(answer: str) -> list[Figure]:
    out: list[Figure] = []
    for m in FIGURE.finditer(answer):
        raw = m.group("num")
        unit = m.group("unit") or ""
        cur = bool(m.group("cur"))
        decimals = len(raw.split(".")[1]) if "." in raw else 0
        num = float(raw.replace(",", ""))
        if m.group("neg"):
            num = -num
        start = m.start()
        prev = answer[max(0, start - 2):start]
        # skip fiscal labels and dates: FY2026, Q2, 2026-01-25, accession numbers, evidence ids
        if re.search(r"(FY|Q|CY|#)$", prev.strip()) or re.match(r"\d{4}-\d{2}", answer[start:start + 7]):
            continue
        if "|" in answer[max(0, start - 1):m.end() + 1] or "-" in answer[m.end():m.end() + 1]:
            continue
        if unit == "%":
            out.append(Figure(m.group(0), num / 100, 0.5 * 10 ** -decimals / 100, "percent"))
        elif unit in ("x", "×"):
            out.append(Figure(m.group(0), num, 0.5 * 10 ** -decimals, "multiple"))
        elif cur or unit in SCALE and unit:
            scale = SCALE.get(unit, 1.0)
            out.append(Figure(m.group(0), num * scale, 0.5 * 10 ** -decimals * scale, "money"))
        elif "," in raw and num >= 10000:
            out.append(Figure(m.group(0), num, 0.5, "number"))
        # bare small integers / years are not checked
    return out


def _matches(fig: Figure, values: list[float]) -> bool:
    for v in values:
        candidates = (v, abs(v)) if fig.value >= 0 else (v,)
        for c in candidates:
            if abs(c - fig.value) <= fig.tolerance + 1e-9:
                return True
            # money written in a coarser unit than the raw value (e.g. $8,468M vs 8468000000)
            if fig.kind == "money" and c and abs(c - fig.value) / abs(c) <= 1e-9:
                return True
    return False


def check_grounding(answer: str, tool_numbers: list[float]) -> dict:
    figures = extract_figures(answer)
    ungrounded = [f.text.strip() for f in figures if not _matches(f, tool_numbers)]
    return {
        "checked": len(figures),
        "ungrounded": ungrounded,
        "status": "no_figures" if not figures else ("verified" if not ungrounded else "unverified"),
    }
