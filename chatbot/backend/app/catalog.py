"""Semantic-model catalog: the retrieval index the chatbot searches before it queries data.

Built at startup from the repo's sources of truth, so it never drifts from the model:
- every measure in dax/<folder>/*.dax (name, folder, format, description, DAX)
- every curated us-gaap concept in gold.dim_line_item (parsed from the gold notebook's CONCEPT_MAP)
- the model's tables and the columns the tools use

Retrieval is lexical BM25 over those entries (no embedding service to run or pay for). With
~120 entries the full catalog is also small enough to cache in the system prompt; the
search tool exists so answers start from the right measure and so the catalog can grow.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

DAX_HEADER = re.compile(
    r"^// (?P<name>.+)\n// Table: (?P<table>.+)\n// Display folder: (?P<folder>.+)\n"
    r"// Format: (?P<format>.*)\n// Hidden: (?P<hidden>true|false)\n// ?(?P<description>.*)\n\n"
    r"(?P=name) =\n(?P<expr>.*?)\n*\Z",
    re.S,
)
CONCEPT_ROW = re.compile(
    r'\("(balance_sheet|income_statement|cash_flow)",\s*"([^"]+)",\s*"([A-Za-z0-9]+)",\s*"(instant|duration)"\)'
)
DAX_FOLDERS = ("01-base", "02-kpi", "03-ratios", "04-analysis")

# Columns the tools read. Kept explicit so the prompt and the DAX builders agree.
MODEL_TABLES: dict[str, str] = {
    "Balance Sheet": "gold.balance_sheet - instant facts, one row per concept x period x filing. "
    "Columns: concept, line_item, fiscal_year, fiscal_period (Q1..Q3, FY), period_end, value_usd, unit, "
    "form, accn, filed, is_latest_filing, is_period_primary.",
    "Income Statement": "gold.income_statement - duration facts. Same columns plus period_start, "
    "duration_days, is_ytd. Latest Q1-Q3 rows are standalone 3-month quarters.",
    "Cash Flow": "gold.cash_flow - duration facts; 10-Q rows are year-to-date (is_ytd = TRUE).",
    "Date": "gold.dim_date - NVIDIA fiscal calendar (FY ends last Sunday of January). Columns: date, "
    "fiscal_year, fiscal_quarter, fiscal_quarter_label, is_fiscal_quarter_end, is_fiscal_year_end.",
    "Line Item": "gold.dim_line_item - statement, line_item, concept, expected_period_type.",
    "Filing": "gold.dim_filing - accn, form, filingDate, reportDate, primaryDocument, sec_url.",
}


@dataclass(frozen=True)
class Measure:
    name: str
    folder: str
    format: str
    hidden: bool
    description: str
    expression: str


@dataclass(frozen=True)
class Concept:
    statement: str
    line_item: str
    concept: str
    period_type: str


@dataclass
class Entry:
    kind: str  # measure | concept | table
    key: str
    text: str
    payload: dict
    tokens: list[str] = field(default_factory=list)


def _tokenize(text: str) -> list[str]:
    # split CamelCase concepts and measure names: "LongTermDebtNoncurrent" -> long term debt noncurrent
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return [t for t in re.findall(r"[a-z0-9%&]+", text.lower()) if len(t) > 1 or t in {"%"}]


def load_measures(dax_dir: Path) -> list[Measure]:
    out: list[Measure] = []
    for folder in DAX_FOLDERS:
        for path in sorted((dax_dir / folder).glob("*.dax")):
            m = DAX_HEADER.match(path.read_text(encoding="utf-8"))
            if not m:
                raise ValueError(f"unparseable measure file: {path}")
            d = m.groupdict()
            out.append(
                Measure(d["name"], d["folder"], d["format"], d["hidden"] == "true",
                        d["description"].strip(), d["expr"].rstrip())
            )
    if not out:
        raise ValueError(f"no measures found under {dax_dir}")
    return out


def load_concepts(gold_notebook: Path) -> list[Concept]:
    nb = json.loads(gold_notebook.read_text(encoding="utf-8"))
    src = "\n".join("".join(c["source"]) for c in nb["cells"] if c.get("cell_type") == "code")
    return [Concept(*m.groups()) for m in CONCEPT_ROW.finditer(src)]


class Catalog:
    """BM25 index over measures, concepts and tables."""

    k1 = 1.4
    b = 0.75

    def __init__(self, measures: list[Measure], concepts: list[Concept]):
        self.measures = {m.name: m for m in measures}
        self.concepts = {c.concept: c for c in concepts}
        self.entries: list[Entry] = []
        for m in measures:
            self.entries.append(Entry(
                "measure", m.name,
                f"{m.name} {m.folder} {m.description}",
                {"name": m.name, "folder": m.folder, "format": m.format, "hidden": m.hidden,
                 "description": m.description},
            ))
        for c in concepts:
            self.entries.append(Entry(
                "concept", c.concept, f"{c.line_item} {c.concept} {c.statement} {c.period_type}",
                {"concept": c.concept, "line_item": c.line_item, "statement": c.statement,
                 "period_type": c.period_type},
            ))
        for t, desc in MODEL_TABLES.items():
            self.entries.append(Entry("table", t, f"{t} {desc}", {"table": t, "description": desc}))
        for e in self.entries:
            e.tokens = _tokenize(e.text)
        self._df = Counter(tok for e in self.entries for tok in set(e.tokens))
        self._avgdl = sum(len(e.tokens) for e in self.entries) / len(self.entries)

    @classmethod
    def from_repo(cls, dax_dir: Path) -> "Catalog":
        gold_nb = dax_dir.parent / "fabric" / "notebooks" / "nb_bronze_silver_gold_sec_edgar.ipynb"
        return cls(load_measures(dax_dir), load_concepts(gold_nb))

    def search(self, query: str, k: int = 8) -> list[dict]:
        q = _tokenize(query)
        n = len(self.entries)
        scored: list[tuple[float, Entry]] = []
        for e in self.entries:
            tf = Counter(e.tokens)
            dl = len(e.tokens)
            s = 0.0
            for tok in q:
                if tok not in tf:
                    continue
                idf = math.log(1 + (n - self._df[tok] + 0.5) / (self._df[tok] + 0.5))
                s += idf * tf[tok] * (self.k1 + 1) / (tf[tok] + self.k1 * (1 - self.b + self.b * dl / self._avgdl))
            if e.kind == "measure" and e.payload["hidden"]:
                s *= 0.5  # helpers rank below the measures people should read
            if s > 0:
                scored.append((s, e))
        scored.sort(key=lambda x: (-x[0], x[1].key))
        return [{"kind": e.kind, "score": round(s, 3), **e.payload} for s, e in scored[:k]]

    def prompt_digest(self) -> str:
        """Compact, deterministic listing for the cached system prompt."""
        lines = ["## Measures (name | folder | format | description)"]
        for m in self.measures.values():
            if not m.hidden:
                lines.append(f"- {m.name} | {m.folder} | {m.format or 'text'} | {m.description}")
        lines.append("\n## us-gaap concepts in gold (concept | statement | line item | period type)")
        for c in self.concepts.values():
            lines.append(f"- {c.concept} | {c.statement} | {c.line_item} | {c.period_type}")
        lines.append("\n## Tables")
        for t, desc in MODEL_TABLES.items():
            lines.append(f"- '{t}': {desc}")
        return "\n".join(lines)
