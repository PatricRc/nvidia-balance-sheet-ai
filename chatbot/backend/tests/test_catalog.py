def test_catalog_loads_every_measure_and_concept(catalog):
    assert len(catalog.measures) == 84
    assert "Net Cash (Cash Only)" in catalog.measures
    assert "LongTermDebtCurrent" in catalog.concepts
    assert catalog.concepts["Assets"].statement == "balance_sheet"


def test_search_ranks_relevant_measures_first(catalog):
    names = [r.get("name") for r in catalog.search("net cash position debt", k=5)]
    assert "Net Cash" in names[:3] or "Net Cash (Cash Only)" in names[:3]
    hits = catalog.search("long term debt current portion", k=5)
    assert any(h.get("concept") == "LongTermDebtCurrent" for h in hits)


def test_hidden_helpers_excluded_from_prompt_digest(catalog):
    digest = catalog.prompt_digest()
    assert "- Revenue Standalone Quarter |" not in digest
    assert "- Total Assets |" in digest
