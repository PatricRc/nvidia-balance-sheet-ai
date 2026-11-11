"""Tools Claude can call. Each one builds DAX from validated, whitelisted inputs - Claude never
sends DAX text unless ALLOW_FREEFORM_DAX is on (and even then it is read-only and capped).

Retrieval-augmented generation over the semantic model works in two stages:
1. search_semantic_model - retrieve the relevant measures / concepts from the catalog
2. query_measures / get_trend / get_sec_evidence - retrieve live numbers and SEC evidence from
   the model via executeQueries, then answer only from what came back.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from .catalog import Catalog
from .powerbi import DaxError, QueryBackend

MAX_ROWS_TO_MODEL = 200
CONCEPT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{1,120}$")


# ----------------------------------------------------------------------------- input models
class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchInput(_Strict):
    query: str = Field(min_length=1, max_length=300)
    k: int = Field(default=8, ge=1, le=15)


class Period(_Strict):
    fiscal_year: int | None = Field(default=None, ge=2005, le=2100)
    fiscal_quarter: int | None = Field(default=None, ge=1, le=4)

    @model_validator(mode="after")
    def _quarter_needs_year(self) -> "Period":
        if self.fiscal_quarter is not None and self.fiscal_year is None:
            raise ValueError("fiscal_quarter requires fiscal_year")
        return self

    def label(self) -> str:
        if self.fiscal_year is None:
            return "latest"
        return f"Q{self.fiscal_quarter} FY{self.fiscal_year}" if self.fiscal_quarter else f"FY{self.fiscal_year}"

    def filters(self) -> list[str]:
        out = []
        if self.fiscal_year is not None:
            out.append(f"'Date'[fiscal_year] = {self.fiscal_year}")
        if self.fiscal_quarter is not None:
            out.append(f"'Date'[fiscal_quarter] = {self.fiscal_quarter}")
        return out


class QueryMeasuresInput(_Strict):
    measures: list[str] = Field(min_length=1, max_length=12)
    periods: list[Period] = Field(default_factory=list, max_length=8)


class TrendInput(_Strict):
    measure: str
    grain: Literal["quarter", "year"]
    last_n: int = Field(ge=2, le=24)


class EvidenceInput(_Strict):
    concepts: list[str] = Field(min_length=1, max_length=10)
    fiscal_year: int = Field(ge=2005, le=2100)
    fiscal_period: Literal["Q1", "Q2", "Q3", "FY"]

    @field_validator("concepts")
    @classmethod
    def _concept_names(cls, v: list[str]) -> list[str]:
        bad = [c for c in v if not CONCEPT_RE.match(c)]
        if bad:
            raise ValueError(f"invalid concept names: {bad}")
        return v


class FreeformDaxInput(_Strict):
    query: str = Field(min_length=8, max_length=4000)

    @field_validator("query")
    @classmethod
    def _evaluate_only(cls, v: str) -> str:
        head = v.lstrip().upper()
        if not (head.startswith("EVALUATE") or head.startswith("DEFINE")):
            raise ValueError("query must start with EVALUATE or DEFINE")
        return v


# ----------------------------------------------------------------------------- tool schemas
def _nullable(t: str) -> dict:
    return {"type": [t, "null"]}


def tool_definitions(allow_freeform_dax: bool) -> list[dict]:
    """Deterministic order and content so the tools block stays prompt-cache friendly."""
    period = {
        "type": "object",
        "properties": {"fiscal_year": _nullable("integer"), "fiscal_quarter": _nullable("integer")},
        "required": ["fiscal_year", "fiscal_quarter"],
        "additionalProperties": False,
    }
    tools = [
        {
            "name": "search_semantic_model",
            "description": (
                "Search the NVIDIA Financials semantic model catalog (measures with their definitions, "
                "us-gaap concepts in gold, tables). Use it first to find the exact measure names for a "
                "question; measure names passed to other tools must match exactly. k = results (1-15)."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}, "k": {"type": "integer"}},
                "required": ["query", "k"],
                "additionalProperties": False,
            },
        },
        {
            "name": "query_measures",
            "description": (
                "Evaluate up to 12 measures for up to 8 fiscal periods in one DAX query against the live "
                "model. Each period is {fiscal_year, fiscal_quarter}; fiscal_quarter null = the fiscal "
                "year (annual 10-K values when the year is complete, otherwise the latest quarter in it); "
                "an empty periods list = the latest period in the model. Every row also returns "
                "'Period Label' (e.g. 'Q2 FY2027 · ended 2026-07-26') - quote it with the numbers. "
                "Values are raw: USD, ratios as decimals (0.583 = 58.3%), BLANK = null."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "measures": {"type": "array", "items": {"type": "string"}},
                    "periods": {"type": "array", "items": period},
                },
                "required": ["measures", "periods"],
                "additionalProperties": False,
            },
        },
        {
            "name": "get_trend",
            "description": (
                "Time series of one measure at fiscal quarter-ends (grain=quarter) or fiscal year-ends "
                "(grain=year), most recent last_n points (2-24), oldest first. Use for trends, peaks and "
                "multi-period comparisons."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "measure": {"type": "string"},
                    "grain": {"type": "string", "enum": ["quarter", "year"]},
                    "last_n": {"type": "integer"},
                },
                "required": ["measure", "grain", "last_n"],
                "additionalProperties": False,
            },
        },
        {
            "name": "get_sec_evidence",
            "description": (
                "Return the SEC EDGAR facts behind numbers: for us-gaap concepts (e.g. Assets, "
                "NetIncomeLoss) in one fiscal period, the reported value, period end, form, accession "
                "number, filed date and SEC filing URL from gold. Each row has an evidence_id to cite. "
                "fiscal_period is Q1, Q2, Q3 or FY."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "concepts": {"type": "array", "items": {"type": "string"}},
                    "fiscal_year": {"type": "integer"},
                    "fiscal_period": {"type": "string", "enum": ["Q1", "Q2", "Q3", "FY"]},
                },
                "required": ["concepts", "fiscal_year", "fiscal_period"],
                "additionalProperties": False,
            },
        },
    ]
    if allow_freeform_dax:
        tools.append({
            "name": "run_dax_query",
            "description": (
                "Run one read-only DAX query (must start with EVALUATE or DEFINE) for questions the "
                "other tools cannot express. Returns at most 200 rows. Prefer the other tools."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
        })
    for t in tools:
        t["strict"] = True
        # Streaming request with client tools: stream inputs as generated; we validate below.
        t["eager_input_streaming"] = True
    return tools


INPUT_MODELS: dict[str, type[_Strict]] = {
    "search_semantic_model": SearchInput,
    "query_measures": QueryMeasuresInput,
    "get_trend": TrendInput,
    "get_sec_evidence": EvidenceInput,
    "run_dax_query": FreeformDaxInput,
}


# ----------------------------------------------------------------------------- DAX builders
def dax_string(s: str) -> str:
    return '"' + s.replace('"', '""') + '"'


def measure_ref(name: str) -> str:
    return "[" + name.replace("]", "]]") + "]"


def calc(expr: str, filters: list[str]) -> str:
    return f"CALCULATE({expr}, {', '.join(filters)})" if filters else f"CALCULATE({expr})"


def build_query_measures(inp: QueryMeasuresInput) -> str:
    names = ["Period Label"] + [m for m in dict.fromkeys(inp.measures) if m != "Period Label"]
    periods = inp.periods or [Period()]
    rows = []
    for p in periods:
        cols = [dax_string("request"), dax_string(p.label())]
        for n in names:
            cols += [dax_string(n), calc(measure_ref(n), p.filters())]
        rows.append("ROW(" + ", ".join(cols) + ")")
    body = rows[0] if len(rows) == 1 else "UNION(\n    " + ",\n    ".join(rows) + "\n)"
    return "EVALUATE\n" + body


def build_trend(inp: TrendInput) -> str:
    m = measure_ref(inp.measure)
    if inp.grain == "quarter":
        group = "'Date'[fiscal_year], 'Date'[fiscal_quarter]"
        flag = "'Date'[is_fiscal_quarter_end]"
        order_desc = "'Date'[fiscal_year], DESC, 'Date'[fiscal_quarter], DESC"
        order_asc = "'Date'[fiscal_year] ASC, 'Date'[fiscal_quarter] ASC"
    else:
        group = "'Date'[fiscal_year]"
        flag = "'Date'[is_fiscal_year_end]"
        order_desc = "'Date'[fiscal_year], DESC"
        order_asc = "'Date'[fiscal_year] ASC"
    return (
        "DEFINE\n"
        f"    VAR _t = SUMMARIZECOLUMNS({group}, TREATAS({{TRUE()}}, {flag}), "
        f"\"value\", {m}, \"Period Label\", [Period Label])\n"
        f"EVALUATE\nTOPN({inp.last_n}, FILTER(_t, NOT ISBLANK([value])), {order_desc})\n"
        f"ORDER BY {order_asc}"
    )


_EVIDENCE_TABLES = (("Balance Sheet", "balance_sheet"), ("Income Statement", "income_statement"),
                    ("Cash Flow", "cash_flow"))


def build_evidence(inp: EvidenceInput) -> str:
    concepts = "{" + ", ".join(dax_string(c) for c in dict.fromkeys(inp.concepts)) + "}"
    parts = []
    for table, statement in _EVIDENCE_TABLES:
        t = f"'{table}'"
        parts.append(
            f"SELECTCOLUMNS(\n        FILTER({t}, {t}[is_latest_filing] = TRUE() "
            f"&& {t}[fiscal_year] = {inp.fiscal_year} && {t}[fiscal_period] = {dax_string(inp.fiscal_period)} "
            f"&& {t}[concept] IN {concepts}),\n"
            f"        \"statement\", {dax_string(statement)}, \"concept\", {t}[concept], "
            f"\"line_item\", {t}[line_item], \"period_end\", {t}[period_end], \"value_usd\", {t}[value_usd], "
            f"\"unit\", {t}[unit], \"form\", {t}[form], \"accn\", {t}[accn], \"filed\", {t}[filed], "
            f"\"sec_url\", RELATED('Filing'[sec_url])\n    )"
        )
    return "EVALUATE\nUNION(\n    " + ",\n    ".join(parts) + "\n)"


# ----------------------------------------------------------------------------- execution
@dataclass
class ToolLedger:
    """Everything the tools returned this turn: used for grounding checks and source lists."""

    numbers: list[float] = field(default_factory=list)
    evidence: dict[str, dict] = field(default_factory=dict)
    queries: list[str] = field(default_factory=list)

    def add_numbers(self, obj: Any) -> None:
        if isinstance(obj, bool):
            return
        if isinstance(obj, (int, float)):
            self.numbers.append(float(obj))
        elif isinstance(obj, dict):
            for v in obj.values():
                self.add_numbers(v)
        elif isinstance(obj, list):
            for v in obj:
                self.add_numbers(v)


def _short_date(v: Any) -> str:
    return str(v)[:10] if v else ""


class ToolExecutor:
    def __init__(self, catalog: Catalog, backend: QueryBackend, allow_freeform_dax: bool):
        self.catalog = catalog
        self.backend = backend
        self.allow_freeform_dax = allow_freeform_dax

    def _check_measures(self, names: list[str]) -> list[str]:
        return [n for n in names if n not in self.catalog.measures]

    async def run(self, name: str, raw_input: Any, ledger: ToolLedger) -> tuple[str, bool]:
        """Return (content, is_error). Never raises for bad input or DAX failures."""
        model = INPUT_MODELS.get(name)
        if model is None or (name == "run_dax_query" and not self.allow_freeform_dax):
            return json.dumps({"error": f"unknown tool {name}"}), True
        if not isinstance(raw_input, dict):
            return json.dumps({"INVALID_JSON": json.dumps(raw_input, default=str)}), True
        try:
            inp = model.model_validate(raw_input)
        except ValidationError as e:
            return json.dumps({"error": "invalid input", "details": e.errors(include_url=False)}, default=str), True

        try:
            if isinstance(inp, SearchInput):
                return json.dumps({"results": self.catalog.search(inp.query, inp.k)}), False

            if isinstance(inp, QueryMeasuresInput):
                unknown = self._check_measures(inp.measures)
                if unknown:
                    return json.dumps({"error": "unknown measures - use search_semantic_model",
                                       "unknown": unknown}), True
                q = build_query_measures(inp)
                rows = await self._query(q, ledger)
                return json.dumps({"rows": rows, "formats": {m: self.catalog.measures[m].format
                                                            for m in inp.measures}}, default=str), False

            if isinstance(inp, TrendInput):
                unknown = self._check_measures([inp.measure])
                if unknown:
                    return json.dumps({"error": "unknown measure - use search_semantic_model",
                                       "unknown": unknown}), True
                rows = await self._query(build_trend(inp), ledger)
                return json.dumps({"measure": inp.measure, "format": self.catalog.measures[inp.measure].format,
                                   "points": rows}, default=str), False

            if isinstance(inp, EvidenceInput):
                rows = await self._query(build_evidence(inp), ledger)
                for r in rows:
                    eid = f"{r.get('concept')}|{_short_date(r.get('period_end'))}|{r.get('accn')}"
                    r["evidence_id"] = eid
                    ledger.evidence[eid] = r
                missing = sorted(set(inp.concepts) - {r.get("concept") for r in rows})
                return json.dumps({"rows": rows, "not_found": missing}, default=str), False

            if isinstance(inp, FreeformDaxInput):
                rows = await self._query(inp.query, ledger)
                return json.dumps({"rows": rows[:MAX_ROWS_TO_MODEL], "truncated": len(rows) > MAX_ROWS_TO_MODEL},
                                  default=str), False
        except DaxError as e:
            return json.dumps({"error": "DAX query failed", "details": str(e)}), True

        return json.dumps({"error": "unhandled tool"}), True

    async def _query(self, dax: str, ledger: ToolLedger) -> list[dict]:
        ledger.queries.append(dax)
        rows = await self.backend.execute_dax(dax)
        ledger.add_numbers(rows)
        return rows
