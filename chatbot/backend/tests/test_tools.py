import json

import pytest

from app.tools import (EvidenceInput, Period, QueryMeasuresInput, ToolExecutor, ToolLedger, TrendInput,
                       build_evidence, build_query_measures, build_trend, tool_definitions)


def test_query_measures_dax_is_one_table_with_period_label():
    dax = build_query_measures(QueryMeasuresInput(
        measures=["Total Assets", "Net Cash (Cash Only)"],
        periods=[Period(fiscal_year=2026), Period(fiscal_year=2027, fiscal_quarter=2)]))
    assert dax.startswith("EVALUATE\nUNION(")
    assert "CALCULATE([Total Assets], 'Date'[fiscal_year] = 2026)" in dax
    assert "CALCULATE([Net Cash (Cash Only)], 'Date'[fiscal_year] = 2027, 'Date'[fiscal_quarter] = 2)" in dax
    assert dax.count('"Period Label"') == 2


def test_latest_period_has_no_filters():
    dax = build_query_measures(QueryMeasuresInput(measures=["Cash"]))
    assert 'ROW("request", "latest"' in dax and "CALCULATE([Cash])" in dax


def test_trend_and_evidence_dax():
    t = build_trend(TrendInput(measure="Revenue", grain="quarter", last_n=8))
    assert "TREATAS({TRUE()}, 'Date'[is_fiscal_quarter_end])" in t and "TOPN(8," in t
    e = build_evidence(EvidenceInput(concepts=["Assets"], fiscal_year=2026, fiscal_period="FY"))
    assert e.count("SELECTCOLUMNS(") == 3 and "RELATED('Filing'[sec_url])" in e


def test_inputs_are_validated():
    with pytest.raises(ValueError):
        Period(fiscal_quarter=2)  # quarter without year
    with pytest.raises(ValueError):
        EvidenceInput(concepts=['Assets"}) , EVALUATE X'], fiscal_year=2026, fiscal_period="FY")


def test_tool_schemas_are_strict_and_stream_eagerly():
    tools = tool_definitions(allow_freeform_dax=False)
    assert [t["name"] for t in tools] == ["search_semantic_model", "query_measures", "get_trend", "get_sec_evidence"]
    for t in tools:
        assert t["strict"] and t["eager_input_streaming"]
        assert t["input_schema"]["additionalProperties"] is False
    assert "run_dax_query" in [t["name"] for t in tool_definitions(allow_freeform_dax=True)]


async def test_executor_rejects_unknown_measures_and_freeform(catalog, backend):
    ex = ToolExecutor(catalog, backend, allow_freeform_dax=False)
    content, err = await ex.run("query_measures", {"measures": ["Made Up"], "periods": []}, ToolLedger())
    assert err and "Made Up" in content
    content, err = await ex.run("run_dax_query", {"query": "EVALUATE {1}"}, ToolLedger())
    assert err
    content, err = await ex.run("query_measures", "not-a-dict", ToolLedger())
    assert err and "INVALID_JSON" in content
    assert backend.queries == []  # nothing reached the model


async def test_executor_returns_rows_evidence_and_ledger(catalog, backend):
    ex = ToolExecutor(catalog, backend, allow_freeform_dax=False)
    ledger = ToolLedger()
    content, err = await ex.run("query_measures", {"measures": ["Total Assets"], "periods": [
        {"fiscal_year": 2026, "fiscal_quarter": None}]}, ledger)
    assert not err and json.loads(content)["rows"][0]["Total Assets"] == 206803000000.0
    content, err = await ex.run("get_sec_evidence", {"concepts": ["Assets", "NotAConcept"],
                                                     "fiscal_year": 2026, "fiscal_period": "FY"}, ledger)
    body = json.loads(content)
    assert not err and "Assets|2026-01-25|0001045810-26-000021" in ledger.evidence
    assert "NotAConcept" in body["not_found"]
    assert 206803000000.0 in ledger.numbers
